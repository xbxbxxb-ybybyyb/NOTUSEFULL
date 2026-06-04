import pandas as pd
import numpy as np
import xfactor.test.symbol_team.DataAPI.DataToolkit as Dtk
from xfactor.test.symbol_team.DataAPI.AddressManagement import AddressManagement
add = AddressManagement()
root = add.get_root()

class LogicExcessKlineBase:
    def __init__(self, start_date, end_date, factor_value_dict):
        self.factor_value_dict = factor_value_dict
        self.ticktime_list = [i for i in self.factor_value_dict]
        self.date_list = Dtk.get_trading_day(start_date,end_date)
        self.start_date = self.date_list[0]
        self.end_date = self.date_list[-1]
        self.stock_list = Dtk.get_complete_stock_list()
        self.ret_df = self.load_ret()
        self.universe_df = self.get_universe_df()
        self.limit_status = self.get_limit_status()
        self.init_benchmark_position()

    def init_benchmark_position(self):
        self.benchmark_position = self.get_benchmark_position()
        benchmark_position_df_dic = self.transfer_benchmark_position_2_df(self.benchmark_position)
        self.benchmark_position_df_dic = benchmark_position_df_dic


    def get_universe_df(self):
        valid_start_date = Dtk.get_n_days_off(self.start_date,-3)[0]
        valid_start_date2 = Dtk.get_n_days_off(self.start_date,-2)[0]
        universe = Dtk.get_panel_daily_info(self.stock_list,valid_start_date,self.end_date,'alpha_universe').shift(1).loc[valid_start_date2:self.end_date]
        return universe

    def load_ret(self):
        start_pre_day = Dtk.get_n_days_off(self.start_date,-2)[0]
        close_df = Dtk.get_panel_min_data('close',start_pre_day,self.end_date,self.stock_list,daily_bar_num=242,forward_adj=True)
        ret = np.log(pd.DataFrame(close_df.values / close_df.shift(1).values,index = close_df.index,columns=close_df.columns))
        ans_df = ret.copy()
        return ans_df

    def get_limit_status(self):
        valid_start_date = Dtk.get_n_days_off(self.start_date,-2)[0]
        limit_status = Dtk.get_panel_min_data('limit_status',valid_start_date,self.end_date,self.stock_list,daily_bar_num=242)
        return limit_status


    def get_top_group(self,factor_data,date,ticktime):
        benchmark_stocks = self.benchmark_position[ticktime][date]
        datetime = str(date) + str(ticktime)
        pre_minute_limit_status = self.limit_status.loc[:datetime].iloc[-2].copy().fillna(1)
        limit_stocks = pre_minute_limit_status[abs(pre_minute_limit_status.values == 1)].dropna().index.tolist()
        factor_data_temp = factor_data.loc[date].copy()
        factor_data_temp.loc[limit_stocks] = np.nan
        factor_data_rk = factor_data_temp.dropna().rank(pct=True)
        top_group_stocks = factor_data_rk[factor_data_rk.values >= 0.9].dropna().index.tolist()
        if top_group_stocks.__len__() <= benchmark_stocks.__len__() * 0.3 / 10:
            top_group_stocks = benchmark_stocks
        return top_group_stocks



    def get_topgourp_position(self):
        factor_dic = self.factor_value_dict
        position_ticktime = {}
        for ticktime in self.ticktime_list:
            position_dic_ticktime = {}
            factor_data = factor_dic[ticktime].copy()
            pre_day = Dtk.get_n_days_off(self.start_date,-2)[0]
            init_top_group = self.get_top_group(factor_data,pre_day,ticktime)
            position_dic_ticktime.update({pre_day:init_top_group})
            for date in self.date_list:
                top_group = self.get_top_group(factor_data,date,ticktime)
                position_dic_ticktime.update({date:top_group})
            position_ticktime.update({ticktime:position_dic_ticktime})
        return position_ticktime

    def get_benchmark_group(self,date,ticktime):
        datetime = str(date) + str(ticktime)
        pre_minute_limit_status = self.limit_status.loc[:datetime].iloc[-2].copy().fillna(1)
        limit_stocks = pre_minute_limit_status[abs(pre_minute_limit_status.values == 1)].dropna().index.tolist()
        universe_temp = self.universe_df.loc[date].copy().fillna(0)
        universe_temp.loc[limit_stocks] = 0
        benchmark_stocks = universe_temp[universe_temp.values == 1].dropna().index.tolist()
        return benchmark_stocks

    def get_benchmark_position(self):
        position_ticktime = {}
        for ticktime in self.ticktime_list:
            position_dic_ticktime = {}
            pre_day = Dtk.get_n_days_off(self.start_date,-2)[0]
            init_benchmark_stocks = self.get_benchmark_group(pre_day,ticktime)
            position_dic_ticktime.update({pre_day:init_benchmark_stocks})
            for date in self.date_list:
                benchmark_group = self.get_benchmark_group(date,ticktime)
                position_dic_ticktime.update({date:benchmark_group})
            position_ticktime.update({ticktime:position_dic_ticktime})
        return position_ticktime


    def transfer_topgroup_position_2_df(self,tougroup_position_dic):
        ans_dic = {}
        for ticktime in self.ticktime_list:
            position_df = pd.DataFrame(0,index=self.ret_df.index,columns=self.stock_list)
            df_list = []
            for date in self.date_list:
                df_list_day = []
                if date == self.date_list[0]:
                    init_day = Dtk.get_n_days_off(date,-2)[0]
                    init_day_datetime = str(init_day) + str(ticktime)
                    temp_df = position_df.loc[str(init_day):str(init_day)].copy()
                    index_switch = temp_df.loc[init_day_datetime:].iloc[1:31].index.tolist()
                    init_day_stock = tougroup_position_dic[ticktime][init_day]
                    init_day_stock_series = pd.Series(0,index=self.stock_list)
                    init_day_stock_series.loc[init_day_stock] = 1
                    limit_status = self.limit_status.loc[index_switch].copy().fillna(1)
                    filter_df = pd.DataFrame(limit_status.values < 1,index=limit_status.index,columns=limit_status.columns)
                    weight_final = filter_df.sum() / 30 * init_day_stock_series
                    holding_overnight = weight_final / weight_final.sum()
                current_datetime = str(date) + str(ticktime)
                temp_df = position_df.loc[str(date):str(date)].copy()
                index_using_pre_day_stock = temp_df.loc[:current_datetime].index.tolist()
                index_using_both_day_stock = temp_df.loc[current_datetime:].iloc[1:31].index.tolist()
                index_using_current_day_stock = sorted(list(set(temp_df.index.tolist()) - set(index_using_pre_day_stock) - set(index_using_both_day_stock)))
                current_day_stock = tougroup_position_dic[ticktime][date]
                temp1 = pd.DataFrame((temp_df.loc[index_using_pre_day_stock].values+1) * holding_overnight.values,index=index_using_pre_day_stock,columns=self.stock_list)
                df_list_day.append(temp1)

                # pre_temp = temp_df.loc[index_using_both_day_stock].copy()
                pre_temp = pd.DataFrame(1,index=index_using_both_day_stock,columns=self.stock_list)
                pre_temp = pd.DataFrame(pre_temp.values*holding_overnight.values,index=pre_temp.index,columns=pre_temp.columns)
                weight_pre = pd.Series([(30-item-1) for item in range(30)]) / 30
                pre_temp_weighted = pd.DataFrame(pre_temp.values * weight_pre.values.reshape([pre_temp.shape[0],1]), index=pre_temp.index,
                                                 columns=pre_temp.columns)
                current_temp = pd.DataFrame(0,index=index_using_both_day_stock,columns=self.stock_list)
                current_temp[current_day_stock] = 1
                current_temp = pd.DataFrame(current_temp.values / current_temp.sum(axis=1).values.reshape([current_temp.shape[0],1]),index=current_temp.index,columns=current_temp.columns)
                limit_status_filter = self.limit_status.loc[index_using_both_day_stock].copy().fillna(1)
                filter_df = pd.DataFrame(limit_status_filter.values < 1,index=limit_status_filter.index,columns=limit_status_filter.columns)
                current_temp = pd.DataFrame(current_temp.values/30,index=current_temp.index,columns=current_temp.columns)
                current_temp_weighted = (current_temp * filter_df / filter_df).cumsum()
                current_temp_weighted.iloc[-1] = current_temp_weighted.iloc[-1] / current_temp_weighted.iloc[-1].sum()
                combine_position = pre_temp_weighted + current_temp_weighted
                temp2 = combine_position.copy()
                df_list_day.append(temp2)
                holding_overnight = current_temp_weighted.iloc[-1].copy()
                if index_using_current_day_stock.__len__() != 0:
                    temp3 = pd.DataFrame(1,index=index_using_current_day_stock,columns=self.stock_list)
                    temp3 = pd.DataFrame(temp3.values * holding_overnight.values,index=temp3.index,columns=temp3.columns)
                    df_list_day.append(temp3)
                position_df_stdrz = pd.concat(df_list_day,axis=0).fillna(0)
                df_list.append(position_df_stdrz)
            final_df = pd.concat(df_list,axis=0)
            ans_dic.update({ticktime:final_df})
        return ans_dic

    def transfer_benchmark_position_2_df(self,benchmark_position_dic):
        ans_dic = {}
        for ticktime in self.ticktime_list:
            position_df = pd.DataFrame(0, index=self.ret_df.index,columns=self.stock_list)
            df_list = []
            for date in self.date_list:
                current_datetime = str(date) + str(ticktime)
                pre_day = Dtk.get_n_days_off(date,-2)[0]
                temp_df = position_df.loc[str(date):str(date)].copy()
                index_using_pre_day_stock = temp_df.loc[:current_datetime].index.tolist()
                index_using_current_day_stock = sorted(list(set(temp_df.index.tolist()) - set(index_using_pre_day_stock)))
                pre_day_stock = benchmark_position_dic[ticktime][pre_day]
                current_day_stock = benchmark_position_dic[ticktime][date]
                temp_df.loc[index_using_pre_day_stock,pre_day_stock] = 1
                temp_df.loc[index_using_current_day_stock,current_day_stock] = 1
                position_df_stdrz = pd.DataFrame(temp_df.values / temp_df.sum(axis=1).values.reshape([temp_df.shape[0],1]),index=temp_df.index,columns=temp_df.columns)
                df_list.append(position_df_stdrz)
            final_df = pd.concat(df_list,axis=0)
            ans_dic.update({ticktime:final_df})
        return ans_dic


    def calculate_excess_ret(self):
        ret_df = self.ret_df.loc[str(self.start_date):str(self.end_date)].copy()
        topgroup_position = self.get_topgourp_position()
        topgroup_position_df_dic = self.transfer_topgroup_position_2_df(topgroup_position)
        excess_ret_dic = {}
        for ticktime in self.ticktime_list:
            long_ret = (topgroup_position_df_dic[ticktime] * ret_df).sum(axis=1)
            benchmark_ret = (self.benchmark_position_df_dic[ticktime] * ret_df).sum(axis=1)
            excess_ret = long_ret - benchmark_ret
            excess_ret_dic.update({ticktime:excess_ret})
        return excess_ret_dic

