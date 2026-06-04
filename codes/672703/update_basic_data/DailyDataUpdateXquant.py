import os
import sys
from copy import deepcopy
import scipy.io as spio
import numpy as np
import pandas as pd

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=pd.io.pytables.PerformanceWarning)

from DataIOFromXquant import DataIOFromXquant


class DailyDataUpdateXquant(object):
    """
    update all the daily date from xquant data source
    first download data, then clean and processs data and save 
    """
    def __init__(self,start_date='',end_date='',save_raw_flag=False,hf_flag=True,data_center_path='/data/group/800020/AlphaDataCenter/'):
        self.start_date = start_date
        self.end_date = end_date
        self.hf_flag = hf_flag
        self.data_center_path = data_center_path
        self.daily_store_path = self.data_center_path + 'Basic/daily/'
        self.minute_store_path = self.data_center_path + 'Basic/minute/'
        self.quarter_store_path = self.data_center_path + 'Basic/quarter/'

        self.xquant = DataIOFromXquant(start_date=self.start_date, end_date=self.end_date, save_flag=save_raw_flag)
        self.start_date = self.xquant.start_date
        self.end_date = self.xquant.end_date
        date_list = self.xquant.update_date
        if not isinstance(date_list, np.ndarray):
            date_list = np.array(date_list, dtype=np.int32)
        self.date_list = date_list

        self.universe = self.xquant.universe

        self.xquant.update_data()


    def save_data(self, date_list, stock_list, raw, factor_path):

        date_list = pd.to_datetime(date_list, format='%Y%m%d')

        store_factor_list = os.listdir(factor_path)
        store_factor_list = [f[:-4] for f in store_factor_list]

        invalid_data = {}
        for k in raw.keys():
            if not isinstance(raw[k], np.ndarray):
                raw[k] = np.array([raw[k]])
            raw[k] = raw[k].reshape(len(date_list), -1)
            raw_data = pd.DataFrame(index=date_list, columns=stock_list, data=raw[k])

            num_valid_entry = np.sum(pd.notnull(raw[k]), axis=1)
            invalid_date = date_list[num_valid_entry==0]

            if invalid_date.size > 0:
                invalid_data[k] = invalid_date
        
            if k not in store_factor_list:
                print('warning: ', k, ' not in database\n')
                raw_data.to_pickle(factor_path + k + '.pkl')
                continue

            store_data = pd.read_pickle(factor_path + k + '.pkl')
            store_date = store_data.index

            concat_date = np.setdiff1d(date_list, store_date)
            cover_date = np.intersect1d(date_list, store_date)
            # concat before cover in case of new stock
            if concat_date.size > 0:
                store_data = pd.concat([store_data, raw_data.loc[concat_date]])
        
            if cover_date.size > 0:
                col = np.intersect1d(store_data.columns, stock_list)
                store_data.loc[cover_date, col] = raw_data.loc[cover_date, col]

            #store_data.sort_index(axis=0, inplace=True)
            #store_data.sort_index(axis=1, inplace=True)
        
            store_data.to_pickle(factor_path + k + '.pkl')
        
        if invalid_data:
            for k,v in invalid_data.items():
                print('warning: invalid update for ', k, ' on following dates: ')
                print(v)
                print()


    def update_base_data(self):
        """"""
        print('update base data ......\n')
        raw_base = self.xquant.raw_base

        if not raw_base:
            print('Error, raw base data not available !')
        else:
        
            if 'volume' in raw_base.keys():
                raw_base['volume_by_share'] = raw_base['volume'] * 100
            
            if 'amt' in raw_base.keys():
                raw_base['amt_by_yuan'] = raw_base['amt'] * 1000

            ########### adjust factor ###########
            factor_adj_list = ['open', 'high', 'low', 'close', 'volume']
            factor_adj_update = list(set(factor_adj_list).intersection(raw_base.keys()))
            if len(factor_adj_update) > 0 and 'adjfactor' in raw_base.keys():
                for f in factor_adj_update:
                    if f == 'volume':
                        raw_base[f + '_adj'] = raw_base[f] * 100 / raw_base['adjfactor']
                    else:
                        raw_base[f + '_adj'] = raw_base[f] * raw_base['adjfactor']
                    

            self.save_data(self.date_list, self.universe, raw_base, self.daily_store_path)


            if 'volume' in raw_base.keys() and 'amt' in raw_base.keys():
                volume_by_share = pd.read_pickle(self.daily_store_path + 'volume_by_share.pkl')
                amt_by_yuan = pd.read_pickle(self.daily_store_path + 'amt_by_yuan.pkl')
                adjfactor = pd.read_pickle(self.daily_store_path + 'adjfactor.pkl')
                vwap = (amt_by_yuan / volume_by_share).fillna(method='ffill')
                vwap_adj = vwap * adjfactor
                vwap.to_pickle(self.daily_store_path + 'vwap.pkl')
                vwap_adj.to_pickle(self.daily_store_path + 'vwap_adj.pkl')

            print('base factor updated\n\n')



    def save_hf_daily_data(self, factor, df_update, factor_path):
    
        store_factor_list = os.listdir(factor_path)
        store_factor_list = [f[:-4] for f in store_factor_list]
        for indexs in df_update.index:
            num_valid_entry = np.sum(pd.notnull(df_update.loc[indexs]))
            if(num_valid_entry==0):
                print ('warning: invalid update for '+factor+' in'+str(indexs))

        if factor not in store_factor_list:
            print('warning: ', factor, ' not in database\n')
            df_update.to_pickle(factor_path + factor + '.pkl')
        else:
            store_data = pd.read_pickle(factor_path + factor + '.pkl')
            store_date = store_data.index
            update_date = df_update.index
            store_data=store_data.append(df_update)

            store_data = store_data.loc[~store_data.index.duplicated(keep='last')].sort_index()
            store_data.to_pickle(factor_path + factor + '.pkl')

    def wrangle_hf_price(self):
        """"""
        adjfactor = pd.read_pickle(self.daily_store_path+'adjfactor.pkl')

        # 10点价格，13点价格，14点价格
        hours_dict = {'ten_am':10,'one_pm':13,'two_pm':14,'vwap_ten_am':10,'vwap_one_pm':13,'vwap_two_pm':14}
        for name in hours_dict:
            hour = hours_dict[name]
            hour_price = {}
            for date in self.date_list:
                if(date<20140101):
                    continue
                date = str(date)
                df = pd.read_pickle(self.minute_store_path+'Close/'+date+'.pkl')
                if name[:4]=='vwap':
                    df0 = (pd.read_pickle(self.minute_store_path+'Amount/'+date+'.pkl')) / (pd.read_pickle(self.minute_store_path+'Volume/'+date+'.pkl'))
                    df0[pd.isnull(df0)] = df[pd.isnull(df0)]
                    df = df0
                hour_price[pd.Timestamp(date)] = df.loc[pd.Timestamp(date)+pd.Timedelta(hours=hour)]
            df_hour_price = pd.DataFrame(hour_price).T
            adjfactor_tmp = deepcopy(adjfactor)
            adjfactor_tmp = adjfactor_tmp.loc[df_hour_price.index]
            df_hour_adj = df_hour_price*adjfactor_tmp
            self.save_hf_daily_data(name, df_hour_price, self.daily_store_path)
            self.save_hf_daily_data(name+'_adj', df_hour_adj, self.daily_store_path)
   
    def update_hf_data(self):
        print('updating hf daily ...\n')

        self.wrangle_hf_price()

        print('hf daily updated \n')


    def wrangle_report_apply_date(self, date_list, stock_list, stm_issuingdate, quarter_date, report_trading_date):

        report_apply_date = np.zeros((len(date_list), len(stock_list))) * np.nan
        quarter_date_mx = np.repeat(np.array(quarter_date).reshape(len(quarter_date), 1), len(stock_list), axis=1)
        for i, dt in enumerate(date_list):
            report_apply_date[i] = pd.DataFrame(np.where(stm_issuingdate <= int(dt), \
            quarter_date_mx, np.nan)).fillna(method='ffill').iloc[-1].values
        return report_apply_date

    def wrangle_report_apply_date_old_unusable(self, date_list, stock_list, stm_issuingdate, quarter_date, report_trading_date):

        report_apply_date = np.zeros((len(date_list), len(stock_list))) * np.nan
        report_trading_date_mx = np.ones((len(quarter_date), 1)) * report_trading_date

        for k in range(len(stock_list)):

            new_index = np.repeat(np.nan, len(quarter_date))
            row_idx, col_idx = np.where(stm_issuingdate[:, [k]] <= report_trading_date_mx)

            # non-vectorized implementation
            for i in np.unique(row_idx):
                new_index[i] = report_trading_date[col_idx[row_idx==i][0]]

            # # vectorized implementation for new_index, slower than non-vectorized
            # stm_trading_position = pd.DataFrame(index=['row', 'col'], data=np.array(np.array([row_idx, col_idx]))).T
            # stm_trading_position = stm_trading_position.groupby(['row'], as_index=False).min().values.T
            # new_index[stm_trading_position[0, :]] = report_trading_date_mx[stm_trading_position[0, :], stm_trading_position[1, :]]
                    
            # when disclose (stm_issuingdate) later than at least the next quarter date, quarter date should equal the closest quarter date
            valid_idx = np.where(~np.isnan(new_index))[0]
            temp = pd.DataFrame(index=new_index[valid_idx], columns=['idx', 'quarter'], data=np.array([valid_idx, quarter_date[valid_idx]]).T)
            stm_too_late = temp['idx'][temp.sort_index()['quarter'] < quarter_date[valid_idx]].values
            new_index[stm_too_late] = np.nan

            valid_idx = ~np.isnan(new_index)
            all_disclose_trading_date = np.union1d(new_index[valid_idx], date_list)
            temp = pd.Series(index=all_disclose_trading_date)
            temp.loc[new_index[valid_idx]] = np.array(quarter_date[valid_idx], dtype=np.float64)
            report_apply_date[:, k] = temp.sort_index().fillna(method='ffill').loc[date_list].values

        return report_apply_date

    def wrangle_growth(self, date_list, stock_list, quarter_date, report_apply_date, growth_data):
    
        report_apply_date_df = pd.DataFrame(index=date_list, columns=stock_list, data=report_apply_date.reshape(len(date_list), -1))
        growth_data_df = pd.DataFrame(index=quarter_date, columns=stock_list, data=growth_data.reshape(len(quarter_date), -1))
        growth_array = np.zeros((len(date_list), len(stock_list))) * np.nan

        for i in range(len(stock_list)):
            report_apply_date_stk = report_apply_date_df[[stock_list[i]]]
            growth_stk = growth_data_df[[stock_list[i]]]
            growth_array[:, i] = report_apply_date_stk.merge(growth_stk, left_on=stock_list[i], right_index=True, how='left')[stock_list[i]+'_y'].values

        return growth_array

    def wrangle_up_down_limit(self, price, pre_close, is_valid_raw, limit=0.1):
        is_valid_hf = is_valid_raw.copy()
        is_valid_hf[pre_close*(1-limit) >= price] = 0
        is_valid_hf[pre_close*(1+limit) <= price] = 0
        return is_valid_hf

    def wrangle_valid(self, date_list, stock_list, list_date, delist_date, stpt, report_trading_date, daily_store_path):

        date_list_timestamp = pd.to_datetime(date_list, format='%Y%m%d')
    
        trade_status = pd.read_pickle(daily_store_path + 'trade_status.pkl')

        isValid = np.ones((len(date_list), len(stock_list)), dtype=int)

        # Proceed new listing stocks
        isValid[:, list_date > date_list[-1]] = 0
        report_trading_date_mx = report_trading_date.reshape(1,-1).T * np.ones(len(stock_list))
        date_list_mx = date_list.reshape(1, -1).T * np.ones(len(stock_list))

        if np.sum(list_date <= date_list[-1]) > 0:
        
            list_position = np.where(report_trading_date_mx >= list_date)
            list_position = pd.DataFrame(index=['row', 'col'], data=np.array(list_position)).T
            list_position = list_position.groupby(['col'], as_index=False).min().values.T
            stk_less_120 = list_position[1, :] + 120 >= len(report_trading_date)
            list_position_120 = deepcopy(list_position)
            list_position_120[1, stk_less_120] = -1
            list_position_120[1, ~stk_less_120] += 120

            # vectorized implementation
            list_date_120 = report_trading_date_mx[list_position_120[1, :], list_position_120[0, :]]
            isValid_list = isValid[:, list_position_120[0, :]]
            isValid_list[date_list_mx[:, list_position_120[0, :]] <= list_date_120] = 0
            isValid[:, list_position_120[0, :]] = isValid_list

            # # non_vectorized implementation
            # for c in range(list_position_120.shape[1]):
            #     list_date_120 = report_trading_date[list_position_120[1, c]]
            #     stk = list_position_120[0, c]
            #     isValid[date_list <= list_date_120, stk] = 0

        num_trade_days = (trade_status.astype(str) != 'nan').rolling(window=60, min_periods=1).sum()
        min_num = 60 * np.ones(trade_status.shape)
        min_num[:59] = np.linspace(1, 59, 59).astype(int).reshape(1,-1).T * np.ones(len(trade_status.columns))
        min_num = pd.DataFrame(index=trade_status.index, columns=trade_status.columns, data=min_num)
        isValid[num_trade_days.loc[date_list_timestamp] < min_num.loc[date_list_timestamp]] = 0

        # Proceed delisting stocks
        isValid[date_list_mx >= delist_date] = 0

        # bct_data
        isValid_bct = deepcopy(isValid)

        isValid_excl_newstock = deepcopy(isValid)
        isValid_excl_newstock_df = pd.DataFrame(index=date_list_timestamp, columns=stock_list, data=isValid_excl_newstock)
   
        # Proceed suspension stocks
        isValid_bct[np.logical_or(trade_status.loc[date_list_timestamp]=='停牌', trade_status.astype(str).loc[date_list_timestamp]=='nan')] = 0
        isValid_bct_pd = pd.DataFrame(index=date_list_timestamp, columns=stock_list, data=isValid_bct)
        isValid_raw_incl_st = deepcopy(isValid_bct_pd)

        num_trade_days = (np.logical_and(trade_status!='停牌', trade_status.astype(str)!='nan')).rolling(window=20,min_periods=1).sum()
        min_num = 20 * np.ones(trade_status.shape)
        min_num[:19] = np.linspace(1, 19, 19).astype(int).reshape(1,-1).T * np.ones(len(trade_status.columns))
        min_num = pd.DataFrame(index=trade_status.index, columns=trade_status.columns, data=min_num)
        isValid[num_trade_days.loc[date_list_timestamp] < min_num.loc[date_list_timestamp]] = 0
  
        isValid_include_st = deepcopy(isValid)
        isValid_include_st_df = pd.DataFrame(index=date_list_timestamp, columns=stock_list, data=isValid_include_st)

        # Proceed ST stocks
        stpt = stpt.reshape(len(date_list), len(stock_list))
        isValid[stpt > 0] = 0
        isValid_bct[stpt > 0] = 0

        isValid_pd = pd.DataFrame(index=date_list_timestamp, columns=stock_list, data=isValid)
        isValid_bct_pd = pd.DataFrame(index=date_list_timestamp, columns=stock_list, data=isValid_bct)

        isValid_not_open_updown_limit = deepcopy(isValid_pd)
        is_valid_raw = deepcopy(isValid_bct_pd)
    
        pre_close = pd.read_pickle(daily_store_path + 'pre_close.pkl').loc[date_list_timestamp]
        open_ = pd.read_pickle(daily_store_path + 'open.pkl').loc[date_list_timestamp]
        close = pd.read_pickle(daily_store_path + 'close.pkl').loc[date_list_timestamp]
        vwap = pd.read_pickle(daily_store_path + 'vwap.pkl').loc[date_list_timestamp]
        if self.hf_flag:
            ten_am = pd.read_pickle(daily_store_path + 'ten_am.pkl').loc[date_list_timestamp]
            one_pm = pd.read_pickle(daily_store_path + 'one_pm.pkl').loc[date_list_timestamp]
            two_pm = pd.read_pickle(daily_store_path + 'two_pm.pkl').loc[date_list_timestamp]
        ST = (isValid_raw_incl_st - is_valid_raw).replace(0., np.nan)

        isValid_pd = self.wrangle_up_down_limit(close, pre_close, isValid_not_open_updown_limit, 0.098)
        is_valid_open = self.wrangle_up_down_limit(open_, pre_close, isValid_not_open_updown_limit, 0.098)
        isValid_8pct_maxupdown = self.wrangle_up_down_limit(close, pre_close, isValid_not_open_updown_limit, 0.08)
        is_valid_open_8pct_maxupdown = self.wrangle_up_down_limit(open_, pre_close, isValid_not_open_updown_limit, 0.08)
        
        if self.hf_flag:
            is_valid_ten_am = self.wrangle_up_down_limit(ten_am, pre_close, isValid_not_open_updown_limit, 0.098)
            is_valid_one_pm = self.wrangle_up_down_limit(one_pm, pre_close, isValid_not_open_updown_limit, 0.098)
            is_valid_two_pm = self.wrangle_up_down_limit(two_pm, pre_close, isValid_not_open_updown_limit, 0.098)
            is_valid_ten_am_8pct_maxupdown = self.wrangle_up_down_limit(ten_am, pre_close, isValid_not_open_updown_limit, 0.08)
            is_valid_one_pm_8pct_maxupdown = self.wrangle_up_down_limit(one_pm, pre_close, isValid_not_open_updown_limit, 0.08)
            is_valid_two_pm_8pct_maxupdown = self.wrangle_up_down_limit(two_pm, pre_close, isValid_not_open_updown_limit, 0.08)
    
        # 跌停
        isValid_and_trigger_lower_price_limit = deepcopy(isValid_raw_incl_st)
        isValid_and_trigger_lower_price_limit[pre_close*(1-0.098) >= close] = 0
        isValid_and_trigger_lower_price_limit[ST * pre_close*(1-0.048) >= ST * close] = 0

        # 涨停
        isValid_and_trigger_upper_price_limit = deepcopy(isValid_raw_incl_st)
        isValid_and_trigger_upper_price_limit[pre_close*(1+0.098) <= close] = 0
        isValid_and_trigger_upper_price_limit[ST * pre_close*(1+0.048) <= ST * close] = 0

        # 均价 > 8 个点
        isValid_and_trigger_upper_avg_price = deepcopy(isValid_raw_incl_st)
        isValid_and_trigger_upper_avg_price[vwap >= pre_close*(1+0.08)] = 0
        isValid_and_trigger_upper_avg_price[ST * vwap >= ST * pre_close*(1+0.04)] = 0
    
        # 均价 < 8 个点
        isValid_and_trigger_lower_avg_price = deepcopy(isValid_raw_incl_st)
        isValid_and_trigger_lower_avg_price[vwap <= pre_close*(1-0.08)] = 0
        isValid_and_trigger_lower_avg_price[ST * vwap <= ST * pre_close*(1-0.04)] = 0
    
        # return
        raw_valid = {}
        raw_valid['is_valid'] = isValid_pd.values
        raw_valid['is_valid_open'] = is_valid_open.values
        raw_valid['is_valid_8pct_maxupdown'] = isValid_8pct_maxupdown.values
        raw_valid['is_valid_open_8pct_maxupdown'] = is_valid_open_8pct_maxupdown.values
        raw_valid['isvalid_and_not_open_updown_limit'] = isValid_not_open_updown_limit.values
        raw_valid['isValid_include_st'] = isValid_include_st_df.values
        raw_valid['isValid_excl_newstock'] = isValid_excl_newstock_df.values
        raw_valid['is_valid_raw'] = is_valid_raw.values
        raw_valid['isValid_and_trigger_lower_price_limit'] = isValid_and_trigger_lower_price_limit.values
        raw_valid['isValid_and_trigger_upper_price_limit'] = isValid_and_trigger_upper_price_limit.values
        raw_valid['isValid_and_trigger_upper_avg_price'] = isValid_and_trigger_upper_avg_price.values
        raw_valid['isValid_and_trigger_lower_avg_price'] = isValid_and_trigger_lower_avg_price.values
        raw_valid['isValid_raw_incl_st'] = isValid_raw_incl_st.values
        if self.hf_flag:
            raw_valid['is_valid_ten_am'] = is_valid_ten_am.values
            raw_valid['is_valid_one_pm'] = is_valid_one_pm.values
            raw_valid['is_valid_two_pm'] = is_valid_two_pm.values
            raw_valid['is_valid_ten_am_8pct_maxupdown'] = is_valid_ten_am_8pct_maxupdown.values
            raw_valid['is_valid_one_pm_8pct_maxupdown'] = is_valid_one_pm_8pct_maxupdown.values
            raw_valid['is_valid_two_pm_8pct_maxupdown'] = is_valid_two_pm_8pct_maxupdown.values
        return raw_valid


    def compute_mkt_smb_hml(self, date_list, stock_list, mkt_cap_ard, bps, close, is_valid, daily_store_path):

        date_list_timestamp = pd.to_datetime(date_list, format='%Y%m%d')

        is_valid = pd.DataFrame(index=date_list_timestamp, columns=stock_list, data=is_valid.reshape(len(date_list), -1))

        mkt_cap_rank = pd.DataFrame(index=date_list_timestamp, columns=stock_list, data=mkt_cap_ard.reshape(len(date_list), -1))
        book_to_price = pd.DataFrame(index=date_list_timestamp, columns=stock_list, data=(bps/close).reshape(len(date_list), -1))
        ret = self.compute_closeadj_return(date_list_timestamp, daily_store_path)

        mkt_cap_rank = mkt_cap_rank[is_valid==1]
        book_to_price = book_to_price[is_valid==1]
        ret = ret[is_valid == 1]

        ff3 = pd.DataFrame(index=date_list_timestamp, columns=['mkt', 'smb', 'hml'])
        for date in date_list_timestamp:

            mkt_cap_rank_today  = mkt_cap_rank.loc[date].sort_values().dropna()
            book_to_price_today = book_to_price.loc[date].sort_values().dropna()

            small_stocks   = mkt_cap_rank_today[:int(len(mkt_cap_rank_today)/3)].index
            large_stocks   = mkt_cap_rank_today[-int(len(mkt_cap_rank_today)/3):].index
            low_bp_stocks  = book_to_price_today[:int(len(book_to_price_today)/3)].index
            high_bp_stocks = book_to_price_today[-int(len(book_to_price_today)/3):].index

            small_stocks_weight   = mkt_cap_rank_today[small_stocks] / mkt_cap_rank_today[small_stocks].sum()
            large_stocks_weight   = mkt_cap_rank_today[large_stocks] / mkt_cap_rank_today[large_stocks].sum()
            low_bp_stocks_weight  = mkt_cap_rank_today[low_bp_stocks] / mkt_cap_rank_today[low_bp_stocks].sum()
            high_bp_stocks_weight = mkt_cap_rank_today[high_bp_stocks] / mkt_cap_rank_today[high_bp_stocks].sum()

            small_ret   = (small_stocks_weight * ret.loc[date, small_stocks]).sum()
            large_ret   = (large_stocks_weight * ret.loc[date, large_stocks]).sum()
            low_bp_ret  = (low_bp_stocks_weight * ret.loc[date, low_bp_stocks]).sum()
            high_bp_ret = (high_bp_stocks_weight * ret.loc[date, high_bp_stocks]).sum()

            mkt_weight = mkt_cap_rank_today / mkt_cap_rank_today.sum()

            mkt = (mkt_weight * ret.loc[date, mkt_cap_rank_today.index]).sum()
            smb = small_ret - large_ret
            hml = high_bp_ret - low_bp_ret

            ff3.loc[date] = [mkt, smb, hml]

        return ff3

    def update_fundamental_data(self):
        """"""
        print('updating fundamental factor...\n')

        raw_fundamental = self.xquant.raw_fundamental

        if not raw_fundamental:
            print('attention: raw fundamental data doesnot exist, no fundamental factor to update \n')
        else:

            ########### report_apply_date, growth ###########
            if 'stm_issuingdate' in raw_fundamental.keys():
                stm_issuingdate = raw_fundamental['stm_issuingdate']
                quarter_date = raw_fundamental['quarter_date']
                report_trading_date = raw_fundamental['report_trading_date']
                raw_fundamental['report_apply_date'] = self.wrangle_report_apply_date(self.date_list, 
                                                                                      self.universe, 
                                                                                      stm_issuingdate, 
                                                                                      quarter_date, 
                                                                                      report_trading_date)

                #growth_factors = self.xquant.fundamental_dict['growth']
                #growth_factors = set(growth_factors).intersection(raw_fundamental.keys())
                #for g in growth_factors:
                #    raw_fundamental[g] = self.wrangle_growth(self.date_list, 
                #                                             self.universe, 
                #                                             quarter_date, 
                #                                             raw_fundamental['report_apply_date'], 
                #                                             raw_fundamental[g])

        
            ########### valid ###########
            valid_factor = ['Listing_date', 'Delisting_date', 'STPT', 'report_trading_date']
            valid_factor_update = set(valid_factor).intersection(raw_fundamental.keys())

            self.valid_factor_update = valid_factor_update   # this variable is added for use in index and industry update

            if len(valid_factor_update) < 4:
                print('attention: ', valid_factor_update, ' exists, missing ', set(valid_factor).difference(valid_factor_update), ' for valid \n')
            else:
                raw_valid = self.wrangle_valid(self.date_list, self.universe, raw_fundamental['Listing_date'], raw_fundamental['Delisting_date'], 
                                      raw_fundamental['STPT'], raw_fundamental['report_trading_date'], self.daily_store_path)

                self.save_data(self.date_list, self.universe, raw_valid, self.daily_store_path)

                self.raw_valid = raw_valid   ### this variable is added for use in index and industry update

            ########### quarter #########
            raw_fundamental_quarter={ key:raw_fundamental[key] for key in raw_fundamental.keys() if key.endswith('_quarter')}
            if 'quarter_date' in raw_fundamental.keys():
                self.save_data(raw_fundamental['quarter_date'], self.universe, raw_fundamental_quarter, self.quarter_store_path)
        
            ########### delete factors not to be saved ###########
            delete_factor = ['stm_issuingdate', 'quarter_date'] + valid_factor + list(raw_fundamental_quarter.keys())
            delete_factor = set(delete_factor).intersection(raw_fundamental.keys())
            for f in delete_factor:
                del raw_fundamental[f]


            ########### bps, eps_ttm, mkt_smb_hml ###########
            if 'total_shares' in self.xquant.raw_base.keys():

                if 'tot_shrhldr_eqy_excl_min_int' in raw_fundamental.keys() and 'other_equity_tools' in raw_fundamental.keys():
                    raw_fundamental['bps'] = (raw_fundamental['tot_shrhldr_eqy_excl_min_int'] - 
                        np.nan_to_num(raw_fundamental['other_equity_tools'])) / self.xquant.raw_base['total_shares'] / 10000


                    if len(valid_factor_update) >= 4 and 'isvalid_and_not_open_updown_limit' in raw_valid.keys() and \
                       'mkt_cap_ard' in self.xquant.raw_base.keys() and 'close' in self.xquant.raw_base.keys():

                        mkt_smb_hml = self.compute_mkt_smb_hml(self.date_list, 
                                                               self.universe, 
                                                               self.xquant.raw_base['mkt_cap_ard'], 
                                                               raw_fundamental['bps'], 
                                                               self.xquant.raw_base['close'], 
                                                               raw_valid['isvalid_and_not_open_updown_limit'], 
                                                               self.daily_store_path)

                        raw_mkt_smb_hml = {}
                        raw_mkt_smb_hml['mkt_smb_hml'] = mkt_smb_hml.values

                        self.save_data(self.date_list, mkt_smb_hml.columns, raw_mkt_smb_hml, self.daily_store_path)

            
                if 'net_profit_excl_min_int_inc_ttm' in raw_fundamental.keys():
                    raw_fundamental['eps_ttm'] = raw_fundamental['net_profit_excl_min_int_inc_ttm'] / self.xquant.raw_base['total_shares'] / 10000

        
            self.save_data(self.date_list, self.universe, raw_fundamental, self.daily_store_path)

            print('fundamental factor updated \n')


    def compute_closeadj_return(self, date_list_timestamp, daily_store_path):
        close_all = pd.read_pickle(daily_store_path + 'close.pkl')
        adjfactor_all = pd.read_pickle(daily_store_path + 'adjfactor.pkl')
        close_adj_all = adjfactor_all * close_all
        ret = (close_adj_all.pct_change(1)).loc[date_list_timestamp]
        return ret

    def compute_sw_industry_re(self, date_list, stock_list, industry_code, free_float_cap, is_valid, daily_store_path):

        date_list_timestamp = pd.to_datetime(date_list, format='%Y%m%d')

        industry_code = pd.DataFrame(index=date_list_timestamp, columns=stock_list, data=industry_code.reshape(len(date_list), -1))
        free_float_cap = pd.DataFrame(index=date_list_timestamp, columns=stock_list, data=free_float_cap.reshape(len(date_list), -1))
        is_valid = pd.DataFrame(index=date_list_timestamp, columns=stock_list, data=is_valid.reshape(len(date_list), -1))
        ret = self.compute_closeadj_return(date_list_timestamp, daily_store_path)

        industry_uni = np.unique(industry_code)
        industry_uni = industry_uni[industry_uni>0].astype(int)
        sw_industry_re = pd.DataFrame(index=date_list_timestamp, columns=industry_uni.astype(str))
        for indus in industry_uni:
            a = (free_float_cap * ret)[np.logical_and(industry_code == indus, is_valid == 1)].sum(axis=1, skipna=True)
            b = free_float_cap[industry_code == indus].sum(axis=1, skipna=True)
            sw_industry_re[str(indus)] = a / b
    
        return sw_industry_re

    def wrangle_index_weight(self, date_list, stock_list, index_data):

        weight_df = pd.DataFrame(index=date_list, columns=stock_list, data=0.)
        
