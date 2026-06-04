import os
# os.environ["DSWMAP_username"] = "013150"


import pandas as pd
import numpy as np
import json
import calendar
import datetime as dt
import time
import threading
import requests
from tquant.strategy.day_factor_backtest_new.backtest.factor_test import SingleFactorTest
from tquant.strategy.day_factor_backtest_new.util.utility import excel_saver, save_pickle, pprint
from tquant.strategy.day_factor_backtest_new.report.report_generator import generate_pdf_customization
from tquant.strategy.day_factor_backtest_new.data.data_preprocess import align_data_inner
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

    def generate_report(self, factor_data, factor_data_num, module=None, cost_flag=True):
        pprint('Generating pdf report')
        save_pickle(self.output_dict, self.pickle_name)
        # calculate correlation with existing factors
        factor_data.index = map(lambda x: x.strftime('%Y%m%d'), factor_data.index)
        self.pdf_name = generate_pdf_customization(factor_name=self.name, pickle_name=self.pickle_name,
                                                   factor_data_num=factor_data_num, module=module, cost_flag=cost_flag)
        pprint('* Finished - %s *' % (self.name))

    def run_backtest(self, factor_data, name='test_factor', result_folder='test_factor', factor_data_num=0,
                     msg_type='backtest_factor', module='complete'):
        """"""
        self.load_factor(factor_data=factor_data, name=name)
        self.shoot(result_folder=result_folder, module=module)
        if msg_type == "backtest_trace":
            return
        cost_flag = False if not self.transaction_cost else True
        self.generate_report(factor_data, factor_data_num, module=module, cost_flag=cost_flag)


@event_trace
def DayFactorBacktest(start_date, end_date, factor_name, factor_data, result_folder='./',
                      universe='alpha_universe', benchmark='alpha_universe', transaction_cost=0, holding_period=1,
                      segment_number=10, median=True, standard=True, fillna=True, seg_by_industry=True,
                      industry_type='CITIC_I', msg_type='backtest_factor', valid_rat=0.8, neutralize=True,
                      module='complete'):
    # msg_type 根据回测模式不同有以下参数决定是否返回及返回哪些回测指标的信息：web_release版本: 'backtest_system', web_develop版本: 'backtest_user',
    # web_tiny_release版本: 'backtest_trace', 默认直接调用不返回kafka消息：'backtest_factor'

    if isinstance(factor_data.index, pd.MultiIndex):
        assert len(factor_data.columns) == 1, "仅支持对单个因子进行回测！"
        factor_data.index.names = ['mddate', 'stock']
        factor_data.reset_index(inplace=True)
        factor_data['mddate'] = factor_data['mddate'].astype(str).apply(pd.Timestamp)
        factor_data.set_index(['mddate', 'stock'], inplace=True)
        factor_data = factor_data.unstack()[factor_name]
        factor_data = factor_data[
            (factor_data.index >= pd.Timestamp(str(start_date))) & (factor_data.index <= pd.Timestamp(str(end_date)))]
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
    if not isinstance(factor_data, pd.DataFrame):
        raise Exception("factor_data 为MultiIndex类型的DataFrame！")
    factor_not_nan = factor_data.dropna(how='all')
    factor_data_num = len(factor_not_nan)
    date_list = bd.get_trading_day(start_date, end_date)
    if factor_data_num < 42:
        raise Exception("有效数据的日期为 {0} 天，所选的日期区间中至少42天必须有因子值!".format(factor_data_num))
    if factor_data_num / len(date_list) < valid_rat:
        raise Exception("所选的日期区间[{0}:{1}]超过{2}".format(start_date, end_date,
                                                       str(round((1 - valid_rat), 2) * 100) + "%的日期因子值全为nan!"))
    instance = FactorBacktest(start_date, end_date, universe=universe, holding_period=holding_period,
                              benchmark=benchmark, transaction_cost=transaction_cost, segment_number=segment_number,
                              seg_by_industry=seg_by_industry, interest_type='cumprod', ret_price='vwap',
                              ret_shift=False, ic_type='original', median=median, standard=standard, fillna=fillna,
                              industry_type=industry_type, neutralize=neutralize)
    instance.run_backtest(factor_data, name=factor_name, result_folder=result_folder, factor_data_num=factor_data_num,
                          msg_type=msg_type, module=module)

    day_ret, week_ret, month_ret, ann_return, ann_vol, sharpe, mdd, hit_rate = '', '', '', '', '', '', '', ''
    if module in ['basic_segment', 'basic_seg_stab',  'industry', 'complete']:
        day_ret = round(instance.excess_return_dict['day_ret'] * 100, 3) if instance.excess_return_dict['day_ret'] else day_ret
        week_ret = round(instance.excess_return_dict['week_ret'] * 100, 3) if instance.excess_return_dict['week_ret'] else week_ret
        month_ret = round(instance.excess_return_dict['month_ret'] * 100, 3) if instance.excess_return_dict['month_ret'] else month_ret
        ann_return = round(instance.excess_return_dict['annReturn'], 5) if not np.isnan(
            instance.excess_return_dict['annReturn']) else ''
        ann_vol = round(instance.excess_return_dict['annVol'], 5) if not np.isnan(
            instance.excess_return_dict['annVol']) else ''
        sharpe = round(instance.excess_return_dict['sharpe'], 5) if not np.isnan(
            instance.excess_return_dict['sharpe']) else ''
        mdd = round(instance.excess_return_dict['mdd'], 5) if not np.isnan(instance.excess_return_dict['mdd']) else ''
        hit_rate = round(instance.excess_return_dict['hitRate'], 5) if not np.isnan(
            instance.excess_return_dict['hitRate']) else ''

    if msg_type in ["backtest_user", "backtest_system", "backtest_trace"]:
        mes_data = {"msgType": msg_type,
                    "factorName": factor_name,
                    "factorId": os.environ.get('factor_id'),
                    "ic": instance.IC,
                    "ir": instance.IR,
                    "dayRet": day_ret,
                    "weekRet": week_ret,
                    "monthRet": month_ret,
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
                    "annReturn": ann_return,
                    "annVol": ann_vol,
                    "sharpe": sharpe,
                    "mdd": mdd,
                    "hitRate": hit_rate}
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
