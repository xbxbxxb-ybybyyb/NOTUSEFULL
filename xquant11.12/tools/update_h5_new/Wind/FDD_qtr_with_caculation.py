# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 13:17:25 2018

@author: 012315  013160
"""
import sys
import datetime as dt
import pandas as pd
import os
import numpy as np
from log import Log
from Wind.utils import *
logger = Log("FDD_qtr_with_caculation")

def FDD_qtr_retriever_withcal(sql_config,cdate_list,date, dataset_name):
    logger.info("The factor %s caculation start"%dataset_name)
    if dataset_name == 'ebitdatosales':
        factor1 = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'S_FA_EBITDA']
        table1 = 'Wind.AShareFinancialIndicator'
        df1 = get_wind_data(table1, factor1,sql_config, date)
        df1.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df1.drop("REPORT_PERIOD", axis=1, inplace=True)
        df1.set_index("Ticker", inplace=True)

        factor2 = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'TOT_OPER_REV', 'STATEMENT_TYPE']
        table2 = 'Wind.AShareIncome'
        df2 = get_wind_data(table2, factor2,sql_config, date)
        df2.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df2.set_index("Ticker", inplace=True)
        if df2['STATEMENT_TYPE'].dtype == 'object':
            df2["STATEMENT_TYPE"] = df2["STATEMENT_TYPE"].apply(pd.to_numeric)
        df2 = df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1,sort=True)
        for i in df.index.values:
            if df.loc[i,'TOT_OPER_REV'] == 0 or pd.isnull(df.loc[i,'TOT_OPER_REV']):
                df.loc[i,'TOT_OPER_REV'] = np.nan
            if pd.isnull(df.loc[i,'S_FA_EBITDA']):
                df.loc[i,'S_FA_EBITDA'] = np.nan
        df[dataset_name] = df.apply(lambda x: 100 * x['S_FA_EBITDA'] / x['TOT_OPER_REV'], axis=1)
        df.drop(['S_FA_EBITDA', 'TOT_OPER_REV'], axis=1, inplace=True)
        if isinstance(date, int):
            df['dt'] = pd.Timestamp(str(date))
        else:
            df['dt'] = date
        df.index.name = 'Ticker'
        df.reset_index('Ticker', inplace=True)
        df = df[['Ticker', 'dt', dataset_name]]

    elif dataset_name == 'ocftocf':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'NET_CASH_FLOWS_OPER_ACT', 'NET_CASH_FLOWS_INV_ACT',
                  'NET_CASH_FLOWS_FNC_ACT', 'STATEMENT_TYPE']
        table = 'Wind.AShareCashFlow'
        df = get_wind_data(table, factor,sql_config, date)
        df.rename(columns={"S_INFO_WINDCODE": "Ticker", "REPORT_PERIOD": "dt"}, inplace=True)
        if df['STATEMENT_TYPE'].dtype == 'object':
            df["STATEMENT_TYPE"] = df["STATEMENT_TYPE"].apply(pd.to_numeric)
        df = df[df['STATEMENT_TYPE'] == 408001000.0]
        df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df.set_index(["dt", "Ticker"], inplace=True)
        df['sum'] = df.sum(axis=1)
        df.reset_index(inplace=True)
        for i in df.index.values:
            if df.loc[i,'sum'] == 0 or pd.isnull(df.loc[i,'sum']):
                df.loc[i,'sum'] = np.nan
        df[dataset_name] = df.apply(lambda x: 100 * x['NET_CASH_FLOWS_OPER_ACT'] / x['sum'], axis=1)
        df.drop(['NET_CASH_FLOWS_OPER_ACT', 'NET_CASH_FLOWS_INV_ACT', 'NET_CASH_FLOWS_FNC_ACT', 'sum'], axis=1,
                inplace=True)
        df = df[['Ticker', 'dt', dataset_name]]

    elif dataset_name == 'fcftocf':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'NET_CASH_FLOWS_FNC_ACT', 'NET_CASH_FLOWS_OPER_ACT',
                  'NET_CASH_FLOWS_INV_ACT', 'STATEMENT_TYPE']
        table = 'Wind.AShareCashFlow'
        df = get_wind_data(table, factor,sql_config, date)
        df.rename(columns={"S_INFO_WINDCODE": "Ticker", "REPORT_PERIOD": "dt"}, inplace=True)
        if df['STATEMENT_TYPE'].dtype == 'object':
            df["STATEMENT_TYPE"] = df["STATEMENT_TYPE"].apply(pd.to_numeric)
        df = df[df['STATEMENT_TYPE'] == 408001000.0]
        df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df.set_index(["dt", "Ticker"], inplace=True)
        df['sum'] = df.sum(axis=1)
        df.reset_index(inplace = True)
        for i in df.index.values:
            if df.loc[i,'sum'] == 0 or pd.isnull(df.loc[i,'sum']):
                df.loc[i,'sum'] = np.nan
        df[dataset_name] = df.apply(lambda x: 100 * x['NET_CASH_FLOWS_FNC_ACT'] / x['sum'], axis=1)
        df.drop(['NET_CASH_FLOWS_OPER_ACT', 'NET_CASH_FLOWS_INV_ACT', 'NET_CASH_FLOWS_FNC_ACT', 'sum'], axis=1,
                inplace=True)
        df = df[['Ticker', 'dt', dataset_name]]

    elif dataset_name == 'ocftoop':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'S_FA_OCFTOOPERATEINCOME']
        table = 'Wind.AShareFinancialIndicator'
        df = get_wind_data(table, factor,sql_config, date)
        df.rename(columns={"S_INFO_WINDCODE": "Ticker", "REPORT_PERIOD": "dt"}, inplace=True)
        df[dataset_name] = df.apply(lambda x: 100 * x['S_FA_OCFTOOPERATEINCOME'], axis=1)
        df.drop(['S_FA_OCFTOOPERATEINCOME'], axis=1, inplace=True)
        df = df[['Ticker', 'dt', dataset_name]]

    elif dataset_name == 'ocftoassets':
        factor1 = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'NET_CASH_FLOWS_OPER_ACT', 'STATEMENT_TYPE']
        table1 = 'Wind.AShareCashFlow'
        df1 = get_wind_data(table1, factor1,sql_config, date)
        df1.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df1.set_index("Ticker", inplace=True)
        if df1['STATEMENT_TYPE'].dtype == 'object':
            df1["STATEMENT_TYPE"] = df1["STATEMENT_TYPE"].apply(pd.to_numeric)
        df1 = df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)
        list_check = []
        for index in df1.index.values:
            if not index in list_check:
                list_check.append(index)
            else:
                df1.drop(index, axis=0, inplace=True)
        factor2 = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'TOT_ASSETS', 'STATEMENT_TYPE']
        table2 = 'Wind.AShareBalanceSheet'
        df2 = get_wind_data(table2, factor2,sql_config, date)
        df2.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df2.set_index("Ticker", inplace=True)
        if df2['STATEMENT_TYPE'].dtype == 'object':
            df2["STATEMENT_TYPE"] = df2["STATEMENT_TYPE"].apply(pd.to_numeric)
        df2 = df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1,sort=True)
        for i in df.index.values:
            if df.loc[i,'TOT_ASSETS'] == 0 or pd.isnull(df.loc[i,'TOT_ASSETS']):
                df.loc[i,'TOT_ASSETS'] = np.nan
        df[dataset_name] = df.apply(lambda x: 100 * x['NET_CASH_FLOWS_OPER_ACT'] / x['TOT_ASSETS'], axis=1)
        df.drop(['NET_CASH_FLOWS_OPER_ACT', 'TOT_ASSETS'], axis=1, inplace=True)
        df.index.name = "Ticker"
        df.reset_index("Ticker", inplace=True)
        if isinstance(date, int):
            df['dt'] = pd.Timestamp(str(date))
        else:
            df['dt'] = date
        df = df[['Ticker', 'dt', dataset_name]]


    elif dataset_name == 'longdebttolongcaptial':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'TOT_NON_CUR_LIAB', 'TOT_SHRHLDR_EQY_EXCL_MIN_INT',
                  'STATEMENT_TYPE']
        table = 'Wind.AShareBalanceSheet'
        df = get_wind_data(table, factor,sql_config, date)
        df.rename(columns={"S_INFO_WINDCODE": "Ticker", "REPORT_PERIOD": "dt"}, inplace=True)
        if df['STATEMENT_TYPE'].dtype == 'object':
            df["STATEMENT_TYPE"] = df["STATEMENT_TYPE"].apply(pd.to_numeric)
        df = df[df['STATEMENT_TYPE'] == 408001000.0]
        df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df.set_index(["dt", "Ticker"], inplace=True)
        df['sum'] = df.sum(axis=1)
        df.reset_index(inplace=True)
        for i in df.index.values:
            if df.loc[i,'sum'] == 0 or pd.isnull(df.loc[i,'sum']):
                df.loc[i,'sum'] = np.nan
        df[dataset_name] = df.apply(lambda x: 100 * x['TOT_NON_CUR_LIAB'] / x['sum'], axis=1)
        df.drop(['TOT_NON_CUR_LIAB', 'TOT_SHRHLDR_EQY_EXCL_MIN_INT', 'sum'], axis=1, inplace=True)
        df = df[['Ticker', 'dt', dataset_name]]


    elif dataset_name == 'longcapitaltoinvestment':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'TOT_SHRHLDR_EQY_INCL_MIN_INT', 'LT_BORROW', 'BONDS_PAYABLE',
                  'LT_PAYABLE', 'SPECIFIC_ITEM_PAYABLE',
                  'FIX_ASSETS', 'FIN_ASSETS_AVAIL_FOR_SALE', 'HELD_TO_MTY_INVEST', 'LONG_TERM_EQY_INVEST',
                  'STATEMENT_TYPE']
        table = 'Wind.AShareBalanceSheet'
        df = get_wind_data(table, factor,sql_config, date)
        df.rename(columns={"S_INFO_WINDCODE": "Ticker", "REPORT_PERIOD": "dt"}, inplace=True)
        if df['STATEMENT_TYPE'].dtype == 'object':
            df["STATEMENT_TYPE"] = df["STATEMENT_TYPE"].apply(pd.to_numeric)
        df = df[df['STATEMENT_TYPE'] == 408001000.0]
        df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df.fillna(0, inplace=True)

        def help(df):
            a = df['TOT_SHRHLDR_EQY_INCL_MIN_INT'] + df['LT_BORROW'] + df['BONDS_PAYABLE'] + df['LT_PAYABLE'] + df[
                'SPECIFIC_ITEM_PAYABLE']
            b = df['FIX_ASSETS'] + df['FIN_ASSETS_AVAIL_FOR_SALE'] + df['HELD_TO_MTY_INVEST'] + df[
                'LONG_TERM_EQY_INVEST']
            if b == 0:
                return np.nan
            return 100 * a / b

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['TOT_SHRHLDR_EQY_INCL_MIN_INT', 'LT_BORROW', 'BONDS_PAYABLE', 'LT_PAYABLE', 'SPECIFIC_ITEM_PAYABLE',
                 'FIX_ASSETS', 'FIN_ASSETS_AVAIL_FOR_SALE', 'HELD_TO_MTY_INVEST', 'LONG_TERM_EQY_INVEST'], axis=1,
                inplace=True)
        df = df[['Ticker', 'dt', dataset_name]]


    elif dataset_name == 'currentdebttoequity':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'TOT_CUR_LIAB', 'TOT_SHRHLDR_EQY_EXCL_MIN_INT', 'STATEMENT_TYPE']
        table = 'Wind.AShareBalanceSheet'
        df = get_wind_data(table, factor,sql_config, date)
        if df.empty:
            return
        df.rename(columns={"S_INFO_WINDCODE": "Ticker", "REPORT_PERIOD": "dt"}, inplace=True)
        if df['STATEMENT_TYPE'].dtype == 'object':
            df["STATEMENT_TYPE"] = df["STATEMENT_TYPE"].apply(pd.to_numeric)
        df = df[df['STATEMENT_TYPE'] == 408001000.0]
        df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        def help(df):
            a = df['TOT_CUR_LIAB']
            b = df['TOT_SHRHLDR_EQY_EXCL_MIN_INT']
            if b == 0:
                return np.nan
            return 100 * a / b

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['TOT_CUR_LIAB', 'TOT_SHRHLDR_EQY_EXCL_MIN_INT'], axis=1, inplace=True)
        df = df[['Ticker', 'dt', dataset_name]]


    elif dataset_name == 'ncatoequity':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'TOT_NON_CUR_ASSETS', 'TOT_SHRHLDR_EQY_EXCL_MIN_INT',
                  'STATEMENT_TYPE']
        table = 'Wind.AShareBalanceSheet'
        df = get_wind_data(table, factor,sql_config, date)
        df.rename(columns={"S_INFO_WINDCODE": "Ticker", "REPORT_PERIOD": "dt"}, inplace=True)
        if df['STATEMENT_TYPE'].dtype == 'object':
            df["STATEMENT_TYPE"] = df["STATEMENT_TYPE"].apply(pd.to_numeric)
        df = df[df['STATEMENT_TYPE'] == 408001000.0]
        df.drop('STATEMENT_TYPE', axis=1, inplace=True)

        def help(df):
            a = df['TOT_NON_CUR_ASSETS']
            b = df['TOT_SHRHLDR_EQY_EXCL_MIN_INT']
            if b == 0:
                return np.nan
            return 100 * a / b

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['TOT_NON_CUR_ASSETS', 'TOT_SHRHLDR_EQY_EXCL_MIN_INT'], axis=1, inplace=True)
        df = df[['Ticker', 'dt', dataset_name]]


    elif dataset_name == 'longdebttodebt':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'LT_BORROW', 'BONDS_PAYABLE', 'LT_PAYABLE',
                  'SPECIFIC_ITEM_PAYABLE', 'TOT_LIAB', 'STATEMENT_TYPE']
        table = 'Wind.AShareBalanceSheet'
        df = get_wind_data(table, factor,sql_config, date)
        df.rename(columns={"S_INFO_WINDCODE": "Ticker", "REPORT_PERIOD": "dt"}, inplace=True)
        if df['STATEMENT_TYPE'].dtype == 'object':
            df["STATEMENT_TYPE"] = df["STATEMENT_TYPE"].apply(pd.to_numeric)
        df = df[df['STATEMENT_TYPE'] == 408001000.0]
        df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        df.fillna(0, inplace=True)

        def help(df):
            a = df['LT_BORROW'] + df['BONDS_PAYABLE'] + df['LT_PAYABLE'] + df['SPECIFIC_ITEM_PAYABLE']
            b = df['TOT_LIAB']
            if b == 0:
                return np.nan
            return 100 * a / b

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['LT_BORROW', 'BONDS_PAYABLE', 'LT_PAYABLE', 'SPECIFIC_ITEM_PAYABLE', 'TOT_LIAB'], axis=1, inplace=True)
        df = df[['Ticker', 'dt', dataset_name]]


    elif dataset_name == 'ebittoassets2':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'S_FA_EBIT_TTM_INVERSE', 'S_FA_ASSET_MRQ']
        table = 'Wind.AShareTTMHis'
        df = get_wind_data(table, factor,sql_config, date)
        df.rename(columns={"S_INFO_WINDCODE": "Ticker", "REPORT_PERIOD": "dt"}, inplace=True)
        df.set_index(["Ticker", "dt"], inplace=True)

        def help(df):
            a = df['S_FA_EBIT_TTM_INVERSE']
            b = df['S_FA_ASSET_MRQ']
            if b == 0:
                return np.nan
            return 100 * a / b

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['S_FA_EBIT_TTM_INVERSE', 'S_FA_ASSET_MRQ'], axis=1, inplace=True)
        df.reset_index(inplace=True)
        df = df[['Ticker', 'dt', dataset_name]]



    elif dataset_name == 'qfa_yoyeps':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'S_QFA_EPS']
        table = 'Wind.AShareFinancialIndicator'
        df1 = get_wind_data(table, factor,sql_config, date - 10000)
        df1.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df1.set_index("Ticker", inplace=True)
        df1.drop("REPORT_PERIOD", axis=1, inplace=True)

        df2 = get_wind_data(table, factor,sql_config, date)
        df2.rename(columns={"S_INFO_WINDCODE": "Ticker", "S_QFA_EPS": "S_QFA_EPS2"}, inplace=True)
        df2.set_index("Ticker", inplace=True)
        df2.drop("REPORT_PERIOD", axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1,sort=True)

        def help(df):
            a = df['S_QFA_EPS']
            b = df['S_QFA_EPS2']
            if b == 0:
                return np.nan
            return 100 * (b - a) / abs(a)

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['S_QFA_EPS', 'S_QFA_EPS2'], axis=1, inplace=True)
        df.index.name = "Ticker"
        df.reset_index("Ticker", inplace=True)
        if isinstance(date, int):
            df['dt'] = pd.Timestamp(str(date))
        else:
            df['dt'] = date
        df = df[['Ticker', 'dt', dataset_name]]


    elif dataset_name == 'qfa_grossmargin':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'S_FA_GROSSMARGIN']
        table = 'Wind.AShareFinancialIndicator'
        df1 = get_wind_data(table, factor,sql_config, date)
        df1.rename(columns={"S_INFO_WINDCODE": "Ticker", "REPORT_PERIOD": "dt"}, inplace=True)
        df1.set_index("Ticker", inplace=True)
        if date % 10000 == 331:
            df = df1
            df.rename(columns={"S_FA_GROSSMARGIN": dataset_name},inplace=True)
            df.reset_index("Ticker", inplace=True)
            df = df[['Ticker', 'dt', dataset_name]]

        else:
            if date % 10000 == 630:
                pre_date = int(date / 10000) * 10000 + 331
            elif date % 10000 == 930:
                pre_date = int(date / 10000) * 10000 + 630
            elif date % 10000 == 1231:
                pre_date = int(date / 10000) * 10000 + 930

            df2 = get_wind_data(table, factor,sql_config, pre_date)
            df2.rename(
                columns={"S_INFO_WINDCODE": "Ticker", "REPORT_PERIOD": "dt", "S_FA_GROSSMARGIN": "S_FA_GROSSMARGIN2"},
                inplace=True)
            df2.set_index("Ticker", inplace=True)
            df1.drop("dt", axis=1, inplace=True)
            df2.drop("dt", axis=1, inplace=True)
            df = pd.concat([df1, df2], axis=1,sort=True)

            def help(df):
                a = df['S_FA_GROSSMARGIN']
                b = df['S_FA_GROSSMARGIN2']
                return a - b

            df[dataset_name] = df.apply(lambda x: help(x), axis=1)
            df.drop(['S_FA_GROSSMARGIN', 'S_FA_GROSSMARGIN2'], axis=1, inplace=True)
            df.index.name = "Ticker"
            df.reset_index("Ticker", inplace=True)
            if isinstance(date, int):
                df['dt'] = pd.Timestamp(str(date))
            else:
                df['dt'] = date
            df = df[['Ticker', 'dt', dataset_name]]

    elif dataset_name == 'qfa_yoyocf':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'TOT_LIAB', 'STATEMENT_TYPE']
        table = 'Wind.AShareBalanceSheet'
        df1 = get_wind_data(table, factor,sql_config, date - 10000)
        df1.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df1.set_index("Ticker", inplace=True)
        if df1['STATEMENT_TYPE'].dtype == 'object':
            df1["STATEMENT_TYPE"] = df1["STATEMENT_TYPE"].apply(pd.to_numeric)
        df1 = df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)

        df2 = get_wind_data(table, factor,sql_config, date)
        df2.rename(columns={"S_INFO_WINDCODE": "Ticker", "TOT_LIAB": "TOT_LIAB2"}, inplace=True)
        df2.set_index("Ticker", inplace=True)
        if df2['STATEMENT_TYPE'].dtype == 'object':
            df2["STATEMENT_TYPE"] = df2["STATEMENT_TYPE"].apply(pd.to_numeric)
        df2 = df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1,sort=True)

        def help(df):
            a = df['TOT_LIAB']
            b = df['TOT_LIAB2']
            if a == 0:
                return np.nan
            return 100 * (b - a) / abs(a)

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['TOT_LIAB', 'TOT_LIAB2'], axis=1, inplace=True)
        df.index.name = "Ticker"
        df.reset_index("Ticker", inplace=True)
        if isinstance(date, int):
            df['dt'] = pd.Timestamp(str(date))
        else:
            df['dt'] = date
        df = df[['Ticker', 'dt', dataset_name]]


    elif dataset_name == 'qfa_yoycf':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'NET_INCR_CASH_CASH_EQU', 'STATEMENT_TYPE']
        table = 'Wind.AShareCashFlow'
        df1 = get_wind_data(table, factor,sql_config, date - 10000)
        df1.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df1.set_index("Ticker", inplace=True)
        if df1['STATEMENT_TYPE'].dtype == 'object':
            df1["STATEMENT_TYPE"] = df1["STATEMENT_TYPE"].apply(pd.to_numeric)
        df1 = df1[df1.loc[:,'STATEMENT_TYPE'] == 408004000.0]
        df1.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)

        df2 = get_wind_data(table, factor,sql_config, date)
        df2.rename(columns={"S_INFO_WINDCODE": "Ticker", "NET_INCR_CASH_CASH_EQU": "NET_INCR_CASH_CASH_EQU2"},
                   inplace=True)
        df2.set_index("Ticker", inplace=True)
        if df2['STATEMENT_TYPE'].dtype == 'object':
            df2["STATEMENT_TYPE"] = df2["STATEMENT_TYPE"].apply(pd.to_numeric)
        df2 = df2[df2.loc[:,'STATEMENT_TYPE'] == 408001000.0]
        df2.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1,sort=True)
        df.index.name = "Ticker"
        df.reset_index("Ticker", inplace=True)
        if isinstance(date, int):
            df['dt'] = pd.Timestamp(str(date))
        else:
            df['dt'] = date

        def help(df):
            a = df['NET_INCR_CASH_CASH_EQU']
            b = df['NET_INCR_CASH_CASH_EQU2']
            if a == 0:
                return np.nan
            return 100 * (b - a) / abs(a)

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['NET_INCR_CASH_CASH_EQU', 'NET_INCR_CASH_CASH_EQU2'], axis=1, inplace=True)
        df = df[['Ticker', 'dt', dataset_name]]


    elif dataset_name == 'yoy_cash':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'MONETARY_CAP', 'STATEMENT_TYPE']
        table = 'Wind.AShareBalanceSheet'
        df1 = get_wind_data(table, factor,sql_config, date - 10000)
        df1.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df1.set_index("Ticker", inplace=True)
        if df1['STATEMENT_TYPE'].dtype == 'object':
            df1["STATEMENT_TYPE"] = df1["STATEMENT_TYPE"].apply(pd.to_numeric)
        df1 = df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)

        df2 = get_wind_data(table, factor,sql_config, date)
        df2.rename(columns={"S_INFO_WINDCODE": "Ticker", "MONETARY_CAP": "MONETARY_CAP2"}, inplace=True)
        df2.set_index("Ticker", inplace=True)
        if df2['STATEMENT_TYPE'].dtype == 'object':
            df2["STATEMENT_TYPE"] = df2["STATEMENT_TYPE"].apply(pd.to_numeric)
        df2 = df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1,sort=True)

        def help(df):
            a = df['MONETARY_CAP']
            b = df['MONETARY_CAP2']
            if a == 0:
                return np.nan
            return 100 * (b - a) / abs(a)

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['MONETARY_CAP', 'MONETARY_CAP2'], axis=1, inplace=True)
        df.index.name = "Ticker"
        df.reset_index("Ticker", inplace=True)
        if isinstance(date, int):
            df['dt'] = pd.Timestamp(str(date))
        else:
            df['dt'] = date
        df = df[['Ticker', 'dt', dataset_name]]


    elif dataset_name == 'yoy_fixedassets':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'FIX_ASSETS', 'STATEMENT_TYPE']
        table = 'Wind.AShareBalanceSheet'
        df1 = get_wind_data(table, factor,sql_config, date - 10000)
        df1.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df1.set_index("Ticker", inplace=True)
        if df1['STATEMENT_TYPE'].dtype == 'object':
            df1["STATEMENT_TYPE"] = df1["STATEMENT_TYPE"].apply(pd.to_numeric)
        df1 = df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)

        df2 = get_wind_data(table, factor,sql_config, date)
        df2.rename(columns={"S_INFO_WINDCODE": "Ticker", "FIX_ASSETS": "FIX_ASSETS2"}, inplace=True)
        df2.set_index("Ticker", inplace=True)
        if df2['STATEMENT_TYPE'].dtype == 'object':
            df2["STATEMENT_TYPE"] = df2["STATEMENT_TYPE"].apply(pd.to_numeric)
        df2 = df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1,sort=True)

        def help(df):
            a = df['FIX_ASSETS']
            b = df['FIX_ASSETS2']
            if a == 0:
                return np.nan
            return 100 * (b - a) / abs(a)

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['FIX_ASSETS', 'FIX_ASSETS2'], axis=1, inplace=True)
        df.index.name = "Ticker"
        df.reset_index("Ticker", inplace=True)
        if isinstance(date, int):
            df['dt'] = pd.Timestamp(str(date))
        else:
            df['dt'] = date
        df = df[['Ticker', 'dt', dataset_name]]


    elif dataset_name == 'yoydebt':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'TOT_LIAB', 'STATEMENT_TYPE']
        table = 'Wind.AShareBalanceSheet'
        df1 = get_wind_data(table, factor,sql_config, date - 10000)
        df1.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df1.set_index("Ticker", inplace=True)
        if df1['STATEMENT_TYPE'].dtype == 'object':
            df1["STATEMENT_TYPE"] = df1["STATEMENT_TYPE"].apply(pd.to_numeric)
        df1 = df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)

        df2 = get_wind_data(table, factor,sql_config, date)
        df2.rename(columns={"S_INFO_WINDCODE": "Ticker", "TOT_LIAB": "TOT_LIAB2"}, inplace=True)
        df2.set_index("Ticker", inplace=True)
        if df2['STATEMENT_TYPE'].dtype == 'object':
            df2["STATEMENT_TYPE"] = df2["STATEMENT_TYPE"].apply(pd.to_numeric)
        df2 = df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1,sort=True)

        def help(df):
            a = df['TOT_LIAB']
            b = df['TOT_LIAB2']
            if a == 0:
                return np.nan
            return 100 * (b - a) / abs(a)

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['TOT_LIAB', 'TOT_LIAB2'], axis=1, inplace=True)
        df.index.name = "Ticker"
        df.reset_index("Ticker", inplace=True)
        if isinstance(date, int):
            df['dt'] = pd.Timestamp(str(date))
        else:
            df['dt'] = date
        df = df[['Ticker', 'dt', dataset_name]]

    elif dataset_name == 'operatecaptialturn':

        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'TOT_OPER_REV', 'STATEMENT_TYPE']
        table = 'Wind.AShareIncome'
        df1 = get_wind_data(table, factor,sql_config, date)
        df1.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df1.set_index("Ticker", inplace=True)
        if df1['STATEMENT_TYPE'].dtype == 'object':
            df1["STATEMENT_TYPE"] = df1["STATEMENT_TYPE"].apply(pd.to_numeric)
        df1 = df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)

        factor2 = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'TOT_CUR_ASSETS', 'TOT_CUR_LIAB', 'STATEMENT_TYPE']
        table2 = 'Wind.AShareBalanceSheet'
        df2 = get_wind_data(table2, factor2,sql_config, date)
        df2.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df2.set_index("Ticker", inplace=True)
        if df2['STATEMENT_TYPE'].dtype == 'object':
            df2["STATEMENT_TYPE"] = df2["STATEMENT_TYPE"].apply(pd.to_numeric)
        df2 = df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)

        date2 = (int((date - 10000) / 10000) * 10000 + 1231)
        df3 = get_wind_data(table2, factor2,sql_config, date2)
        df3.rename(
            columns={"S_INFO_WINDCODE": "Ticker", 'TOT_CUR_ASSETS': 'TOT_CUR_ASSETS2', 'TOT_CUR_LIAB': 'TOT_CUR_LIAB2'},
            inplace=True)
        df3.set_index("Ticker", inplace=True)
        if df3['STATEMENT_TYPE'].dtype == 'object':
            df3["STATEMENT_TYPE"] = df3["STATEMENT_TYPE"].apply(pd.to_numeric)
        df3 = df3[df3['STATEMENT_TYPE'] == 408001000.0]
        df3.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)
        df = pd.concat([df1, df2, df3], axis=1,sort=True)
        df.index.name = "Ticker"
        df.reset_index("Ticker", inplace=True)
        if isinstance(date, int):
            df['dt'] = pd.Timestamp(str(date))
        else:
            df['dt'] = date

        def help(df):
            a = df['TOT_OPER_REV']
            b = (df['TOT_CUR_ASSETS'] - df['TOT_CUR_LIAB'] + df['TOT_CUR_ASSETS2'] - df['TOT_CUR_LIAB2'])
            if b == 0:
                return np.nan
            return 2 * a / b

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['TOT_OPER_REV', 'TOT_CUR_ASSETS', 'TOT_CUR_LIAB', 'TOT_CUR_ASSETS2', 'TOT_CUR_LIAB2'], axis=1,
                inplace=True)
        df = df[['Ticker', 'dt', dataset_name]]

    elif dataset_name == 'apturn':

        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'LESS_OPER_COST', 'STATEMENT_TYPE']
        table = 'Wind.AShareIncome'
        df1 = get_wind_data(table, factor,sql_config, date)
        df1.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df1.set_index("Ticker", inplace=True)
        if df1['STATEMENT_TYPE'].dtype == 'object':
            df1["STATEMENT_TYPE"] = df1["STATEMENT_TYPE"].apply(pd.to_numeric)
        df1 = df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)

        factor2 = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'ACCT_PAYABLE', 'STATEMENT_TYPE']
        table2 = 'Wind.AShareBalanceSheet'
        df2 = get_wind_data(table2, factor2,sql_config, date)
        df2.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df2.set_index("Ticker", inplace=True)
        if df2['STATEMENT_TYPE'].dtype == 'object':
            df2["STATEMENT_TYPE"] = df2["STATEMENT_TYPE"].apply(pd.to_numeric)
        df2 = df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)

        date2 = (int((date - 10000) / 10000) * 10000 + 1231)
        df3 = get_wind_data(table2, factor2,sql_config, date2)
        df3.rename(columns={"S_INFO_WINDCODE": "Ticker", "ACCT_PAYABLE": "ACCT_PAYABLE2"}, inplace=True)
        df3.set_index("Ticker", inplace=True)
        if df3['STATEMENT_TYPE'].dtype == 'object':
            df3["STATEMENT_TYPE"] = df3["STATEMENT_TYPE"].apply(pd.to_numeric)
        df3 = df3[df3['STATEMENT_TYPE'] == 408001000.0]
        df3.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)
        df = pd.concat([df1, df2, df3], axis=1,sort=True)
        df.replace(0, np.nan, inplace=True)
        df.index.name = "Ticker"
        df.reset_index("Ticker", inplace=True)
        if isinstance(date, int):
            df['dt'] = pd.Timestamp(str(date))
        else:
            df['dt'] = date

        def help(df):
            a = df['LESS_OPER_COST']
            b = (df['ACCT_PAYABLE'] + df['ACCT_PAYABLE2'])
            if b == 0:
                return np.nan
            return 2 * a / b

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['LESS_OPER_COST', 'ACCT_PAYABLE', 'ACCT_PAYABLE2'], axis=1, inplace=True)
        df = df[['Ticker', 'dt', dataset_name]]

    elif dataset_name == 'yoy_assets':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'TOT_ASSETS', 'STATEMENT_TYPE']
        table = 'Wind.AShareBalanceSheet'
        df1 = get_wind_data(table, factor,sql_config, date - 10000)
        df1.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df1.set_index("Ticker", inplace=True)
        if df1['STATEMENT_TYPE'].dtype == 'object':
            df1["STATEMENT_TYPE"] = df1["STATEMENT_TYPE"].apply(pd.to_numeric)
        df1 = df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)

        df2 = get_wind_data(table, factor,sql_config, date)
        df2.rename(columns={"S_INFO_WINDCODE": "Ticker", "TOT_ASSETS": "TOT_ASSETS2"}, inplace=True)
        df2.set_index("Ticker", inplace=True)
        if df2['STATEMENT_TYPE'].dtype == 'object':
            df2["STATEMENT_TYPE"] = df2["STATEMENT_TYPE"].apply(pd.to_numeric)
        df2 = df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)

        df12 = get_wind_data(table, factor,sql_config, date - 10000)
        df12.rename(columns={"S_INFO_WINDCODE": "Ticker", "TOT_ASSETS": "TOT_ASSETS12"}, inplace=True)
        df12.set_index("Ticker", inplace=True)
        if df12['STATEMENT_TYPE'].dtype == 'object':
            df12["STATEMENT_TYPE"] = df12["STATEMENT_TYPE"].apply(pd.to_numeric)
        df12 = df12[df12['STATEMENT_TYPE'] == 408004000.0]
        df12.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)

        factor3 = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'TOT_ASSETS']
        table3 = 'Wind.AShareProfitExpress'
        df3 = get_wind_data(table3, factor3,sql_config, date - 10000)
        df3.rename(columns={"S_INFO_WINDCODE": "Ticker", "TOT_ASSETS": "TOT_ASSETS3"}, inplace=True)
        df3.set_index("Ticker", inplace=True)
        df3.drop("REPORT_PERIOD", axis=1, inplace=True)

        df4 = get_wind_data(table3, factor3,sql_config, date)
        df4.rename(columns={"S_INFO_WINDCODE": "Ticker", "TOT_ASSETS": "TOT_ASSETS4"}, inplace=True)
        df4.set_index("Ticker", inplace=True)
        df4.drop("REPORT_PERIOD", axis=1, inplace=True)
        df = pd.concat([df1, df2, df3, df4, df12], axis=1,sort=True)

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
            if a == 0:
                return np.nan
            return 100 * (b - a) / abs(a)

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['TOT_ASSETS', 'TOT_ASSETS2', 'TOT_ASSETS3', 'TOT_ASSETS4', 'TOT_ASSETS12'], axis=1, inplace=True)
        df.index.name = "Ticker"
        df.reset_index("Ticker", inplace=True)
        if isinstance(date, int):
            df['dt'] = pd.Timestamp(str(date))
        else:
            df['dt'] = date
        df = df[['Ticker', 'dt', dataset_name]]


    elif dataset_name == 'cashtostdebt':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'MONETARY_CAP', 'ST_BORROW', 'NOTES_PAYABLE', 'TRADABLE_FIN_LIAB',
                  'NON_CUR_LIAB_DUE_WITHIN_1Y', 'STATEMENT_TYPE']
        table = 'Wind.AShareBalanceSheet'
        df = get_wind_data(table, factor,sql_config, date)
        df.rename(columns={"S_INFO_WINDCODE": "Ticker", "REPORT_PERIOD": "dt"}, inplace=True)
        df.set_index(["dt", "Ticker"], inplace=True)
        if df['STATEMENT_TYPE'].dtype == 'object':
            df["STATEMENT_TYPE"] = df["STATEMENT_TYPE"].apply(pd.to_numeric)
        df = df[df['STATEMENT_TYPE'] == 408001000.0]
        df.drop('STATEMENT_TYPE', axis=1, inplace=True)

        def help(df):
            a = df['MONETARY_CAP']
            try:
                b = (df['ST_BORROW'] + df['NOTES_PAYABLE'] + df['TRADABLE_FIN_LIAB'] + df['NON_CUR_LIAB_DUE_WITHIN_1Y'])
            except Exception as e:
                return np.nan
            if b == 0:
                return np.nan
            return a / b

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['MONETARY_CAP', 'ST_BORROW', 'NOTES_PAYABLE', 'TRADABLE_FIN_LIAB', 'NON_CUR_LIAB_DUE_WITHIN_1Y'],
                axis=1, inplace=True)
        df.reset_index(inplace=True)
        df = df[['Ticker', 'dt', dataset_name]]


    elif dataset_name == 'ocftointerest':
        factor1 = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'NET_CASH_FLOWS_OPER_ACT', 'STATEMENT_TYPE']
        table1 = 'Wind.AShareCashFlow'
        df1 = get_wind_data(table1, factor1,sql_config, date)
        df1.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df1.set_index("Ticker", inplace=True)
        if df1['STATEMENT_TYPE'].dtype == 'object':
            df1["STATEMENT_TYPE"] = df1["STATEMENT_TYPE"].apply(pd.to_numeric)
        df1 = df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)
        list_check = []
        for index in df1.index.values:
            if not index in list_check:
                list_check.append(index)
            else:
                df1.drop(index, axis=0, inplace=True)
        factor2 = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'S_STMNOTE_FINEXP']
        table2 = 'Wind.AShareFinancialIndicator'
        df2 = get_wind_data(table2, factor2,sql_config, date)
        df2.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df2.set_index("Ticker", inplace=True)
        df2.drop("REPORT_PERIOD", axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1,sort=True)
        for i in df.index.values:
            if df.loc[i,'S_STMNOTE_FINEXP'] == 0 or pd.isnull(df.loc[i,'S_STMNOTE_FINEXP']):
                df.loc[i,'S_STMNOTE_FINEXP'] = np.nan
        df[dataset_name] = df.apply(lambda x: x['NET_CASH_FLOWS_OPER_ACT'] / x['S_STMNOTE_FINEXP'], axis=1)
        df.drop(['NET_CASH_FLOWS_OPER_ACT', 'S_STMNOTE_FINEXP'], axis=1, inplace=True)
        df.index.name = "Ticker"
        df.reset_index("Ticker", inplace=True)
        if isinstance(date, int):
            df['dt'] = pd.Timestamp(str(date))
        else:
            df['dt'] = date
        df = df[['Ticker', 'dt', dataset_name]]

    elif dataset_name == 'ocftodividend':
        factor1 = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'NET_CASH_FLOWS_OPER_ACT', 'STATEMENT_TYPE']
        table1 = 'Wind.AShareCashFlow'
        df1 = get_wind_data(table1, factor1,sql_config, date)
        df1.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df1.set_index("Ticker", inplace=True)
        if df1['STATEMENT_TYPE'].dtype == 'object':
            df1["STATEMENT_TYPE"] = df1["STATEMENT_TYPE"].apply(pd.to_numeric)
        df1 = df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)
        list_check = []
        for index in df1.index.values:
            if not index in list_check:
                list_check.append(index)
            else:
                df1.drop(index, axis=0, inplace=True)
        factor2 = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'COMSHARE_DVD_PAYABLE', 'STATEMENT_TYPE']
        table2 = 'Wind.AShareIncome'
        df2 = get_wind_data(table2, factor2,sql_config, date)
        df2.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df2.set_index("Ticker", inplace=True)
        if df2['STATEMENT_TYPE'].dtype == 'object':
            df2["STATEMENT_TYPE"] = df2["STATEMENT_TYPE"].apply(pd.to_numeric)
        df2 = df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1,sort=True)
        for i in df.index.values:
            if df.loc[i,'COMSHARE_DVD_PAYABLE'] == 0 or pd.isnull(df.loc[i,'COMSHARE_DVD_PAYABLE']):
                df.loc[i,'COMSHARE_DVD_PAYABLE'] = np.nan
        df[dataset_name] = df.apply(lambda x: x['NET_CASH_FLOWS_OPER_ACT'] / x['COMSHARE_DVD_PAYABLE'], axis=1)
        df.drop(['NET_CASH_FLOWS_OPER_ACT', 'COMSHARE_DVD_PAYABLE'], axis=1, inplace=True)
        df.index.name = "Ticker"
        df.reset_index("Ticker", inplace=True)
        if isinstance(date, int):
            df['dt'] = pd.Timestamp(str(date))
        else:
            df['dt'] = date
        df = df[['Ticker', 'dt', dataset_name]]

    elif dataset_name == 'yoyprofit':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'NET_PROFIT_INCL_MIN_INT_INC', 'STATEMENT_TYPE']
        table = 'Wind.AShareIncome'
        df1 = get_wind_data(table, factor,sql_config, date - 10000)
        df1.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df1.set_index("Ticker", inplace=True)
        if df1['STATEMENT_TYPE'].dtype == 'object':
            df1["STATEMENT_TYPE"] = df1["STATEMENT_TYPE"].apply(pd.to_numeric)
        df1 = df1[df1['STATEMENT_TYPE'] == 408001000.0]
        df1.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)
        list_check = []
        for index in df1.index.values:
            if not index in list_check:
                list_check.append(index)
            else:
                df1.drop(index, axis=0, inplace=True)
        df2 = get_wind_data(table, factor,sql_config, date)
        df2.rename(columns={"S_INFO_WINDCODE": "Ticker", "NET_PROFIT_INCL_MIN_INT_INC": "NET_PROFIT_INCL_MIN_INT_INC2"},
                   inplace=True)
        df2.set_index("Ticker", inplace=True)
        if df2['STATEMENT_TYPE'].dtype == 'object':
            df2["STATEMENT_TYPE"] = df2["STATEMENT_TYPE"].apply(pd.to_numeric)
        df2 = df2[df2['STATEMENT_TYPE'] == 408001000.0]
        df2.drop(['STATEMENT_TYPE', 'REPORT_PERIOD'], axis=1, inplace=True)
        list_check = []
        for index in df2.index.values:
            if not index in list_check:
                list_check.append(index)
            else:
                df2.drop(index, axis=0, inplace=True)

        df = pd.concat([df1, df2], axis=1,sort=True)

        def help(df):
            a = df['NET_PROFIT_INCL_MIN_INT_INC']
            b = df['NET_PROFIT_INCL_MIN_INT_INC2']
            if a == 0:
                return np.nan
            return 100 * (b - a) / abs(a)

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['NET_PROFIT_INCL_MIN_INT_INC', 'NET_PROFIT_INCL_MIN_INT_INC2'], axis=1, inplace=True)
        df.index.name = "Ticker"
        df.reset_index("Ticker", inplace=True)
        if isinstance(date, int):
            df['dt'] = pd.Timestamp(str(date))
        else:
            df['dt'] = date
        df = df[['Ticker', 'dt', dataset_name]]

    elif dataset_name == 'yoycf':
        factor = ['S_INFO_WINDCODE', 'REPORT_PERIOD', 'S_FA_CFPS', 'TOT_SHR']
        table = 'Wind.AShareFinancialIndicator'
        df1 = get_wind_data(table, factor,sql_config, date - 10000)
        df1.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
        df1.set_index("Ticker", inplace=True)
        df1.drop("REPORT_PERIOD", axis=1, inplace=True)

        df2 = get_wind_data(table, factor,sql_config, date)
        df2.rename(columns={"S_INFO_WINDCODE": "Ticker", "S_FA_CFPS": "S_FA_CFPS2", "TOT_SHR": "TOT_SHR2"},
                   inplace=True)
        df2.set_index("Ticker", inplace=True)
        df2.drop("REPORT_PERIOD", axis=1, inplace=True)
        df = pd.concat([df1, df2], axis=1,sort=True)

        def help(df):
            a = df['S_FA_CFPS'] * df['TOT_SHR']
            b = df['S_FA_CFPS2'] * df['TOT_SHR2']
            if a == 0:
                return np.nan
            return 100 * (b - a) / abs(a)

        df[dataset_name] = df.apply(lambda x: help(x), axis=1)
        df.drop(['S_FA_CFPS', 'TOT_SHR', 'S_FA_CFPS2', 'TOT_SHR2'], axis=1, inplace=True)
        df.index.name = "Ticker"
        df.reset_index("Ticker", inplace=True)
        if isinstance(date, int):
            df['dt'] = pd.Timestamp(str(date))
        else:
            df['dt'] = date
        df = df[['Ticker', 'dt', dataset_name]]

    return df

