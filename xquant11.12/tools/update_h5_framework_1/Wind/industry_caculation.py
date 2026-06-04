# _*_ coding:utf-8 _*_
from Wind.utils import *
import pandas as pd

def industry_retriever(sql_config,cdate_list,date,factor_name):
    industry_code = ['b10100', 'b10200', 'b10300', 'b10400', 'b10500', 'b10600',
        'b10700', 'b10800', 'b10900', 'b10a00', 'b10b00', 'b10c00',
        'b10d00', 'b10e00', 'b10f00', 'b10g00', 'b10h00', 'b10i00',
        'b10j00', 'b10k00', 'b10l00', 'b10n00', 'b10o00', 'b10p00',
        'b10q00', 'b10r00', 'b10s00', 'b10t00','b10m01', 'b10m02', 'b10m03']
    map_dict = {29: 6, 30: 7, 31: 8, 21: 1, 27: 2, 24: 2, 26: 2, 25: 2, 5: 3, 2: 3, 3: 3, 19: 4, 18: 4, 15: 5, 4: 5,
                11: 5, 22: 5, 17: 5,12: 5, 10: 5, 6: 5, 16: 5, 8: 5, 7: 5, 23: 5, 20: 5, 13: 5, 9: 5, 14: 5, 1: 5, 28: 5}

    industry_num = [i+1 for i in range(len(industry_code))]
    industry_dict = dict(zip(industry_code,industry_num))

    factor = ['S_INFO_WINDCODE', 'CITICS_IND_CODE','ENTRY_DT','REMOVE_DT']
    table_name = 'Wind.AShareIndustriesClassCITICS'
    df = get_wind_data(table_name,factor,sql_config,date)
    df.rename(columns={"S_INFO_WINDCODE":"Ticker"},inplace=True)
    df["dt"] = pd.Timestamp(str(date))
    if df['REMOVE_DT'].dtype == 'object':
        df['REMOVE_DT'] = df['REMOVE_DT'].apply(pd.to_numeric)
    if df['ENTRY_DT'].dtype == 'object':
        df['ENTRY_DT'] = df['ENTRY_DT'].apply(pd.to_numeric)
    df['REMOVE_DT'].fillna(20990101,inplace=True)
    df = df[(df['ENTRY_DT']<=date) & (df['REMOVE_DT']>=date)]
    def industry_parser(ind_code):
        ind2 = ind_code[:6]
        if 'b10m' in ind2:
            ind_lv2_code = ind2
        else:
            ind_lv2_code = ind2[:4] + '00'
        return ind_lv2_code
    df['lv2_ind_code'] = df['CITICS_IND_CODE'].apply(industry_parser)
    df['lv2_ind_num'] = df['lv2_ind_code'].apply(lambda x:industry_dict[x])
    df.drop(['CITICS_IND_CODE','ENTRY_DT','REMOVE_DT', 'lv2_ind_code', 'lv2_ind_code'], axis=1, inplace=True)
    df.rename(columns={"lv2_ind_num":"CITIC_I"},inplace=True)

    df["KNN_I"] = df["CITIC_I"].map(map_dict)
    df.loc[:, "KNN_I"].fillna(-1, inplace=True)
    df.reset_index(inplace = True)
    df = df[['Ticker', 'dt', 'CITIC_I','KNN_I']]
    return df




