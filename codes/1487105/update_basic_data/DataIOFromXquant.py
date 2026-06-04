import os
import sys
import datetime
import time
from copy import deepcopy
import scipy.io as spio
import numpy as np
import pandas as pd
from xquant.factordata import FactorData


class DataIOFromXquant(object):
    """
    update data from xquant data source
    """

    def __init__(self, start_date='', 
                       end_date='', 
                       update_type=0, 
                       universe_path='',
                       save_flag=False, 
                       save_path=''):

        self.start_date = start_date
        self.end_date = end_date

        self.data_api = FactorData()

        self.update_date = self.__get_tradingdays(self.start_date, self.end_date)
        self.trading_date = self.__get_tradingdays('20111102', self.end_date)
        assert len(self.update_date) != 0, 'error: no trading day between given start date and end date'
        self.start_date = self.update_date[0]
        self.end_date = self.update_date[-1]

        self.update_type = update_type
        assert self.update_type in [0, 1], 'update_type should be in [0, 1]'

        self.universe_path = universe_path
        stock_list = self.__load_raw(self.universe_path + 'universe.mat')
        self.universe = list(stock_list['universe'])

        self.save_flag = save_flag
        self.save_path = save_path
        if self.save_flag:
            new_save_path = self.save_path+'{0}_{1}/'.format(self.start_date,self.end_date)
            if not os.path.exists(new_save_path): os.mkdir(new_save_path)
            self.save_path = new_save_path

        self.base_list = ['adjfactor', 'amt', 'close', 'dealnum', 'float_a_shares', 'high', 'low', 'mkt_cap_ard',
                          'open', 'pe_ttm', 'pre_close', 'share_totala', 'swing', 'total_shares', 'trade_status',
                          'turn', 'volume', 's_val_pb_new', 's_price_div_dps', 'ps_ttm', 'pcf_ocf_ttm', 'dyr_12',
                          'free_float_shares']

        self.fundamental_dict = {
                'hdf_publishday': [
                    'tot_shrhldr_eqy_excl_min_int',
                    'other_equity_tools',
                    'net_profit_excl_min_int_inc',
                    'net_profit_incl_min_int_inc',
                    'tot_liab',
                    'tot_assets',
                    'longdebtodebt',
                    'tot_cur_assets',
                    'monetary_cap',
                    'tot_cur_liab',
                    'less_impair_loss_assets',
                    'deductedprofittoprofit',
                    'adminexpensetogr_ttm',
                    'ocftooperateincome_ttm',
                    'ebit',
                    'ebitda',
                    'tot_shrhldr_eqy_incl_min_int',
                    'fcffps',
                    'finaexpensetogr_ttm',
                    'fix_assets',
                    'gctogr_ttm',
                    'tot_oper_cost',
                    'less_oper_cost',
                    'oper_exp',
                    'invturn',
                    'tot_non_cur_liab',
                    'oper_rev',
                    'grossprofitmargin_ttm',
                    'nptocostexpense',
                    'inc_tax',
                    'optogr_ttm',
                    'operateexpensetogr_ttm',
                    'less_selling_dist_exp',
                    'less_gerl_admin_exp',
                    'less_fin_exp',
                    'expensetosales',
                    'expensetosales_ttm',
                    'oper_profit',
                    'net_cash_flows_oper_act',
                    'plus_non_oper_rev',
                    'cash_pay_beh_empl',
                    'adv_from_cust',
                    'acct_rcv',
                    'inventories',
                    'arturn',
                    'prepay',
                    'net_cash_flows_fnc_act',
                    'eps_basic',
                    'roic_ttm',
                    'optoebt',
                    'profittogr_ttm',
                    'roe_ttm',
                    'roe2_ttm',
                    'netprofitmargin_ttm',
                    'operateincometoebt_ttm',
                    'yoyeps_basic',
                    'yoyocf',
                    'yoynetprofit',
                    'yoyroe',
                    'yoy_equity',
                    'yoydebt',
                    'yoy_assets',
                    'ocftoor_ttm',
                    'icftocf',
                    'debttoassets',
                    'longdebttolongcaptial',
                    'assetstoequity',
                    'catoassets',
                    'equitytototalcapital',
                    'currentdebttodebt',
                    'current',
                    'quick',
                    'cashtocurrentdebt',
                    'debttoequity',
                    'ebitdatodebt',
                    'ocftoshortdebt',
                    'ebittointerest',
                    'longdebttoworkingcapital',
                    'tltoebitda',
                    'turndays',
                    'invturndays',
                    'arturndays',
                    'apturndays',
                    'caturn',
                    'operatecapitalturn',
                    'faturn',
                    'assetsturn'
                ],

                'hdf_ttm': [
                    'net_profit_excl_min_int_inc',
                    'net_profit_incl_min_int_inc',
                    'net_cash_flows_oper_act'
                ],

                'hfactor_ttm': [
                    'ocfps_ttm',
                    'orps_ttm',
                    'cfps_ttm',
                    'oper_rev_ttm',
                    'ev1',
                    'pcf_ncf_ttm',
                    'net_assets_today'
                ],

                'report_date': [
                    'quarter_date',
                    'report_trading_date',
                    'stm_issuingdate',
                ],

                'hfactor_quarter': [
                    'acct_payable',
                    'acct_rcv',
                    'arturn',
                    'assetsturn',
                    'cap_rsrv',
                    'cash_pay_beh_empl',
                    'ebit',
                    'ebitda',
                    'equitytodebt',
                    'fcffps',
                    'free_cash_flow',
                    'goodwill',
                    'intang_assets',
                    'inventories',
                    'invturn',
                    'less_impair_loss_assets',
                    'less_oper_cost',
                    'lt_payroll_payable',
                    'monetary_cap',
                    'net_cash_flows_fnc_act',
                    'net_cash_flows_inv_act',
                    'net_cash_flows_oper_act',
                    'net_profit_after_ded_nr_lp',
                    'net_profit_excl_min_int_inc',
                    'netprofitmargin',
                    'ocftoor_ttm',
                    'oper_profit',
                    'oper_rev',
                    'plus_non_oper_rev',
                    'profittogr',
                    'profittogr_ttm',
                    'roe_ttm',
                    'roic',
                    'roic_ttm',
                    's_fa_eps_basic',
                    'tot_assets',
                    'tot_bal_netcash_inc',
                    'tot_compreh_inc_parent_comp',
                    'tot_cur_assets',
                    'tot_cur_liab',
                    'tot_liab',
                    'tot_non_cur_assets',
                    'tot_oper_cost',
                    'tot_oper_rev',
                    'tot_shrhldr_eqy_excl_min_int'
                ],

                'valid': [
                    'listing_date',
                    'delisting_date',
                    'STPT'
                ],

                'growth': [
                    'growth_cagr_tr_3y',
                    'growth_cagr_tr_5y',
                    'growth_netprofit_3y',
                    'growth_netprofit_5y'
                ]
            }

        ###########################################################################
        self.index_industry_dict = {
                'index_code': [
                    '000001.SH',    # SZZZ
                    '000016.SH',    # SZ50
                    '000300.SH',    # HS300
                    '000905.SH',    # ZZ500
                    '000906.SH',    # ZZ800
                    '000985.CSI',    # ZZQZ
                    '000852.SH',    # ZZ1000
                    '399001.SZ',    # SZCZ
                    '399005.SZ',    # ZXBZ
                    '399006.SZ'     # CYBZ
                ],

                'index_factor': ['close', 'open'],
                'index_factor_map_wind': ['S_DQ_CLOSE', 'S_DQ_OPEN'],

                'index_data': ['HS300', 'ZZ500',  'SZ50'], # 'ZZ800',

                'industry': [            
                    'sw1',
                    'sw2',
                    'citics1',
                    'citics2']
            }


        if self.update_type != 0:
            self.base_list, self.fundamental_dict, self.index_industry_dict = [], {}, {}


        self.raw_base = {}               ### dict to save all data
        self.raw_fundamental = {}
        self.raw_index_industry = {}  

    def __get_tradingdays(self, start_date, end_date):
        if not isinstance(start_date, str):
            start_date = str(start_date)
        if not isinstance(end_date, str):
            end_date = str(end_date)
        trade_dates = self.data_api.tradingday(start_date, end_date)
        if trade_dates is None:
            return []
        else:
            trade_dates = sorted(trade_dates)
        return trade_dates

    def __load_raw(self, raw_file_path):
        raw = spio.loadmat(raw_file_path, squeeze_me=True)
        for d in ['__header__', '__version__', '__globals__']:
            del raw[d]
        return raw

    def download_raw_base(self):
        """"""
        print('start query raw base data from xquant ......')

        res = self.data_api.get_factor_value('Basic_factor', stock=self.universe, mddate=self.update_date,
                                             factor_names=self.base_list)
        res['free_float_cap'] = res['free_float_shares'] * res['close'] * 10000

        for i in res.columns:
            self.raw_base[i] = res[i].unstack().reindex(columns=self.universe).values
        del self.raw_base['free_float_shares']

        if not self.raw_base:
            print('attention: raw base data is empty, no data downloaded \n')        

        print('download raw base data done !')

        if self.save_flag:
            raw_base_path = self.save_path + '/raw_base.mat'
            spio.savemat(raw_base_path, self.raw_base)
            print(' raw base data has been saved !')

    def __ttm_calculator(self, field, quarter_list):
        data_ttm = np.nan * np.ones((len(quarter_list), len(self.universe)))
        for i, item in enumerate(quarter_list):
            current_year = int(item[:4])
            year = np.repeat([[current_year - 1, current_year]], 4, axis=0).T
            quarter = np.repeat([[331, 630, 930, 1231]], 2, axis=0)
            quarter = 10000 * year + quarter
            quarter = quarter[quarter <= int(item)]
            quarter = [str(i) for i in quarter]
            last_annual = [i for i in quarter if int(i) % 10000 == 1231][0]
            data = self.data_api.get_factor_value('Basic_factor', self.universe, quarter, [field])[field]
            data = data.unstack().reindex(index=quarter, columns=self.universe)
            data_ttm[i] = (data.iloc[-1] + data.loc[last_annual] - data.iloc[-5]).values
        return data_ttm

    def __growth_calculator(self, field, quarter_list, lb):
        growth = np.nan * np.ones((len(quarter_list), len(self.universe)))
        if field == 'growth_netprofit':
            field = 'net_profit_excl_min_int_inc'
        elif field == 'growth_cagr_tr':
            field = 'tot_oper_rev'
        for i, item in enumerate(quarter_list):
            quarter = [str(int(item) - lb * 10000), item]
            data = self.data_api.get_factor_value('Basic_factor', self.universe, quarter, [field])[field]
            data = data.unstack().reindex(index=quarter, columns=self.universe)
            if field == 'net_profit_excl_min_int_inc':
                growth[i] = ((data.iloc[1] - data.iloc[0]) / data.iloc[0].abs()).values
            elif field == 'tot_oper_rev':
                growth[i] = ((data.iloc[1] / data.iloc[0].abs()) ** (1. / lb) - 1).values
        return growth

    def download_raw_fundamental(self):
        """"""
        print('start query fundamental base data from xquant ......')

        hdf_publishday_list = self.fundamental_dict['hdf_publishday']
        hdf_ttm_list = self.fundamental_dict['hdf_ttm']
        hfactor_ttm_list = self.fundamental_dict['hfactor_ttm']
        hfactor_quarter_list = self.fundamental_dict['hfactor_quarter']
        report_date_list = self.fundamental_dict['report_date']
        valid_list = self.fundamental_dict['valid']
        growth_list = self.fundamental_dict['growth']

        ### calculate quarter date and report trading date
        start_date = int(self.update_date[0])
        start_year = np.floor(start_date / 10000) - 1
        end_date = int(self.update_date[-1])
        end_year = np.floor(end_date / 10000)
        all_year = np.arange(start_year, end_year + 1)
        all_quarter = np.array([331, 630, 930, 1231])
        quarter_date = all_year.reshape(len(all_year), 1).dot(np.ones((1, len(all_quarter)))) * 10000 + np.ones(
            (len(all_year), 1)).dot(all_quarter.reshape(1, len(all_quarter)))
        quarter_date = list(quarter_date[quarter_date < end_date].astype('int').astype('str'))
        report_trading_date = self.data_api.tradingday(int(start_year * 10000 + 101), int(end_date))
        report_trading_date = np.array(report_trading_date).astype('int')
        stm_issuingdate = self.data_api.get_factor_value('Basic_factor', self.universe, quarter_date,
                                                         ['stm_issuingdate']).stm_issuingdate.astype('float').unstack()
        stm_issuingdate = stm_issuingdate.reindex(columns=self.universe).values
        if 'quarter_date' in report_date_list:
            self.raw_fundamental['quarter_date'] = np.array(quarter_date).astype('int')
        if 'report_trading_date' in report_date_list:
            self.raw_fundamental['report_trading_date'] = report_trading_date
        if 'stm_issuingdate' in report_date_list:
            self.raw_fundamental['stm_issuingdate'] = stm_issuingdate

        ### download hdf_publishday factors
        res = self.data_api.get_factor_value('Basic_factor', self.universe, quarter_date, hdf_publishday_list)
        for i in hdf_publishday_list:
            temp_q = res[i].unstack().reindex(columns=self.universe).values
            temp = np.nan * np.ones((len(self.update_date), len(self.universe)))
            for j, item in enumerate(self.update_date):
                temp[j] = pd.DataFrame(np.where(stm_issuingdate <= int(item), temp_q, np.nan)).fillna(
                    method='ffill').iloc[-1].values
            if i != 'roe2_ttm':
                self.raw_fundamental[i] = temp
            else:
                self.raw_fundamental['roa2_ttm'] = temp
            if i in hfactor_quarter_list:
                self.raw_fundamental[i + '_quarter'] = temp_q

        ### download hdf_ttm factors
        # res = self.data_api.get_factor_value('Basic_factor', self.universe, quarter_date, hdf_ttm_list)
        # for i in hdf_ttm_list:
        #     temp_q = res[i].unstack().reindex(columns=self.universe).values
        #     temp = np.nan * np.ones((len(self.update_date), len(self.universe)))
        #     for j, item in enumerate(self.update_date):
        #         temp[j] = pd.DataFrame(np.where(stm_issuingdate <= int(item), temp_q, np.nan)).fillna(
        #             method='ffill').iloc[-1].values
        #     self.raw_fundamental[i + '_ttm'] = temp
        #     if i in hfactor_quarter_list:
        #         self.raw_fundamental[i + '_quarter'] = temp_q

        ### download hfactor_ttm factors
        res = self.data_api.get_factor_value('Basic_factor', self.universe, self.update_date, hfactor_ttm_list)
        for i in res.columns:
            self.raw_fundamental[i] = res[i].unstack().reindex(columns=self.universe).values

        ### download hdf_ttm factors
        for i in hdf_ttm_list:
            temp_q = self.__ttm_calculator(i, quarter_date)
            temp = np.nan * np.ones((len(self.update_date), len(self.universe)))
            for j, item in enumerate(self.update_date):
                temp[j] = pd.DataFrame(np.where(stm_issuingdate <= int(item), temp_q, np.nan)).fillna(
                    method='ffill').iloc[-1].values
            self.raw_fundamental[i + '_ttm'] = temp

        ### downlaod growth factors
        growth_parameter = [(i[:-3], int(i[-2])) for i in growth_list]
        for i in growth_parameter:
            f, p = i[0], i[1]
            temp_q = self.__growth_calculator(f, quarter_date, p)
            temp = np.nan * np.ones((len(self.update_date), len(self.universe)))
            for j, item in enumerate(self.update_date):
                temp[j] = pd.DataFrame(np.where(stm_issuingdate <= int(item), temp_q, np.nan)).fillna(
                    method='ffill').iloc[-1].values
            self.raw_fundamental[f + '_{}y'.format(p)] = temp

        ### download hfactor_quarter factors
        hfactor_quarter_list = list(set(hfactor_quarter_list) - set(hdf_publishday_list))
        res = self.data_api.get_factor_value('Basic_factor', self.universe, quarter_date, hfactor_quarter_list)
        for i in hfactor_quarter_list:
            self.raw_fundamental[i + '_quarter'] = res[i].unstack().reindex(columns=self.universe).values

        ### download valid factors (listing, delisting, stpt stocks)
        if 'listing_date' in valid_list:
            temp = self.data_api.get_factor_value('Basic_factor', self.universe, ['20980105'],
                                                  ['listing_date']).listing_date.reindex(self.universe).values
            self.raw_fundamental['Listing_date'] = temp

        if 'delisting_date' in valid_list:
            temp = self.data_api.get_factor_value('Basic_factor', self.universe, ['20980105'],
                                                  ['delisting_date']).delisting_date.reindex(self.universe).values
            self.raw_fundamental['Delisting_date'] = temp

        if 'STPT' in valid_list:
            stpt = np.ones((len(self.update_date), len(self.universe)))
            for i, item in enumerate(self.update_date):
                temp = self.data_api.stock_filter(self.universe, int(item), 'STPT').set_index('stock')['stock_name']
                if len(temp) == 0:
                    stpt[i] = 0
                else:
                    idx = ~temp.reindex(self.universe).isnull().values
                    stpt[i, idx] = 0
            self.raw_fundamental['STPT'] = stpt

        print('download fundamental data done !')

        if self.save_flag:
            raw_fundamental_path = self.save_path + '/raw_fundamental.mat'
            spio.savemat(raw_fundamental_path, self.raw_fundamental)
            print(' raw fundamental data has been saved !')

    def download_raw_index_industry(self):
        """"""
        print('start query index and industry data from xquant ......')

        index_code_list = self.index_industry_dict['index_code']
        index_factor_list = self.index_industry_dict['index_factor']
        index_factor_map_wind = self.index_industry_dict['index_factor_map_wind']
        index_data_list = self.index_industry_dict['index_data']
        industry_list = self.index_industry_dict['industry']
        
        ### downlaod index close and open
        res = self.data_api.get_factor_value('WIND_AIndexEODPrices', factors=['S_INFO_WINDCODE', 'TRADE_DT']+index_factor_map_wind, 
                         TRADE_DT=['>='+self.start_date, '<='+self.end_date], S_INFO_WINDCODE=index_code_list).sort_values(by=['TRADE_DT'],ascending=True)
        for code in index_code_list:
            code_df = res[res['S_INFO_WINDCODE']==code]
            for var, windvar in zip(index_factor_list, index_factor_map_wind):
                var_name = var + '_' + code.replace('.', '')
                if code.split('.')[-1]=='CSI':
                    var_name = var + '_' + code.split('.')[0] + 'SH'   ### 000985.CSI to 000985.SH for dump file name
                self.raw_index_industry[var_name] = code_df[windvar].values

        ### download index data, HS300, ZZ500, ZZ800, SZ50
        for index in index_data_list:
            var_name = index + '_index'
            self.raw_index_industry[var_name] = np.empty(len(self.update_date),dtype=object)
            for idx, date in enumerate(self.update_date):
                self.raw_index_industry[var_name][idx] = self.data_api.hset('INDEX',self.trading_date[-2],index).sort_values(by=['stock']).values   

        ### download industry code
        for indus in industry_list:
            standard_type = indus[:-1].upper()
            level = int(indus[-1:]);
            code_str = indus + '_industry_code'
            name_str = indus + '_industry_name'
            self.raw_index_industry[code_str] = np.empty((len(self.update_date),len(self.universe)),dtype=object)
            self.raw_index_industry[name_str] = np.empty((len(self.update_date),len(self.universe)),dtype=object)
            for idx, date in enumerate(self.update_date):
                try:
                    res = self.data_api.hsi(self.universe, date, standard_type, level)
                except:
                    self.raw_index_industry[code_str][idx] = np.nan
                    self.raw_index_industry[name_str][idx] = np.nan
                    continue
                #20191211, bug in IndustryClassCICIS data source, 600747.SH
                #if res.shape[0]!=len(self.universe):
                #    res = res.drop_duplicates(subset=['stock'],keep='first')
                self.raw_index_industry[code_str][idx] = res[res['stock']==self.universe]['industry_code'].values
                self.raw_index_industry[name_str][idx] = res[res['stock']==self.universe]['industry_name'].values

        if not self.raw_index_industry:
            print('attention: index industry factor list is empty, no index industry factor data downloaded \n')
        
        print('download index and industry data done !')

        if self.save_flag:
            raw_index_industry_path = self.save_path + '/raw_index_industry.mat'
            spio.savemat(raw_index_industry_path, self.raw_index_industry)
            print(' raw index industry data has been saved !')

    def update_data(self):
        self.download_raw_base()
        self.download_raw_fundamental()
        self.download_raw_index_industry()


if __name__ == '__main__':
    start_date = '20190102'
    end_date = '20190105'
    update_type = 0
    print('downloading daily data from ', start_date, ' to ', end_date)
    instance = DataIOFromXquant(start_date=start_date, end_date=end_date, update_type=update_type, save_flag=True)
    instance.update_data()

