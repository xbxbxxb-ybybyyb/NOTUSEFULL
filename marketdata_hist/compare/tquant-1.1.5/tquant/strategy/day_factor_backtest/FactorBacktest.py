import os
import sys
sys.path.append('..')
sys.path.append("../..")
import pandas as pd
import numpy as np

from tquant.strategy.day_factor_backtest.backtest.factor_test import SingleFactorTest
from tquant.strategy.day_factor_backtest.backtest.utility import *
from tquant.strategy.day_factor_backtest.backtest.segment_test import segment_test
from tquant.strategy.day_factor_backtest.backtest.report_generator import generate_pdf
from sklearn.model_selection import train_test_split
from tquant import tq_logger


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
        #分层后选取收益最大层的收益
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
        top_return = seg_return_top[select_cols].multiply(weight, axis=1).sum(axis=1)#每一层的收益加权
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
            half_year_list.append(str(year) + '0630')
            half_year_list.append(str(year) + '1231')

        calmar_ratio = {}
        for idx, half in enumerate(half_year_list):
            if idx == 0:
                sub_part_ret = excess_return[:half]
            else:
                sub_part_ret = excess_return[half_year_list[idx - 1]:half]
            if len(sub_part_ret):
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

    def generate_report(self, factor_data):
        excel_saver(self.output_dict, self.excel_name)
        save_pickle(self.output_dict, self.pickle_name)

        pprint('Generating pdf report')
        # calculate correlation with existing factors
        factor_data.index = map(lambda x: x.strftime('%Y%m%d'), factor_data.index)

        generate_pdf(self.pickle_name)
        pprint('* Finished - %s *' % (self.name))

    def run_backtest(self, factor_data, name='test_factor', result_folder='test_factor'):
        """"""
        self.load_factor(factor_data=factor_data, name=name)
        self.shoot(result_folder=result_folder)

        #### new metrics
        self.algo_shoot()
        self.generate_report(factor_data)


def DayFactorBacktest(start_date, end_date, factor_name, factor_data, result_folder, universe='alpha_universe',
                      benchmark='alpha_universe', transaction_cost=0.0013, holding_period=1, segment_number=10,
                      median=True, standard=True, fillna=False, seg_by_industry=False, industry_type='CITIC_I'):
    instance = FactorBacktest(start_date, end_date, universe=universe, holding_period=holding_period,
                              benchmark=benchmark, transaction_cost=transaction_cost, segment_number=segment_number,
                              seg_by_industry=seg_by_industry, interest_type='cumprod', ret_price='close', ret_shift=True,
                              ic_type='original', median=median, standard=standard, fillna=fillna, industry_type=industry_type)
    instance.run_backtest(factor_data, name=factor_name, result_folder=result_folder)


if __name__ == '__main__':
    # SJL至少选一年时间,data_dict.pkl的时间范围为20180101到20190630，因此本时间不能超出这个范围
    import time

    t0 = time.time()
    start_date = 20180108
    end_date = 20190630
    # /app/data/SHARE_20/AlphaDataCenter/Factor/daily
    # /app/data/SHARE_20/AlphaDataCenter/Factor/barra
    # factor_name = "ZaoYinTrader"
    # factor_data = pd.read_pickle('../backtest_data/{}.pkl'.format(factor_name))
    # #SJL factor_data的起止时间不能大于strategy/data文件夹下是文件时间
    # factor_data = factor_data[(factor_data.index>=pd.Timestamp(str(start_date))) & (factor_data.index<=pd.Timestamp(str(end_date)))]
    result_folder = '/home/appadmin/'
    import tquant
    print(tquant)
    from tquant import StockData
    from tquant import BasicData

    sd = StockData()
    bd = BasicData()
    tradingdate = bd.get_trading_day(end_date, -5)[-1]
    stock_list = sd.get_plate_info('MARKET', tradingdate, 'ALLA_HIS')['stock'].tolist()
    factor_name = "ev2"
    factor_data = sd.get_factor_valuation_metrics(stock_list, (str(start_date), str(end_date)), [factor_name])
    factor_data.reset_index(inplace=True)
    factor_data['mddate'] = factor_data['mddate'].apply(pd.Timestamp)

    factor_data.set_index(['mddate', 'stock'], inplace=True)
    factor_data = factor_data.unstack()[factor_name]

    DayFactorBacktest(start_date, end_date, factor_name, factor_data, result_folder)
    print("spend time %s" % (time.time() - t0))
