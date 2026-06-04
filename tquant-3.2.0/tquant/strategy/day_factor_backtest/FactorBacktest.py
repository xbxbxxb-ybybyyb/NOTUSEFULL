import os
#os.environ["DSWMAP_username"] = "013150"


import pandas as pd
import numpy as np
import json
import calendar
import datetime as dt
import time
import threading
import requests
from tquant.strategy.day_factor_backtest.backtest.factor_test import SingleFactorTest
from tquant.strategy.day_factor_backtest.backtest.utility import *
from tquant.strategy.day_factor_backtest.backtest.segment_test import segment_test
from tquant.strategy.day_factor_backtest.backtest.report_generator import generate_pdf
from sklearn.model_selection import train_test_split
from tquant import tq_logger
from tquant import BasicData
from FactorProvider.conf.LoadConf import SendFile
from tquant.utils.event_trace import event_trace


class FactorBacktest(SingleFactorTest):
    """
    Algorithm group single daily factor backtest wrapper
    """

    def load_factor(self, factor_data, name='test_factor'):
        """"""
        ### input factor data transformation: normalization, winsorization and neutralization
        pprint('Factor data preprocessing')
        assert np.any([isinstance(factor_data, _type) for _type in [pd.DataFrame]])
        tq_logger.debug("factor_data shape: {}.".format(factor_data.shape))
        tq_logger.debug("self.base_data keys: {}.".format(self.base_data.keys()))

        self.factor_data = factor_data.copy()
        self.name = name
        data_dict = self.base_data.copy()
        check_factors = ['stock_filter_' + str(self.universe), 'user_industry', 'stock_weight', 'neutral_dict']
        factor_data_date_list = list(self.factor_data.index)
        for cf in check_factors:
            try:
                if cf == 'neutral_dict':
                    cf_date_list = list(data_dict[cf]['Size'].index)
                    # cf_stock_list = list(data_dict[cf]['Size'].columns)
                elif cf == 'risk_universe':
                    cf_date_list = list(data_dict[cf].unstack().index)
                    # cf_stock_list = list(data_dict[cf].unstack().columns)
                else:
                    cf_date_list = list(data_dict[cf].index)
                    # cf_stock_list = list(data_dict[cf].columns)
            except:
                continue
            lack_date_list = list(set(factor_data_date_list) - set(cf_date_list))
            if lack_date_list:
                if cf == 'neutral_dict':
                    raise Exception("因子评价依赖的因子：{0} 缺失数据，缺失日期：{1}".format('Size', lack_date_list))
                else:
                    raise Exception("因子评价依赖的因子：{0} 缺失数据，缺失日期：{1}".format(cf, lack_date_list))

        pprint('Filter factor by universe')
        data_dict['factor_data'] = factor_data.reindex(columns=data_dict['stock_filter_' + str(self.universe)].columns)
        # replace inf, -inf by nan
        data_dict['factor_data'][~np.isfinite(data_dict['factor_data'])] = np.nan

        pprint('Align factor with base data')
        # 数据做了整理校准（取并集）操作，不改变数据本身
        data_dict = align_data_inner(data_dict)
        data_dict['factor_data'][data_dict['stock_filter_' + str(self.universe)] == False] = np.nan
        data_dict['factor_data'] = data_dict['factor_data'].dropna(how='all', axis=1)
        data_dict = align_data_inner(data_dict)
        self._data = data_dict

    def compute_top_excess_return(self, group=5):
        """"""
        # 分层后选取收益最大层的收益
        weight = np.arange(group, 0, -1)
        weight = weight / np.sum(weight)

        if self.neutralized_data is not None:
            factor_data = self.neutralized_data
        elif self.standardized_data is not None:
            factor_data = self.standardized_data
        else:
            factor_data = self.data['factor_data']

        factor_top = factor_data[factor_data.rank(pct=True, ascending=False, axis=1) < (1. / group)]  #### top 20% stock

        _ = segment_test(factor_top, self.data[self.price_use], self.holding_period,
                         self.data[self.bmk_use], group,
                         handle_return_outlier=self.robust_segment, transaction_cost=self.transaction_cost)

        select_cols = ['Q' + str(i) for i in np.arange(1, group + 1)]

        if self.transaction_cost is None:
            seg_return = _
            seg_return_top = seg_return
        else:
            seg_return, seg_return_after_cost = _[0], _[1]
            seg_return_top = seg_return_after_cost

        er_col, top_q, bottom_q = find_er_ls_col(seg_return_top)
        if int(top_q[1:]) > int(bottom_q[1:]):
            weight = weight[::-1]
        top_return = seg_return_top[select_cols].multiply(weight, axis=1).sum(axis=1)  # 每一层的收益加权
        top_excess_return = top_return - seg_return_top[er_col[0:2]] + seg_return_top[er_col]
        return top_excess_return

    def sample_random(self, excess, random_state=0, bootstrap_steps=9):
        ## sample containing two parts
        # part 1: 10% of the sample
        sample_90, sample_10 = train_test_split(excess, test_size=1. / (bootstrap_steps + 1), random_state=random_state)
        # part 2:bootstrap sampling of the rest 90%
        excess_sample = sample_10.tolist()
        for i in range(bootstrap_steps):
            sample_new = sample_90.sample(n=len(sample_10), replace=True, random_state=random_state).tolist()
            excess_sample += sample_new
            random_state += 10
        return pd.Series(excess_sample).mean()

    def compute_sampling_ret_stat(self, excess_return, in_sample=True, random_state=0, bootstrap_steps=9,
                                  experiment_steps=10):
        """
        random sampling of excess return
        """
        assert bootstrap_steps >= 1, "bootstrap_steps must be >= 1"
        sample_bin_ret_mean = []
        for i in range(experiment_steps):
            sample_bin_ret_mean.append(
                self.sample_random(excess_return, random_state=random_state, bootstrap_steps=bootstrap_steps) * 1e4)
            random_state += 1
        sample_bin_ret_mean = pd.Series(sample_bin_ret_mean, index=np.arange(1, experiment_steps + 1))

        bins_ret_diff2ret = (sample_bin_ret_mean.nlargest(
            int(experiment_steps / 2)).mean() - sample_bin_ret_mean.nsmallest(
            int(experiment_steps / 2)).mean()) / sample_bin_ret_mean.mean()
        std2ret = sample_bin_ret_mean.std() / sample_bin_ret_mean.mean()

        sample_bins_ret_stat = pd.DataFrame([bins_ret_diff2ret, std2ret])
        sample_bins_ret_stat.index = ['bins_ret_diff2ret', 'std2ret']
        sample_bins_ret_stat.columns = ['sample_bins_ret_stat']

        sample_bin_ret_mean = sample_bin_ret_mean.to_frame()
        sample_bin_ret_mean.columns = ['sample_bin_ret_mean']

        bin_ret_diff = pd.DataFrame(index=excess_return.index[::5],
                                    columns=[str(i) for i in np.arange(1, experiment_steps + 1)] + ['bins_ret_diff2ret',
                                                                                                    'sample_std2ret'])
        if bin_ret_diff.shape[0] <= 50:
            print('warning, date num less than 250')
            sample_bins_ret_diff2ret = np.nan
            sample_std2ret = np.nan

        for sdate, edate in zip(bin_ret_diff.index, bin_ret_diff.index[50:]):
            ret_list = []
            for iexp in np.arange(1, experiment_steps + 1):
                _ = self.sample_random(excess_return[sdate:edate], random_state=iexp) * 1e4
                ret_list.append(_)
                bin_ret_diff.loc[edate, str(iexp)] = _
            ret_list = pd.Series(ret_list, index=np.arange(1, experiment_steps + 1))
            ret_mean = ret_list.mean()
            bin_ret_diff.loc[edate, 'bins_ret_diff2ret'] = (ret_list.nlargest(
                int(experiment_steps / 2)).mean() - ret_list.nsmallest(int(experiment_steps / 2)).mean()) / ret_mean
            bin_ret_diff.loc[edate, 'sample_std2ret'] = ret_list.std() / ret_mean

        sample_bins_ret_diff2ret = bin_ret_diff['bins_ret_diff2ret'].dropna()
        sample_std2ret = bin_ret_diff['sample_std2ret'].dropna()

        return sample_bin_ret_mean, sample_bins_ret_stat, sample_bins_ret_diff2ret, sample_std2ret

    def compute_calmar_ratio_half_year(self, excess_return):
        year_list = np.unique(excess_return.index.year.tolist())
        half_year_list = []
        for year in year_list:
            half_year_list.append(str(year) + '0701')
            half_year_list.append(str(year) + '1231')

        calmar_ratio = {}
        for idx, half in enumerate(half_year_list):
            if idx == 0:
                sub_part_ret = excess_return[:half]
            else:
                sub_part_ret = excess_return[half_year_list[idx - 1]:half]
            if len(sub_part_ret.dropna()):
                sub_part_ret = sub_part_ret.dropna()
                nav = (1. + sub_part_ret).cumprod()
                calmar = sub_part_ret.mean() / np.abs(max_drawdown(nav))
                calmar_ratio[half] = calmar
        if len(calmar_ratio):
            calmar_ratio = pd.Series(calmar_ratio).to_frame()
            calmar_ratio.columns = ['calmar_ratio']
            return calmar_ratio
        else:
            return np.nan

    def algo_shoot(self):
        """
        new metrics added by algo group
        """
        pprint('compute new metrics ......')

        excess_return = self.compute_top_excess_return()

        sample_stat = self.compute_sampling_ret_stat(excess_return)
        self.output_dict['sample_bin_ret_mean'] = sample_stat[0]
        self.output_dict['sample_bins_ret_stat'] = sample_stat[1]
        self.output_dict['sample_bins_ret_diff2ret'] = sample_stat[2]
        self.output_dict['sample_std2ret'] = sample_stat[3]

        self.output_dict['Calmar_half_year'] = self.compute_calmar_ratio_half_year(excess_return)

    def generate_report(self, factor_data, factor_data_num):
        excel_saver(self.output_dict, self.excel_name)
        save_pickle(self.output_dict, self.pickle_name)

        pprint('Generating pdf report')
        # calculate correlation with existing factors
        factor_data.index = map(lambda x: x.strftime('%Y%m%d'), factor_data.index)

        self.pdf_name = generate_pdf(self.pickle_name, factor_data_num=factor_data_num)
        pprint('* Finished - %s *' % (self.name))

    def run_backtest(self, factor_data, name='test_factor', result_folder='test_factor', factor_data_num=0,
                     msg_type='backtest_factor'):
        """"""
        self.load_factor(factor_data=factor_data, name=name)
        self.shoot(result_folder=result_folder)
        if msg_type == "backtest_trace":
            return

        #### new metrics
        self.algo_shoot()
        self.generate_report(factor_data, factor_data_num)

