# -*- encoding=utf-8 -*-
import math
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta
import numpy as np

    
def factors2df(data):
    """
    将量化分析平台上获取的因子数据，转化为dataframe格式
    **参数**
            data：量化分析平台上的获取的因子数据
            
    **返回**
            
            将因子转化为multiIndex格式的DataFrame
    """
    stock_code = data[2]
    date = data[1]
    print(date)

    multi = pd.MultiIndex.from_product([date,stock_code])
    df = pd.DataFrame(index=multi)
    df.index.names = ['dateTime','symbol']
    factor = []
    for stru in data[0]:
        df[stru[0]] = [0.0]*len(df)
        for sidx, stock_factor in enumerate(stru[1]):
            for didx, day_factor in enumerate(stock_factor):
                df.loc[date[didx],stock_code[sidx]].loc[stru[0]] = day_factor
    return df

    

def multi2single(multi_df):
    """
    将multiindex的DataFrame转化为DataFrame
    """
    indexs = multi_df.index.levels[0]
    columns = multi_df.index.levels[1]
    df = pd.DataFrame(index = indexs, columns = columns)
    for (mindex, row) in multi_df.iterrows():
        df.loc[mindex[0], mindex[1]] = row.iloc[0]
        
    return df

def get_Previousyear(date):
    '''
    获取前一年、两年、三年的日期
    :param end_date:
    :return:
    '''
    day = dt.datetime.strptime(str(date), "%Y%m%d")
    start_date_list = [
        (day + relativedelta(months=-36)).strftime("%Y%m%d"),
        (day + relativedelta(months=-24)).strftime("%Y%m%d"),
        (day + relativedelta(months=-12)).strftime("%Y%m%d"),
    ]
    return start_date_list


def fill_na(close_data, position_bases, startTime):
    """
    若初始持仓存在停牌股，获取最后停牌时的收盘价。
    参数：
    close_data: 股票池中股票的收盘价，DataFrame，行为时间，列为股票名
    position_bases：初始持仓，dict，key为股票名，value是持仓数量
    startTime：回测开始时间
    fa：Factor
    """
    from xquant.thirdpartydata.factor import FactorData
    fa = FactorData(timeout=60 * 3)
    if position_bases:
        # 剔除停牌股
        stock_universe = list(set(close_data.columns[np.where(np.isnan(close_data))[1]].tolist()))
        die_universe = []
        for position_base in position_bases:
            if position_base in stock_universe:
                end = startTime
                for start in get_Previousyear(startTime):
                    flag_ = 0
                    factor_history = fa.getSimpleFactorData(["pre_close"], (start, end), [position_base])
                    end = start
                    factor_values = []
                    for i, df in factor_history.iterrows():
                        factor_values.append(df[position_base])
                    factor_values = factor_values[::-1]
                    for factor_value in factor_values:
                        if not math.isnan(factor_value):
                            d = dict(close_data.iloc[0])
                            d[position_base] = factor_value
                            close_data.iloc[0] = pd.Series(d)
                            flag_ = 1
                            break
                    if flag_:
                        break
                    if not flag_:
                        die_universe.append(position_base)
        if die_universe:
            import sys
            print(str(list(set(die_universe))) + "股票停牌时间过长，建议踢出股票池！")
            sys.exit()
    close_data = close_data.fillna(method="ffill")
    return close_data
    


        
    
    