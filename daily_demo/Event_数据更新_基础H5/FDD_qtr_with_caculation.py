
import sys
import datetime as dt
import pandas as pd
import os
import numpy as np
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
from log import Log
import config_reader
from multifactor.data.utils import *

def FDD_qtr_retriever_withcal(date, dataset_name):
    print('mission start')
    print(dataset_name)
    h5_path = '/data/group/800080/warehouse/prod/DATABASE/WIND/'
    if dataset_name == 'ebitdatosales':
        factor1 = ['S_FA_EBITDA']
        table1 = 'AShareFinancialIndicator'
        table_path1 = h5_path +  table1 + '/' +  table1 + '.h5'
        df1 = IO.read_data(date, columns = factor1, alt = table_path1)
        factor2 = ['TOT_OPER_REV', 'STATEMENT_TYPE']
        table2 = 'AShareIncome'
        table_path2 = h5_path +  table2 + '/'  + table2 + '.h5'
        df2 = IO.read_data(date, columns = factor2, alt=table_path2)
        df2 = df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df = pd.concat([df1, df2], axis = 1)
        df[dataset_name] = df.apply(lambda x : 100 * x['S_FA_EBITDA'] / x['TOT_OPER_REV'], axis=1)
        df.drop(['S_FA_EBITDA', 'TOT_OPER_REV'], axis=1, inplace=True)
        df.reset_index('dt', inplace = True)
        df.drop('dt', axis=1, inplace=True)
        
    elif dataset_name == 'ocftocf':
        factor2 = ['NET_CASH_FLOWS_OPER_ACT', 'NET_CASH_FLOWS_INV_ACT', 'NET_CASH_FLOWS_FNC_ACT', 'STATEMENT_TYPE']
        table2 = 'AShareCashFlow'
        table_path2 = h5_path +  table2 + '/' +  table2 + '.h5'
        df = IO.read_data(date, columns = factor2, alt=table_path2)
        df = df[df['STATEMENT_TYPE'] == 408001000.0]
        df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df['sum'] = df.sum(axis=1)
        df[dataset_name] = df.apply(lambda x : 100 * x['NET_CASH_FLOWS_OPER_ACT'] / x['sum'],axis=1)
        df.drop(['NET_CASH_FLOWS_OPER_ACT', 'NET_CASH_FLOWS_INV_ACT', 'NET_CASH_FLOWS_FNC_ACT', 'sum'], axis = 1, inplace=True)
        df.reset_index('dt', inplace = True)
        df.drop('dt', axis=1, inplace=True)
        
    elif dataset_name == 'fcftocf':
        factor = ['NET_CASH_FLOWS_FNC_ACT', 'NET_CASH_FLOWS_OPER_ACT', 'NET_CASH_FLOWS_INV_ACT',  'STATEMENT_TYPE']
        table = 'AShareCashFlow'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df = IO.read_data(date, columns = factor, alt=table_path)
        df= df[df['STATEMENT_TYPE'] == 408001000.0]
        df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df['sum'] = df.sum(axis=1)
        df[dataset_name] = df.apply(lambda x : 100 * x['NET_CASH_FLOWS_FNC_ACT'] / x['sum'], axis=1)
        df.drop(['NET_CASH_FLOWS_OPER_ACT', 'NET_CASH_FLOWS_INV_ACT', 'NET_CASH_FLOWS_FNC_ACT', 'sum'], axis = 1, inplace=True)
        df.reset_index('dt', inplace = True)
        df.drop('dt', axis=1, inplace=True)
        
    elif dataset_name == 'ocftoop':
        factor = ['S_FA_OCFTOOPERATEINCOME']
        table = 'AShareFinancialIndicator'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df = IO.read_data(date, columns = factor, alt=table_path)
        df[dataset_name] = df.apply(lambda x : 100 * x['S_FA_OCFTOOPERATEINCOME'], axis=1)
        df.drop(['S_FA_OCFTOOPERATEINCOME'],axis=1, inplace=True)
        df.reset_index('dt', inplace = True)
        df.drop('dt', axis=1, inplace=True)
        
    elif dataset_name == 'ocftoassets':
        factor1 = ['NET_CASH_FLOWS_OPER_ACT', 'STATEMENT_TYPE']
        table1 = 'AShareCashFlow'
        table_path1 = h5_path +  table1 + '/' +  table1 + '.h5'
        df1 = IO.read_data(date, columns = factor1, alt = table_path1)
        df1= df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop('STATEMENT_TYPE', axis=1, inplace=True)
        list_check = []
        for index in df1.index.values:
            if not index in list_check:
                list_check.append(index)
            else:
                df1.drop(index, axis=0, inplace=True)
        factor2 = ['TOT_ASSETS', 'STATEMENT_TYPE']
        table2 = 'AShareBalanceSheet'
        table_path2 = h5_path +  table2 + '/' +  table2 + '.h5'
        df2 = IO.read_data(date, columns = factor2, alt=table_path2)
        df2 = df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop('STATEMENT_TYPE', axis=1, inplace=True)
        print(df1, df2)
        df = pd.concat([df1, df2], axis = 1)
        df[dataset_name] = df.apply(lambda x : 100 * x['NET_CASH_FLOWS_OPER_ACT'] / x['TOT_ASSETS'], axis=1)
        df.drop(['NET_CASH_FLOWS_OPER_ACT', 'TOT_ASSETS'], axis=1, inplace=True)
        df.reset_index('dt', inplace = True)
        df.drop('dt', axis=1, inplace=True)
        

    elif dataset_name == 'longdebttolongcaptial':
        factor = ['TOT_NON_CUR_LIAB', 'TOT_SHRHLDR_EQY_EXCL_MIN_INT', 'STATEMENT_TYPE']
        table = 'AShareBalanceSheet'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df = IO.read_data(date, columns = factor, alt=table_path)
        df= df[df['STATEMENT_TYPE'] == 408001000.0]
        df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df['sum'] = df.sum(axis=1)
        df[dataset_name] = df.apply(lambda x : 100 * x['TOT_NON_CUR_LIAB'] / x['sum'], axis=1)
        df.drop(['TOT_NON_CUR_LIAB', 'TOT_SHRHLDR_EQY_EXCL_MIN_INT', 'sum'], axis = 1, inplace=True)
        df.reset_index('dt', inplace = True)
        df.drop('dt', axis=1, inplace=True)
        

    elif dataset_name == 'longcapitaltoinvestment':
        factor = ['TOT_SHRHLDR_EQY_INCL_MIN_INT','LT_BORROW','BONDS_PAYABLE','LT_PAYABLE','SPECIFIC_ITEM_PAYABLE',
        'FIX_ASSETS', 'FIN_ASSETS_AVAIL_FOR_SALE', 'HELD_TO_MTY_INVEST', 'LONG_TERM_EQY_INVEST', 'STATEMENT_TYPE']
        table = 'AShareBalanceSheet'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df = IO.read_data(date, columns = factor, alt=table_path)
        df= df[df['STATEMENT_TYPE'] == 408001000.0]
        df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df.fillna(0, inplace=True)
        def help(df):
            a = df['TOT_SHRHLDR_EQY_INCL_MIN_INT'] + df['LT_BORROW'] + df['BONDS_PAYABLE'] + df['LT_PAYABLE'] + df['SPECIFIC_ITEM_PAYABLE']
            b = df['FIX_ASSETS'] + df['FIN_ASSETS_AVAIL_FOR_SALE'] + df['HELD_TO_MTY_INVEST'] + df['LONG_TERM_EQY_INVEST']
            if b == 0:
                return np.nan
            return 100 * a / b
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['TOT_SHRHLDR_EQY_INCL_MIN_INT','LT_BORROW','BONDS_PAYABLE','LT_PAYABLE','SPECIFIC_ITEM_PAYABLE',
        'FIX_ASSETS', 'FIN_ASSETS_AVAIL_FOR_SALE', 'HELD_TO_MTY_INVEST', 'LONG_TERM_EQY_INVEST'], axis = 1, inplace=True)
        df.reset_index('dt', inplace = True)
        df.drop('dt', axis=1, inplace=True)
        

    elif dataset_name == 'currentdebttoequity':
        factor = ['TOT_CUR_LIAB', 'TOT_SHRHLDR_EQY_EXCL_MIN_INT', 'STATEMENT_TYPE']
        table = 'AShareBalanceSheet'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df = IO.read_data(date, columns = factor, alt=table_path)
        df= df[df['STATEMENT_TYPE'] == 408001000.0]
        df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        def help(df):
            a = df['TOT_CUR_LIAB']
            b = df['TOT_SHRHLDR_EQY_EXCL_MIN_INT']
            return 100 * a / b
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['TOT_CUR_LIAB', 'TOT_SHRHLDR_EQY_EXCL_MIN_INT'], axis = 1, inplace=True)
        df.reset_index('dt', inplace = True)
        df.drop('dt', axis=1, inplace=True)
        

    elif dataset_name == 'ncatoequity':
        factor = ['TOT_NON_CUR_ASSETS', 'TOT_SHRHLDR_EQY_EXCL_MIN_INT','STATEMENT_TYPE']
        table = 'AShareBalanceSheet'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df = IO.read_data(date, columns = factor, alt=table_path)
        df= df[df['STATEMENT_TYPE'] == 408001000.0]
        df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        def help(df):
            a = df['TOT_NON_CUR_ASSETS']
            b = df['TOT_SHRHLDR_EQY_EXCL_MIN_INT']
            return 100 * a / b
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['TOT_NON_CUR_ASSETS', 'TOT_SHRHLDR_EQY_EXCL_MIN_INT'], axis = 1, inplace=True)
        df.reset_index('dt', inplace = True)
        df.drop('dt', axis=1, inplace=True)
        

    elif dataset_name == 'longdebttodebt':
        factor = ['LT_BORROW', 'BONDS_PAYABLE', 'LT_PAYABLE', 'SPECIFIC_ITEM_PAYABLE', 'TOT_LIAB','STATEMENT_TYPE']
        table = 'AShareBalanceSheet'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df = IO.read_data(date, columns = factor, alt=table_path)
        df= df[df['STATEMENT_TYPE'] == 408001000.0]
        df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df.fillna(0, inplace=True)
        def help(df):
            a = df['LT_BORROW'] + df['BONDS_PAYABLE'] + df['LT_PAYABLE'] + df['SPECIFIC_ITEM_PAYABLE']
            b = df['TOT_LIAB']
            if b == 0:
                return np.nan
            return 100 * a / b
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['LT_BORROW', 'BONDS_PAYABLE', 'LT_PAYABLE', 'SPECIFIC_ITEM_PAYABLE', 'TOT_LIAB'], axis = 1, inplace=True)
        df.reset_index('dt', inplace = True)
        df.drop('dt', axis=1, inplace=True)
        

    elif dataset_name == 'ebittoassets2':
        factor = ['S_FA_EBIT_TTM_INVERSE', 'S_FA_ASSET_MRQ']
        table = 'AShareTTMHis'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df = IO.read_data(date, columns = factor, alt=table_path)
        def help(df):
            a = df['S_FA_EBIT_TTM_INVERSE']
            b = df['S_FA_ASSET_MRQ']
            return 100 * a / b
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['S_FA_EBIT_TTM_INVERSE', 'S_FA_ASSET_MRQ'], axis = 1, inplace=True)
        df.reset_index('dt', inplace = True)
        df.drop('dt', axis=1, inplace=True)
        


    elif dataset_name == 'qfa_yoyeps':
        factor = ['S_QFA_EPS']
        table = 'AShareFinancialIndicator'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df1 = IO.read_data(date-10000, columns = factor, alt=table_path)
        df1.reset_index('dt', inplace = True)
        df1.drop('dt', axis=1, inplace=True)

        df2 = IO.read_data(date, columns = factor, alt=table_path)
        df2.columns = ['S_QFA_EPS2']
        df2.reset_index('dt', inplace = True)
        df2.drop('dt', axis=1, inplace=True)
        # df= df[df['STATEMENT_TYPE'] == 408001000.0]
        # df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1)
        def help(df):
            a = df['S_QFA_EPS']
            b = df['S_QFA_EPS2']
            return 100 * (b - a) / abs(a)
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['S_QFA_EPS', 'S_QFA_EPS2'], axis = 1, inplace=True)
    

    elif dataset_name == 'qfa_grossmargin':
        factor = ['S_FA_GROSSMARGIN']
        table = 'AShareFinancialIndicator'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df1 = IO.read_data(date, columns = factor, alt=table_path)
        df1.reset_index('dt', inplace = True)
        df1.drop('dt', axis=1, inplace=True)
        if date % 10000 == 331:
            df = df1
            df.columns = [dataset_name]

        else:
            if date % 10000 == 630:
                pre_date = int(date / 10000) * 10000 + 331
            elif date % 10000 == 930:
                pre_date = int(date / 10000) * 10000 + 630
            elif date % 10000 == 1231:
                pre_date = int(date / 10000) * 10000 + 930

            df2 = IO.read_data(pre_date, columns = factor, alt=table_path)
            df2.columns = ['S_FA_GROSSMARGIN2']
            df2.reset_index('dt', inplace = True)
            df2.drop('dt', axis=1, inplace=True)
            df = pd.concat([df1, df2], axis=1)
            def help(df):
                a = df['S_FA_GROSSMARGIN']
                b = df['S_FA_GROSSMARGIN2']
                return a - b
            df[dataset_name] = df.apply(lambda x : help(x), axis=1)
            df.drop(['S_FA_GROSSMARGIN', 'S_FA_GROSSMARGIN2'], axis = 1, inplace=True)