#        if len(date_list) == 1:
#            index_data = np.array(index_data)
            
        for i in range(len(date_list)):

            missing_stk = list(set(index_data[i][:, 0]).difference(stock_list))
            common_stk = list(set(index_data[i][:, 0]).intersection(stock_list))
        
            temp_index = pd.Series(index=index_data[i][:, 0], data=index_data[i][:, 2], dtype=np.float64)
            weight_df.loc[date_list[i], common_stk] = temp_index.loc[common_stk]

            if len(missing_stk) > 0:
                print('warning: index, ', index_data[0].shape[0], ', missing following constituent stock data on ', date_list[i], '\n', missing_stk)

        return weight_df.values


    def update_index_industry_data(self):
        """"""
        print('update index industry data ...... \n')
        raw_index_industry = self.xquant.raw_index_industry

        if not raw_index_industry:
            print('attention: raw index industry not exist\n')
        else:
            ########### index close ###########
            for k,v in raw_index_industry.items():
                if 'close' in k or 'open' in k:
                    raw_index = {}
                    raw_index[k] = v
                    self.save_data(self.date_list, [k], raw_index, self.daily_store_path)

        
            ########### index weight (data), index code and corresponding name ###########
            raw_index_industry_ = {}
            index_data_list = ['HS300_', 'ZZ500_', 'ZZ800_', 'SZ50_']
            for k in index_data_list:
                if k+'index' in raw_index_industry.keys():
                    raw_index_industry_[k+'data'] = self.wrangle_index_weight(self.date_list, self.universe, raw_index_industry[k+'index'])
            
            if 'sw1_industry_code' in raw_index_industry.keys() or 'sw1_industry_name' in raw_index_industry.keys():
                raw_index_industry_['sw1_industry_code'] = deepcopy(raw_index_industry['sw1_industry_code'])
                raw_index_industry_['sw1_industry_code'][raw_index_industry_['sw1_industry_code']=='nan'] = np.nan
                raw_index_industry_['sw1_industry_name'] = deepcopy(raw_index_industry['sw1_industry_name'])
                raw_index_industry_['sw1_industry_name'][raw_index_industry_['sw1_industry_name']=='nan'] = np.nan
                raw_index_industry_['sw2_industry_code'] = deepcopy(raw_index_industry['sw2_industry_code'])
                raw_index_industry_['sw2_industry_code'][raw_index_industry_['sw2_industry_code']=='nan'] = np.nan
                raw_index_industry_['sw2_industry_name'] = deepcopy(raw_index_industry['sw2_industry_name'])
                raw_index_industry_['sw2_industry_name'][raw_index_industry_['sw2_industry_name']=='nan'] = np.nan
                raw_index_industry_['industry_code_all'] = deepcopy(raw_index_industry['sw1_industry_code'].astype(np.float64))
            
                bank_fin_position = np.logical_or(raw_index_industry_['sw1_industry_name']=='银行', raw_index_industry_['sw1_industry_name']=='非银金融')
                raw_index_industry_['swX_industry_name'] = deepcopy(raw_index_industry_['sw1_industry_name'])
                raw_index_industry_['swX_industry_name'][bank_fin_position] = raw_index_industry_['sw2_industry_name'][bank_fin_position]
                raw_index_industry_['swX_industry_code'] = deepcopy(raw_index_industry_['sw1_industry_code'])
                raw_index_industry_['swX_industry_code'][bank_fin_position] = raw_index_industry_['sw2_industry_code'][bank_fin_position]
            
            if 'citics1_industry_code' in raw_index_industry.keys() or 'citics2_industry_code' in raw_index_industry.keys() or 'citics1_industry_name' in raw_index_industry.keys() or 'citics2_industry_name' in raw_index_industry.keys():
                raw_index_industry_['citics1_industry_code'] = raw_index_industry['citics1_industry_code']
                raw_index_industry_['citics1_industry_code'][raw_index_industry_['citics1_industry_code']=='nan'] = np.nan
                raw_index_industry_['citics2_industry_code'] = raw_index_industry['citics2_industry_code']
                raw_index_industry_['citics2_industry_code'][raw_index_industry_['citics2_industry_code']=='nan'] = np.nan
                raw_index_industry_['citics1_industry_name'] = raw_index_industry['citics1_industry_name']
                raw_index_industry_['citics1_industry_name'][raw_index_industry_['citics1_industry_name']=='nan'] = np.nan
                raw_index_industry_['citics2_industry_name'] = raw_index_industry['citics2_industry_name']
                raw_index_industry_['citics2_industry_name'][raw_index_industry_['citics2_industry_name']=='nan'] = np.nan

                bank_fin_position = np.logical_or(raw_index_industry_['citics1_industry_name']=='银行', raw_index_industry_['citics1_industry_name']=='非银行金融')
                raw_index_industry_['citicsX_industry_name'] = deepcopy(raw_index_industry_['citics1_industry_name'])
                raw_index_industry_['citicsX_industry_name'][bank_fin_position] = raw_index_industry_['citics2_industry_name'][bank_fin_position]
                raw_index_industry_['citicsX_industry_code'] = deepcopy(raw_index_industry_['citics1_industry_code'])
                raw_index_industry_['citicsX_industry_code'][bank_fin_position] = raw_index_industry_['citics2_industry_code'][bank_fin_position]
            
                ########### sw_industry_re ###########
                if 'free_float_cap' in self.xquant.raw_base.keys() and  len(self.valid_factor_update) >= 4 and 'is_valid' in self.raw_valid.keys():

                    sw_industry_re = self.compute_sw_industry_re(self.date_list, 
                                                                 self.universe, 
                                                                 raw_index_industry['sw1_industry_code'].astype(np.float64), 
                                                                 self.xquant.raw_base['free_float_cap'], 
                                                                 self.raw_valid['is_valid'], 
                                                                 self.daily_store_path)

                    raw_sw_industry_re = {}
                    raw_sw_industry_re['sw_industry_re'] = sw_industry_re.values

                    self.save_data(self.date_list, sw_industry_re.columns, raw_sw_industry_re, self.daily_store_path)

            self.save_data(self.date_list, self.universe, raw_index_industry_, self.daily_store_path)

            print('index industry data updated \n')

    
    def update_data(self):
        self.update_base_data()
        if self.hf_flag:
            self.update_hf_data()
        self.update_fundamental_data()
        self.update_index_industry_data()


if __name__=='__main__':

     #start_date = '20190101'
     #end_date = '20190517'
     #date_list = FactorData().tradingday(start_date, end_date)

     #today = datetime.datetime.today().strftime('%Y%m%d')
     #start_date = '20191119' #today
     #end_date = '20191119' #today
     #instance = DailyDataUpdateXquant(start_date=start_date,end_date=end_date)
     #instance.update_data()  #'20190101','20180101','20170101','20160101','20191209','20181231','20171231','20161231',

     start_date_list = ['20150101','20140101', '20130101','20120101','20110101','20100101'] 
     end_date_list = ['20151231','20141231','20131231','20121231','20111231','20101231']  
     hf_flag = False
     for start_date, end_date in zip(start_date_list,end_date_list):
         print(start_date,end_date)
         if start_date < '20150101': hf_flag = False
         instance = DailyDataUpdateXquant(start_date=start_date,end_date=end_date,hf_flag=hf_flag)
         instance.update_data()