@event_trace
def DayFactorBacktest(start_date, end_date, factor_name, factor_data, result_folder='./',
                      universe='alpha_universe', benchmark='alpha_universe', transaction_cost=0, holding_period=1,
                      segment_number=10, median=True, standard=True, fillna=True, seg_by_industry=True,
                      industry_type='CITIC_I', msg_type='backtest_factor', valid_rat=0.8, neutralize=True,
                      ret_price='vwap'):
    # msg_type 根据回测模式不同有以下参数决定是否返回及返回哪些回测指标的信息：web_release版本: 'backtest_system', web_develop版本: 'backtest_user',
    # web_tiny_release版本: 'backtest_trace', 默认直接调用不返回kafka消息：'backtest_factor'
    factor_data_c = factor_data.copy()
    if isinstance(factor_data_c.index, pd.MultiIndex):
        assert len(factor_data_c.columns) == 1, "仅支持对单个因子进行回测！"
        factor_data_c.index.names = ['mddate', 'stock']
        factor_data_c.reset_index(inplace=True)
        factor_data_c['mddate'] = factor_data_c['mddate'].astype(str).apply(pd.Timestamp)
        factor_data_c.set_index(['mddate', 'stock'], inplace=True)
        factor_data_c = factor_data_c.unstack()[factor_name]
        factor_data_c = factor_data_c[
            (factor_data_c.index >= pd.Timestamp(str(start_date))) & (factor_data_c.index <= pd.Timestamp(str(end_date)))]
    bd = BasicData()
    try:
        dt.datetime.strptime(start_date, '%Y/%m')
        origin_start_date = start_date.split('/')
        start_date = '{}{}{}'.format(origin_start_date[0], origin_start_date[1], '01')
    except:
        start_date = start_date
    try:
        dt.datetime.strptime(end_date, '%Y/%m')
        origin_end_date = end_date.split('/')
        last_day_of_month = str(calendar.monthrange(int(origin_end_date[0]), int(origin_end_date[1]))[1])
        end_date = '{}{}{}'.format(origin_end_date[0], origin_end_date[1], last_day_of_month)
    except:
        end_date = end_date
    if not isinstance(factor_data_c, pd.DataFrame):
        raise Exception("factor_data 为MultiIndex类型的DataFrame！")
    factor_not_nan = factor_data_c.dropna(how='all')
    factor_data_num = len(factor_not_nan)
    date_list = bd.get_trading_day(start_date, end_date)
    if factor_data_num < 42:
        raise Exception("有效数据的日期为 {0} 天，所选的日期区间中至少42天必须有因子值!".format(factor_data_num))
    if factor_data_num / len(date_list) < valid_rat:
        raise Exception("所选的日期区间[{0}:{1}]超过{2}".format(start_date, end_date,
                                                       str(round((1 - valid_rat), 2) * 100) + "%的日期因子值全为nan!"))
    instance = FactorBacktest(start_date, end_date, universe=universe, holding_period=holding_period,
                              benchmark=benchmark, transaction_cost=transaction_cost, segment_number=segment_number,
                              seg_by_industry=seg_by_industry, interest_type='cumprod', ret_price=ret_price,
                              ret_shift=False, ic_type='original', median=median, standard=standard, fillna=fillna,
                              industry_type=industry_type, neutralize=neutralize)
    instance.run_backtest(factor_data_c, name=factor_name, result_folder=result_folder, factor_data_num=factor_data_num,
                          msg_type=msg_type)

    if msg_type in ["backtest_user", "backtest_system", "backtest_trace"]:
        mes_data = {"msgType": msg_type,
                    "factorName": factor_name,
                    "factorId": os.environ.get('factor_id'),
                    "ic": instance.IC,
                    "ir": instance.IR,
                    "dayRet": round(instance.day_ret * 100, 3) if instance.day_ret else instance.day_ret,
                    "weekRet": round(instance.week_ret * 100, 3) if instance.week_ret else instance.week_ret,
                    "monthRet": round(instance.month_ret * 100, 3) if instance.month_ret else instance.month_ret,
                    "dayBenchmarkRet": round(instance.day_benchmark_ret * 100, 3),
                    "weekBenchmarkRet": round(instance.week_benchmark_ret * 100, 3),
                    "monthBenchmarkRet": round(instance.month_benchmark_ret * 100, 3),
                    "universe": universe,
                    "startDate": start_date,
                    "endDate": end_date,
                    "segmentNumber": segment_number,
                    "transactionCost": transaction_cost,
                    "holdingPeriod": holding_period,
                    "benchmark": benchmark,
                    "uuid": os.environ.get('uuid'),
                    "calcDate": "{}_{}".format(start_date, end_date),
                    "createTime": time.strftime('%Y-%m-%d %H:%M:%S'),
                    "annReturn": round(instance.excess_return_dict['annReturn'], 5) if not np.isnan(instance.excess_return_dict['annReturn']) else '',
                    "annVol": round(instance.excess_return_dict['annVol'], 5) if not np.isnan(instance.excess_return_dict['annVol']) else '',
                    "sharpe": round(instance.excess_return_dict['sharpe'], 5) if not np.isnan(instance.excess_return_dict['sharpe']) else '',
                    "mdd": round(instance.excess_return_dict['mdd'], 5) if not np.isnan(instance.excess_return_dict['mdd']) else '',
                    "hitRate": round(instance.excess_return_dict['hitRate'], 5) if not np.isnan(instance.excess_return_dict['hitRate']) else ''}
        print("回测指标计算完成")

        if msg_type in ["backtest_user", "backtest_system"]:
            file_name = instance.pdf_name.split("/")[-1]
            pdfurl, fileName = SendFile(instance.pdf_name, file_name, os.environ["exec_env"])
            mes_data["pdfurl"] = pdfurl
            mes_data["fileName"] = fileName
            print("回测报告上传成功")
        return mes_data


