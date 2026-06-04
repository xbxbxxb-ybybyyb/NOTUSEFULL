import pandas as pd
from tquant import StockData
from tquant import BasicData

sd = StockData()
bd = BasicData()


class DataIsUniverse:
    def __init__(self, start_date, end_date, item):
        self.start_date = start_date
        self.end_date = end_date
        self.item = item
        self.stocks = sd.get_plate_info('MARKET', self.end_date, 'ALLA_HIS').loc[:, 'stock'].tolist()
        self.stock_info_df = sd.get_factor_newsmsg(self.stocks, ['listing_date', 'delisting_date'])
        self.stock_info_df.fillna(0, inplace=True)
        self.stock_info_df = self.stock_info_df[(self.stock_info_df.listing_date <= int(self.end_date)) & (
                self.stock_info_df.delisting_date <= int(self.end_date))]
        self.stock_list = list(self.stock_info_df.index)

        self.mkt_cap_df = sd.get_factor_valuation_metrics(self.stock_list, (self.start_date, self.end_date),
                                                          ['mkt_cap_ard'])
        self.mkt_cap_df = self.mkt_cap_df.unstack(level=1)
        start_date_minus_half_year = bd.get_trading_day(self.start_date, -125)[0]
        self.vol_df = sd.get_factor_price_daily(self.stock_list, (start_date_minus_half_year, self.end_date),
                                                ['volume'])
        self.vol_df = self.vol_df['volume']
        self.vol_df = self.vol_df.unstack(level=1)
        # 因得到的VOLUME单位是“手”，这里转为“股”
        self.vol_df = pd.DataFrame(self.vol_df.values * 100, index=self.vol_df.index, columns=self.vol_df.columns)
        start_date_minus_10 = bd.get_trading_day(self.start_date, -10)[0]
        self.amt_close_df = sd.get_factor_price_daily(self.stock_list, (start_date_minus_10, self.end_date),
                                                      ['amt', 'close', 'adjfactor'])
        self.amt_df = self.amt_close_df.loc[:, 'amt']
        self.amt_df = self.amt_df.unstack(level=1)
        self.amt_close_df['close_adj'] = self.amt_close_df['close'] * self.amt_close_df['adjfactor']
        self.close_df = self.amt_close_df.loc[:, 'close_adj']
        self.close_df = self.close_df.unstack(level=1)

    def factor_calc(self):
        trading_day_list = bd.get_trading_day(self.start_date, self.end_date)
        alpha_universe_df = pd.DataFrame(0, columns=self.stock_list, index=trading_day_list)
        for i_day in trading_day_list:
            qualified_stock_list = self.check_qualified(i_day)
            for i_stock in qualified_stock_list:
                alpha_universe_df.at[i_day, i_stock] = 1
        ans_df = alpha_universe_df
        # ----以下勿改动----
        ans_df = ans_df.loc[self.start_date: self.end_date]
        return ans_df

    def check_qualified(self, i_date):
        i_date = int(i_date)
        print(i_date)
        if self.item in ['alpha_universe', 'risk_universe', 'alpha_universe_b']:
            pass
        else:
            raise TypeError
        # 检查i_date当天股票是否满足alpha_universe的条件

        # 条件1 上市满一年
        listing_1yr_df = self.stock_info_df[self.stock_info_df['listing_date'] <= (i_date - 10000)]
        valid_stock_list1 = list(listing_1yr_df.index)

        # 条件3 过去半年至少一半日期有正常交易
        i_date_minus_half_year = bd.get_trading_day(i_date, -125)[0]
        # i_date_minus_half_year = Dtk.get_n_days_off(i_date, -125)[0]
        vol_df = self.vol_df.loc[i_date_minus_half_year: str(i_date)].copy()
        vol_df = vol_df.clip(upper=1)  # 将交易量大于1的直接设为1
        vol_df_cumsum = vol_df.cumsum()  # 统计交易量大于1的天数
        valid_stock_array3 = vol_df_cumsum.iloc[-1]

        valid_stock_array3 = valid_stock_array3[valid_stock_array3 >= 63]
        # valid_stock_array3.reset_index(level=0, drop=True, inplace=True)
        valid_stock_list3 = list(valid_stock_array3.index)

        # 条件4 剔除市值最小的5%的股票
        mkt_cap_df_idate = self.mkt_cap_df.loc[str(i_date)].copy()
        mkt_cap_df_idate = mkt_cap_df_idate.dropna()  # 去掉没有市值的股票（就是退市股啦）
        mkt_cap_df_rank_idate = mkt_cap_df_idate.rank()  # 升序排列
        mkt_cap_df_rank_idate.reset_index(level=0, drop=True, inplace=True)
        valid_stock_array4 = mkt_cap_df_rank_idate[mkt_cap_df_rank_idate > mkt_cap_df_rank_idate.max() * 0.05]
        valid_stock_list4 = list(valid_stock_array4.index)

        # alpha_universe & risk_universe - 取条件1，3，4的交集
        valid_stock_list_step1 = set(valid_stock_list1).intersection(set(valid_stock_list3)).intersection(
            set(valid_stock_list4))

        valid_stock_list_step1 = list(valid_stock_list_step1)

        # 条件2和5——这一步非常慢，要通过量化平台过滤i_date当天STPT和停牌的股票
        valid_stock_list_step2 = sd.stock_filter(valid_stock_list_step1, str(i_date), filter_type='STSPEND')[
            'stock'].values.tolist()
        valid_stock_list_step2.sort()

        # if self.item in ['alpha_universe', 'alpha_universe_b']:
        #     valid_stock_list_step2 = xqf.stock_filter(valid_stock_list_step1, i_date, filterType='STSPEND')[
        #         'stock'].values.tolist()
        #     valid_stock_list_step2.sort()
        # else:
        #     valid_stock_list_step2 = xqf.stock_filter(valid_stock_list_step1, i_date, filterType='STPT')[
        #         'stock'].values.tolist()
        #     valid_stock_list_step2.sort()

        # 条件7，剔除当日涨幅跌幅在9.8%以上的股票
        pct_df = self.close_df / self.close_df.shift(1) - 1
        temp = pct_df.loc[str(i_date)]
        a = temp.apply(lambda x: x > -0.098 and x < 0.098)
        valid_stock_list_step7 = a.index.tolist()
        valid_stock_list_step_out = list(set(valid_stock_list_step7).intersection(set(valid_stock_list_step2)))

        # print(len(valid_stock_list_step_out))
        return valid_stock_list_step_out


def update_is_universe(start_date, end_date):
    factor_obj = DataIsUniverse(start_date, end_date, 'alpha_universe')
    ans_df = factor_obj.factor_calc()
    return ans_df
