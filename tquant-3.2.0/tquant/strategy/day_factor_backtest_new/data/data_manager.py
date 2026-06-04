import pandas as pd
import numpy as np
from tquant import StockData, BasicData
from tquant.strategy.day_factor_backtest_new.util.utility import get_trading_day_offset

universe_set = {'sz50':'index_50', 'hs300':'index_300', 'zz500':'index_500', 'zz800': 'index_800', 'zz1000':'index_1000',
                'risk_universe': 'risk_universe', 'alpha_universe':'alpha_universe'}  # , 'index_800'
index_lookup = {'zz500': '000905.SH', 'sz50': '000016.SH', 'hs300': '000300.SH', 'zz800': '000906.SH',
                'zz1000': '000852.SH',
                'wind_alla': '881001.WI'}  # 'zz800': '000906.SH',
prev_len = 20  # for holding period return
corr_len = 60  # style correlation


class DataManager:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            return cls.__instance
        else:
            obj = object.__new__(cls)
            cls.__instance = obj
            cls.__instance.__initialized = False
            return cls.__instance

    def __init__(self, start_date=None, end_date=None, price_use='close', universe='alpha_universe', holding_period=1,
                 ret_shift=True, ic_type='original', industry_type='CITIC_I',benchmark='alpha_universe'):

        self.sd = StockData()
        self.bd = BasicData()
        self.start_date = start_date
        self.end_date = end_date
        self.universe = universe
        self.seg_benchmark = benchmark
        self.benchmark = benchmark
        self.holding_period = holding_period
        self.price_use = price_use
        self.ret_shift = ret_shift
        self.ic_type = ic_type
        self.industry_type = industry_type
        self.data_dict = {}
        if self.__initialized:
            return
        self.__initialized = True

    def median_filter(self, factor_data=None, mad=3, winsor=False):
        """
        :param factor_data:
        :param mad:
        :param winsor: 是否使用winsor截尾
        :return:
        # """
        # if not factor_data:
        #     factor_data = self.factor_data.copy()
        dm = factor_data.median(axis=1)
        # caution of symmetric uppper & lower bounds
        dist_dm = (factor_data.subtract(dm, axis=0)).abs().median(axis=1)
        date_num, stock_num = factor_data.shape
        fac_ub = pd.DataFrame(np.tile(dm + mad * dist_dm, [stock_num, 1]).T, index=factor_data.index,
                              columns=factor_data.columns)
        fac_lb = pd.DataFrame(np.tile(dm - mad * dist_dm, [stock_num, 1]).T, index=factor_data.index,
                              columns=factor_data.columns)
        if winsor:
            factor_data[factor_data > fac_ub] = np.nan
            factor_data[factor_data < fac_lb] = np.nan
        else:
            factor_data[factor_data > fac_ub] = fac_ub
            factor_data[factor_data < fac_lb] = fac_lb
        return factor_data

    def load_evaluation_data(self):
        if self.seg_benchmark in ['hs300', 'zz500', 'sh50', 'zz800', 'zz1000', 'sz50']:
            if self.seg_benchmark == 'sz50':
                self.seg_benchmark = 'sh50'
            eval_factors = [universe_set[self.universe], 'filter_stpt', self.industry_type] + ['index_weight_' + self.seg_benchmark]
        else:
            eval_factors = [universe_set[self.universe], 'filter_stpt', self.industry_type]
        stock_list = self.sd.get_plate_info('MARKET', self.end_date, 'ALLA_HIS')['stock'].tolist()
        evaluation_df = self.sd.get_factor_evaluation(stock_list, (self.start_date, self.end_date), eval_factors)
        self.data_dict['evaluation_data'] = evaluation_df
        return

    def get_evaluation_data(self):
        if 'evaluation_data' not in self.data_dict:
            self.load_evaluation_data()
        return self.data_dict['evaluation_data']

    def load_valuation_metrix_data(self, factors=None):
        stock_list = self.sd.get_plate_info('MARKET', self.end_date, 'ALLA_HIS')['stock'].tolist()
        if factors is None:
            factors = ['mkt_cap_ard']
        valuation_metrics_data = self.sd.get_factor_valuation_metrics(stock_list, (self.start_date, self.end_date),
                                                                      factors, sort_option=False)

        self.data_dict['valuation_data'] = valuation_metrics_data
        return

    def get_valuation_metrix_data(self, factors=None):
        if 'valuation_data' not in self.data_dict:
            self.load_valuation_metrix_data(factors=factors)
        return self.data_dict['valuation_data']

    def load_industry_data(self):
        evaluation_df = self.get_evaluation_data()
        user_industry = evaluation_df.loc[:, [self.industry_type]]
        user_industry.reset_index(inplace=True)
        user_industry.rename(columns={"mddate": "dt", "stock": "Ticker"}, inplace=True)
        user_industry.set_index(["dt", "Ticker"], inplace=True)
        user_industry = user_industry[self.industry_type].unstack()
        user_industry.index = pd.DatetimeIndex(user_industry.index)
        stock_industry_df = user_industry
        self.data_dict['industry_data'] = stock_industry_df
        return

    def get_industry_data(self):
        if 'industry_data' not in self.data_dict:
            self.load_industry_data()
        return self.data_dict['industry_data']

    def load_size_data(self):
        mkt_cap_data_ori = self.get_valuation_metrix_data(factors=['mkt_cap_ard'])
        stock_filter = self.get_stock_filter_data()

        mkt_cap_data = mkt_cap_data_ori.reset_index()
        mkt_cap_data.rename(columns={"mddate": "dt", "stock": "Ticker"}, inplace=True)
        mkt_cap_data.set_index(["dt", "Ticker"], inplace=True)
        mkt_cap_ard = mkt_cap_data['mkt_cap_ard'].unstack()
        mkt_cap_ard.index = pd.DatetimeIndex(mkt_cap_ard.index)

        mkt_cap_ard = mkt_cap_ard.reindex(index=stock_filter.index, columns=stock_filter.columns)
        lncap = np.log(mkt_cap_ard)
        lncap = self.median_filter(lncap, mad=5, winsor=False)
        std_ts = lncap.std(axis=1, ddof=0)
        std_ts.loc[std_ts == 0] = 1
        size_data = lncap.subtract(lncap.mean(axis=1), axis=0).divide(std_ts, axis=0)
        self.data_dict['size_data'] = size_data
        return

    def get_size_data(self):
        if 'size_data' not in self.data_dict:
            self.load_size_data()
        return self.data_dict['size_data']

    def load_stock_filter_data(self):
        evaluation_df = self.get_evaluation_data()
        h5_filter = evaluation_df.loc[:, [universe_set[self.universe], 'filter_stpt']]
        for f in h5_filter.columns:
            h5_filter[f].fillna(value=0, inplace=True)
            h5_filter[f] = h5_filter[f].astype(int).astype(bool)
        h5_filter.reset_index(inplace=True)
        h5_filter.rename(columns={"mddate": "dt", "stock": "Ticker"}, inplace=True)
        h5_filter.set_index(["dt", "Ticker"], inplace=True)
        h5_filter = h5_filter.fillna(value=False)
        if self.universe in universe_set.keys():
            compound_filter = h5_filter[universe_set[self.universe]] & h5_filter['filter_stpt']
        else:
            compound_filter = h5_filter['filter_stpt']
        stock_filter_df = compound_filter.unstack().fillna(value=False)
        stock_filter_df.index = pd.DatetimeIndex(stock_filter_df.index)
        self.data_dict['stock_filter'] = stock_filter_df
        return

    def get_stock_filter_data(self):
        if 'stock_filter' not in self.data_dict:
            self.load_stock_filter_data()
        return self.data_dict['stock_filter']

    def load_price_use_data(self):
        date_list = self.bd.get_trading_day(self.start_date, self.end_date)
        stock_list = self.sd.get_plate_info('MARKET', self.end_date, 'ALLA_HIS')['stock'].tolist()
        md_list_df = self.sd.get_factor_price_daily(stock_list, date_list, [self.price_use, 'adjfactor'], sort_option=False,
                                                    fill_na=False)
        md_dict = {}
        stock_filter = self.get_stock_filter_data()

        for fac in [self.price_use, 'adjfactor']:
            sub_df = md_list_df.loc[:, fac].unstack()
            sub_df.replace(0.0, np.nan, inplace=True)
            sub_df.fillna(method='ffill', inplace=True)
            sub_df.index.name = 'dt'
            sub_df.index = pd.DatetimeIndex(sub_df.index)
            sub_df = sub_df.reindex(index=stock_filter.index, columns=stock_filter.columns)
            md_dict[fac] = sub_df
        price_adj_data = md_dict[self.price_use] * md_dict['adjfactor']
        self.data_dict['{}_adj'.format(self.price_use)] = price_adj_data
        return

    def get_price_use_data(self):
        if '{}_adj'.format(self.price_use) not in self.data_dict:
            self.load_price_use_data()
        return self.data_dict['{}_adj'.format(self.price_use)]

    def load_benchmark_data(self):
        if (self.benchmark in universe_set.keys() and self.benchmark == self.universe) or self.benchmark not in list(
                index_lookup.keys()):
            # daily return average - return2price - dummy price
            # self.price_name的增长率
            stock_filter_df = self.get_stock_filter_data()
            price_use_df = self.get_price_use_data()
            stk_ret = price_use_df / price_use_df.shift(1) - 1  # fix
            stk_ret.replace([np.inf, -np.inf], 0.0, inplace=True)  # bug修复，收益率为inf时替换为0
            universe_ret = stk_ret[
                stock_filter_df.reindex(index=stk_ret.index, columns=stk_ret.columns).fillna(value=False)].mean(
                axis=1)  # 市场每日平均收益
            universe_ret.iloc[0] = 0.0
            benchmark_price = (universe_ret + 1).cumprod()  # 市场每日累计收益
        else:
            # bie 切换数据源
            index_list = ['000300.SH', '000905.SH', '000016.SH', '000906.SH', '000852.SH']
            prev_date = max(get_trading_day_offset(self.start_date, -prev_len)[0], pd.Timestamp(20090105)).strftime(
                '%Y%m%d')
            index_price = self.sd.get_factor_price_daily(index_list, (prev_date, self.end_date), ['close'],
                                                         fill_na=True)
            index_price.reset_index(inplace=True)
            index_price.rename(columns={'mddate': 'dt', 'stock': 'Ticker'}, inplace=True)
            index_price['dt'] = index_price['dt'].apply(pd.Timestamp)
            index_price.set_index(['dt', 'Ticker'], inplace=True)
            benchmark_price = index_price.unstack()['close'][index_lookup[self.benchmark]]
        self.data_dict['benchmark_price'] = benchmark_price
        return

    def get_benchmark_data(self):
        if 'benchmark_price' not in self.data_dict:
            self.load_benchmark_data()
        return self.data_dict['benchmark_price']

    def load_holding_period_ret_data(self):
        """
        :param seg_benchmark:
        :param price_use:
        :param universe:
        :param holding_period:
        :param ret_shift:
        :return:
        """
        price_use_df = self.get_price_use_data()
        stock_filter_df = self.get_stock_filter_data()

        hpr_df = price_use_df.shift(-1 * self.holding_period) / price_use_df - 1
        hpr_df[~stock_filter_df] = np.nan
        if self.ret_shift:
            hpr_df = hpr_df.shift(-1)
        self.data_dict['hpr_data'] = hpr_df
        return

    def get_holding_period_ret_data(self):
        if 'hpr_data' not in self.data_dict:
            self.load_holding_period_ret_data()
        return self.data_dict['hpr_data']

    def load_industry_weight_data(self):
        industry_data = self.get_industry_data()
        stock_weight = self.get_stock_weight_data()
        _stock_industry = pd.DataFrame(industry_data.stack(), columns=['Industry'])
        # 计算行业内股票权重，每个行业权重未股票权重加和。stock_weight是全市场票的市值加权。
        weight_grouped = pd.concat([_stock_industry, stock_weight], axis=1).groupby(['dt', 'Industry'])
        industry_weight = weight_grouped['stock_weight'].sum()
        self.data_dict['industry_weight'] = industry_weight / industry_weight.groupby('dt').sum()
        return

    def get_industry_weight_data(self):
        if 'industry_weight' not in self.data_dict:
            self.load_industry_weight_data()
        return self.data_dict['industry_weight']

    def load_stock_weight_data(self):
        if self.seg_benchmark in ['hs300', 'zz500', 'sh50', 'zz800', 'zz1000']:
            evaluation_df = self.get_evaluation_data()
            stock_weight = evaluation_df.loc[:, ['index_weight_' + self.seg_benchmark]]
            stock_weight.reset_index(inplace=True)
            stock_weight.rename(columns={"mddate": "dt", "stock": "Ticker"}, inplace=True)
            stock_weight['dt'] = stock_weight['dt'].apply(pd.Timestamp)
            stock_weight.set_index(["dt", "Ticker"], inplace=True)
            stock_weight.columns = ['stock_weight']
        else:
            mkt_cap_data_ori = self.get_valuation_metrix_data(factors=['mkt_cap_ard'])
            stock_filter = self.get_stock_filter_data()
            # TODO： 小bug，退市票需要去掉之后，再计算市值权重
            mkt_cap_ard = mkt_cap_data_ori.iloc[:, 0].unstack()
            mkt_cap_ard.index = pd.DatetimeIndex(mkt_cap_ard.index)
            mkt_cap_ard = mkt_cap_ard.reindex(index=stock_filter.index, columns=stock_filter.columns)
            mkt_cap_ard[~stock_filter] = np.nan
            mkt_cap_ard_MI = mkt_cap_ard.stack()
            stock_weight = pd.DataFrame(mkt_cap_ard_MI / mkt_cap_ard_MI.groupby('dt').sum())
            stock_weight.columns = ['stock_weight']
        #     stock_weight = stock_weight[stock_weight.columns[0]].unstack()
        self.data_dict['stock_weight'] = stock_weight
        return

    def get_stock_weight_data(self):
        if 'stock_weight' not in self.data_dict:
            self.load_stock_weight_data()
        return self.data_dict['stock_weight']