#        print(df)
    elif dataset_name == 'qfa_yoyocf':
        factor = ['TOT_LIAB', 'STATEMENT_TYPE']
        table = 'AShareBalanceSheet'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df1 = IO.read_data(date-10000, columns = factor, alt=table_path)
        df1= df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df1.reset_index('dt', inplace = True)
        df1.drop('dt', axis=1, inplace=True)

        df2 = IO.read_data(date, columns = factor, alt=table_path)
        df2= df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df2.columns = ['TOT_LIAB2']
        df2.reset_index('dt', inplace = True)
        df2.drop('dt', axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1)
        def help(df):
            a = df['TOT_LIAB']
            b = df['TOT_LIAB2']
            return 100 * (b - a) / abs(a)
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['TOT_LIAB', 'TOT_LIAB2'], axis = 1, inplace=True)
        

    elif dataset_name == 'qfa_yoycf':
        factor = ['NET_INCR_CASH_CASH_EQU', 'STATEMENT_TYPE']
        table = 'AShareCashFlow'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df1 = IO.read_data(date-10000, columns = factor, alt=table_path)
        df1= df1[df1['STATEMENT_TYPE'] == 408004000.0]
        df1.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df1.reset_index('dt', inplace = True)
        df1.drop('dt', axis=1, inplace=True)

        df2 = IO.read_data(date, columns = factor, alt=table_path)
        df2= df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df2.columns = ['NET_INCR_CASH_CASH_EQU2']
        df2.reset_index('dt', inplace = True)
        df2.drop('dt', axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1)
        def help(df):
            a = df['NET_INCR_CASH_CASH_EQU']
            b = df['NET_INCR_CASH_CASH_EQU2']
            return 100 * (b - a) / abs(a)
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['NET_INCR_CASH_CASH_EQU', 'NET_INCR_CASH_CASH_EQU2'], axis = 1, inplace=True)
        

    elif dataset_name == 'yoy_cash':
        factor = ['MONETARY_CAP', 'STATEMENT_TYPE']
        table = 'AShareBalanceSheet'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df1 = IO.read_data(date-10000, columns = factor, alt=table_path)
        df1= df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df1.reset_index('dt', inplace = True)
        df1.drop('dt', axis=1, inplace=True)

        df2 = IO.read_data(date, columns = factor, alt=table_path)
        df2= df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df2.columns = ['MONETARY_CAP2']
        df2.reset_index('dt', inplace = True)
        df2.drop('dt', axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1)
        def help(df):
            a = df['MONETARY_CAP']
            b = df['MONETARY_CAP2']
            return 100 * (b - a) / abs(a)
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['MONETARY_CAP', 'MONETARY_CAP2'], axis = 1, inplace=True)
        

    elif dataset_name == 'yoy_fixedassets':
        factor = ['STM_BS_TOT', 'STATEMENT_TYPE']
        table = 'AShareBalanceSheet'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df1 = IO.read_data(date-10000, columns = factor, alt=table_path)
        df1= df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df1.reset_index('dt', inplace = True)
        df1.drop('dt', axis=1, inplace=True)

        df2 = IO.read_data(date, columns = factor, alt=table_path)
        df2= df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df2.columns = ['STM_BS_TOT2']
        df2.reset_index('dt', inplace = True)
        df2.drop('dt', axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1)
        def help(df):
            a = df['STM_BS_TOT']
            b = df['STM_BS_TOT2']
            return 100 * (b - a) / abs(a)
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['STM_BS_TOT', 'STM_BS_TOT2'], axis = 1, inplace=True)
        

    elif dataset_name == 'yoydebt':
        factor = ['TOT_LIAB', 'STATEMENT_TYPE']
        table = 'AShareBalanceSheet'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df1 = IO.read_data(date-10000, columns = factor, alt=table_path)
        df1= df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df1.reset_index('dt', inplace = True)
        df1.drop('dt', axis=1, inplace=True)

        df2 = IO.read_data(date, columns = factor, alt=table_path)
        df2= df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df2.columns = ['TOT_LIAB2']
        df2.reset_index('dt', inplace = True)
        df2.drop('dt', axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1)
        def help(df):
            a = df['TOT_LIAB']
            b = df['TOT_LIAB2']
            return 100 * (b - a) / abs(a)
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['TOT_LIAB', 'TOT_LIAB2'], axis = 1, inplace=True)

    elif dataset_name == 'operatecaptialturn':
    
        factor = ['TOT_OPER_REV', 'STATEMENT_TYPE']
        table = 'AShareIncome'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df1 = IO.read_data(date, columns = factor, alt=table_path)
        df1= df1[df1['STATEMENT_TYPE'] == 408001000.0]
        
        df1.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df1.reset_index('dt', inplace = True)
        df1.drop('dt', axis=1, inplace=True)

        factor2 = ['TOT_CUR_ASSETS', 'TOT_CUR_LIAB', 'STATEMENT_TYPE']
        table2 = 'AShareBalanceSheet'
        table_path2 = h5_path +  table2 + '/' +  table2 + '.h5'
        df2 = IO.read_data(date, columns = factor2, alt=table_path2)
        df2= df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df2.reset_index('dt', inplace = True)
        df2.drop('dt', axis=1, inplace=True)

        date2 = (int((date - 10000) / 10000) * 10000 + 1231) 
        df3 = IO.read_data(date2, columns = factor2, alt=table_path2)
        df3= df3[df3['STATEMENT_TYPE'] == 408001000.0]
        df3.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df3.columns = ['TOT_CUR_ASSETS2', 'TOT_CUR_LIAB2']
        df3.reset_index('dt', inplace = True)
        df3.drop('dt', axis=1, inplace=True)
        df = pd.concat([df1, df2, df3], axis=1)
        # 
        def help(df):
            a = df['TOT_OPER_REV']
            b = (df['TOT_CUR_ASSETS'] - df['TOT_CUR_LIAB'] + df['TOT_CUR_ASSETS2'] - df['TOT_CUR_LIAB2']) 
            return 2 * a / b
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['TOT_OPER_REV', 'TOT_CUR_ASSETS', 'TOT_CUR_LIAB', 'TOT_CUR_ASSETS2','TOT_CUR_LIAB2'], axis = 1, inplace=True)

    elif dataset_name == 'apturn':

        factor = ['LESS_OPER_COST', 'STATEMENT_TYPE']
        table = 'AShareIncome'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df1 = IO.read_data(date, columns = factor, alt=table_path)
        df1= df1[df1['STATEMENT_TYPE'] == 408001000.0]
        
        df1.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df1.reset_index('dt', inplace = True)
        df1.drop('dt', axis=1, inplace=True)

        factor2 = ['ACCOUNTS_PAYABLE', 'STATEMENT_TYPE']
        table2 = 'AShareBalanceSheet'
        table_path2 = h5_path +  table2 + '/' +  table2 + '.h5'
        df2 = IO.read_data(date, columns = factor2, alt=table_path2)
        df2= df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df2.reset_index('dt', inplace = True)
        df2.drop('dt', axis=1, inplace=True)

        date2 = (int((date - 10000) / 10000) * 10000 + 1231) 
        df3 = IO.read_data(date2, columns = factor2, alt=table_path2)
        df3= df3[df3['STATEMENT_TYPE'] == 408001000.0]
        df3.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df3.columns = ['ACCOUNTS_PAYABLE2']
        df3.reset_index('dt', inplace = True)
        df3.drop('dt', axis=1, inplace=True)
        df = pd.concat([df1, df2, df3], axis=1)
        df.replace(0,np.nan, inplace=True)
        def help(df):
            a = df['LESS_OPER_COST']
            b = (df['ACCOUNTS_PAYABLE'] + df['ACCOUNTS_PAYABLE2']) 
            return 2 * a / b
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['LESS_OPER_COST', 'ACCOUNTS_PAYABLE', 'ACCOUNTS_PAYABLE2'], axis = 1, inplace=True)

    elif dataset_name == 'yoy_assets':
        factor = ['TOT_ASSETS', 'STATEMENT_TYPE']
        table = 'AShareBalanceSheet'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df1 = IO.read_data(date-10000, columns = factor, alt=table_path)
        df1= df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df1.reset_index('dt', inplace = True)
        df1.drop('dt', axis=1, inplace=True)

        df2 = IO.read_data(date, columns = factor, alt=table_path)
        df2= df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df2.columns = ['TOT_ASSETS2']
        df2.reset_index('dt', inplace = True)
        df2.drop('dt', axis=1, inplace=True)


        df12 = IO.read_data(date - 10000, columns = factor, alt=table_path)
        df12= df12[df12['STATEMENT_TYPE'] == 408004000.0]
        df12.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df12.columns = ['TOT_ASSETS12']
        df12.reset_index('dt', inplace = True)
        df12.drop('dt', axis=1, inplace=True)

        factor = ['TOT_ASSETS']
        table = 'AShareProfitExpress'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df3 = IO.read_data(date-10000, columns = factor, alt=table_path)
        df3.columns = ['TOT_ASSETS3']
        df3.reset_index('dt', inplace = True)
        df3.drop('dt', axis=1, inplace=True)
        
        df4 = IO.read_data(date, columns = factor, alt=table_path)
        df4.columns = ['TOT_ASSETS4']
        df4.reset_index('dt', inplace = True)
        df4.drop('dt', axis=1, inplace=True)
        df = pd.concat([df1, df2, df3, df4, df12], axis=1)
        def help(df):
            if np.isnan(df['TOT_ASSETS12']):
                if np.isnan(df['TOT_ASSETS']):
                    a = df['TOT_ASSETS3']
                else:
                    a = df['TOT_ASSETS']
            else:
                a = df['TOT_ASSETS12']
            if np.isnan(df['TOT_ASSETS2']):
                b = df['TOT_ASSETS4']
            else:
                b = df['TOT_ASSETS2']
            return 100 * (b - a) / abs(a)
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['TOT_ASSETS', 'TOT_ASSETS2', 'TOT_ASSETS3', 'TOT_ASSETS4', 'TOT_ASSETS12'], axis = 1, inplace=True)
    

    elif dataset_name == 'cashtostdebt':
        factor = ['MONETARY_CAP', 'ST_BORROW', 'ACCOUNTS_PAYABLE', 'TRADABLE_FIN_LIAB', 'NON_CUR_LIAB_DUE_WITHIN_1Y','STATEMENT_TYPE']
        table = 'AShareBalanceSheet'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df = IO.read_data(date, columns = factor, alt=table_path)
        df = df[df['STATEMENT_TYPE'] == 408001000.0]
        df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df.reset_index('dt', inplace = True)
        df.drop('dt', axis=1, inplace=True)

        def help(df):
            a = df['MONETARY_CAP']
            b = (df['ST_BORROW'] + df['ACCOUNTS_PAYABLE'] + df['TRADABLE_FIN_LIAB'] + df['NON_CUR_LIAB_DUE_WITHIN_1Y']) 
            return  a / b
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['MONETARY_CAP', 'ST_BORROW', 'ACCOUNTS_PAYABLE', 'TRADABLE_FIN_LIAB', 'NON_CUR_LIAB_DUE_WITHIN_1Y'], axis = 1, inplace=True)


    elif dataset_name == 'ocftointerest':
        factor1 = ['NET_CASH_FLOWS_OPER_ACT', 'STATEMENT_TYPE']
        table1 = 'AShareCashFlow'
        table_path1 = h5_path +  table1 + '/' +  table1 + '.h5'
        df1 = IO.read_data(date, columns = factor1, alt = table_path1)
        df1= df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop('STATEMENT_TYPE', axis=1, inplace=True)
        list_check = []
        for index in df1.index.values:
            if not index in list_check:
                list_check.append(index)
            else:
                df1.drop(index, axis=0, inplace=True)
        factor2 = ['S_STMNOTE_FINEXP']
        table2 = 'AShareFinancialIndicator'
        table_path2 = h5_path +  table2 + '/' +  table2 + '.h5'
        df2 = IO.read_data(date, columns = factor2, alt=table_path2)
        df = pd.concat([df1, df2], axis = 1)
        df[dataset_name] = df.apply(lambda x : x['NET_CASH_FLOWS_OPER_ACT'] / x['S_STMNOTE_FINEXP'], axis=1)
        df.drop(['NET_CASH_FLOWS_OPER_ACT', 'S_STMNOTE_FINEXP'], axis=1, inplace=True)
        df.reset_index('dt', inplace = True)
        df.drop('dt', axis=1, inplace=True)

    elif dataset_name == 'ocftodividend':
        factor1 = ['NET_CASH_FLOWS_OPER_ACT', 'STATEMENT_TYPE']
        table1 = 'AShareCashFlow'
        table_path1 = h5_path +  table1 + '/' +  table1 + '.h5'
        df1 = IO.read_data(date, columns = factor1, alt = table_path1)
        df1= df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop('STATEMENT_TYPE', axis=1, inplace=True)
        list_check = []
        for index in df1.index.values:
            if not index in list_check:
                list_check.append(index)
            else:
                df1.drop(index, axis=0, inplace=True)
        factor2 = ['COMSHARE_DVD_PAYABLE', 'STATEMENT_TYPE']
        table2 = 'AShareIncome'
        table_path2 = h5_path +  table2 + '/'  + table2 + '.h5'
        df2 = IO.read_data(date, columns = factor2, alt=table_path2)
        df2 = df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df = pd.concat([df1, df2], axis = 1)
        df[dataset_name] = df.apply(lambda x : x['NET_CASH_FLOWS_OPER_ACT'] / x['COMSHARE_DVD_PAYABLE'], axis=1)
        df.drop(['NET_CASH_FLOWS_OPER_ACT', 'COMSHARE_DVD_PAYABLE'], axis=1, inplace=True)
        df.reset_index('dt', inplace = True)
        df.drop('dt', axis=1, inplace=True)

    elif dataset_name == 'yoyprofit':
        factor = ['NET_PROFIT_INCL_MIN_INT_INC', 'STATEMENT_TYPE']
        table = 'AShareIncome'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df1 = IO.read_data(date-10000, columns = factor, alt=table_path)
        df1= df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df1.reset_index('dt', inplace = True)
        df1.drop('dt', axis=1, inplace=True)
        list_check = []
        for index in df1.index.values:
            if not index in list_check:
                list_check.append(index)
            else:
                df1.drop(index, axis=0, inplace=True)
        df2 = IO.read_data(date, columns = factor, alt=table_path)
        df2= df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df2.columns = ['NET_PROFIT_INCL_MIN_INT_INC2']
        df2.reset_index('dt', inplace = True)
        df2.drop('dt', axis=1, inplace=True)
        list_check = []
        for index in df2.index.values:
            if not index in list_check:
                list_check.append(index)
            else:
                df2.drop(index, axis=0, inplace=True)

        df = pd.concat([df1, df2], axis=1)
        def help(df):
            a = df['NET_PROFIT_INCL_MIN_INT_INC']
            b = df['NET_PROFIT_INCL_MIN_INT_INC2']
            return 100 * (b - a) / abs(a)
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['NET_PROFIT_INCL_MIN_INT_INC', 'NET_PROFIT_INCL_MIN_INT_INC2'], axis = 1, inplace=True)
    
    elif dataset_name == 'yoycf':
        factor = ['S_FA_CFPS', 'TOT_SHR']
        table = 'AShareFinancialIndicator'
        table_path = h5_path +  table + '/' +  table + '.h5'
        df1 = IO.read_data(date-10000, columns = factor, alt=table_path)
        df1.reset_index('dt', inplace = True)
        df1.drop('dt', axis=1, inplace=True)

        df2 = IO.read_data(date, columns = factor, alt=table_path)
        df2.columns = ['S_FA_CFPS2', 'TOT_SHR2']
        df2.reset_index('dt', inplace = True)
        df2.drop('dt', axis=1, inplace=True)
        # df= df[df['STATEMENT_TYPE'] == 408001000.0]
        # df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1)
        def help(df):
            a = df['S_FA_CFPS'] * df['TOT_SHR']
            b = df['S_FA_CFPS2'] * df['TOT_SHR2']
            return 100 * (b - a) / abs(a)
        df[dataset_name] = df.apply(lambda x : help(x), axis=1)
        df.drop(['S_FA_CFPS', 'TOT_SHR', 'S_FA_CFPS2', 'TOT_SHR2'], axis = 1, inplace=True)


    universe_folder = config_reader.getConfig('root_path', 'wind_stock_path')
    stock_list = pd.read_csv(universe_folder+str(date)+'.csv',header=0)['Ticker'].values.tolist()
    exist_stock = df.index.values.tolist()
    stock_list1 = list(set(exist_stock) & set(stock_list))
    stock_list2 = list(set(stock_list) - set(stock_list1))
    df = df.loc[stock_list1]
    data = []
    for stock in stock_list2:
        data.append(np.nan)
    df2 = pd.DataFrame(data, index=stock_list2, columns=[dataset_name])
    df = df.append(df2)
    df = df.sort_index()
    df.index.name = 'Ticker'
#    print(df)
    return df