if __name__ == '__main__':
    t0 = time.time()
    msg_type = "backtest_user"
    start_date = os.environ.get('start_date')
    end_date = os.environ.get('end_date')
    result_folder = '/home/appadmin/'
    factor_name = os.environ.get('factor_name')
    universe = os.environ.get('universe')
    benchmark = os.environ.get('benchmark')
    transaction_cost = float(os.environ.get('transaction_cost'))
    holding_period = int(os.environ.get('holding_period'))
    segment_number = int(os.environ.get('segment_number'))
    median = bool(int(os.environ.get('median')))
    standard = bool(int(os.environ.get('standard')))
    fillna = bool(int(os.environ.get('fillna')))
    seg_by_industry = bool(int(os.environ.get('seg_by_industry')))
    industry_type_environ = os.environ.get('industry_type')
    if industry_type_environ == "中信行业":
        industry_type = 'CITIC_I'
    else:
        industry_type = 'CITIC_I'
    # 需要取因子数据
    factor_data = pd.read_pickle('ZaoYinTrader.pkl')
    factor_data = factor_data[
        (factor_data.index >= pd.Timestamp(str(start_date))) & (factor_data.index <= pd.Timestamp(str(end_date)))]
    DayFactorBacktest(start_date, end_date, factor_name, factor_data, result_folder=result_folder, universe=universe,
                      benchmark=benchmark, transaction_cost=transaction_cost, holding_period=holding_period,
                      segment_number=segment_number, median=median, standard=standard, fillna=fillna,
                      seg_by_industry=seg_by_industry, industry_type=industry_type, msg_type=msg_type)
    print("spend time %s" % (time.time() - t0))
