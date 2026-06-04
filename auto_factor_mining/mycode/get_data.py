#encoding=utf-8
import pandas as pd
import copy
import numpy as np
import tqdm
from tqdm import tqdm
from xquant.factordata import FactorData
import time
import argparse
import json
import sys 
sys.path.append("./gplearn_my/")
sys.path.append("./gplearn_my/tests")
from gplearn_my.customized_utils import Normalization2


s = FactorData()

def get_factor_data(stock_list, trading_day, factor, save_path = ""):
    """
        获取大数据集
        Parameters
        ----------
        stock_list: list 
            Record each stock code by string format
        trading_day: list
            Record trading day by int or string format [20220729, ....]    
        factor: list
            Record all needed factors by string, notice that the factor names should be valid in Xqaunt
        save_path: string
            The path where save the all_data_parquet
    """

    # 这两样是计算oneday return 的必须项， 除非制定其他 预测标的（需要改代码），否则需要这两项
    factor_names = ['vwap', 'adjfactor'] + factor
    df1 = s.get_factor_value('Basic_factor', stock_list, mddate= trading_day, 
                             factor_names = factor_names, fill_na=True).reset_index()
    
    df1['vwap_badj'] = df1['vwap'] * df1['adjfactor']
    if "swing" in factor_names:
        df1['swing'] *= 100
    stock_list = list(set(df1['stock'])) 
    print('数据总数: %d 股票总数: %d 交易日总数：%d'  %(len(df1), len(stock_list), len(trading_day)))  
    df1.replace([np.inf, -np.inf], np.nan, inplace=True)
    df1 = df1.fillna(0)
    df1 = df1[['mddate','stock','vwap_badj'] + list(df1.columns.values[3:-1])]
    
    df = pd.DataFrame()
    print("1DayReturn计算：")
    for i in tqdm(range(len(stock_list))):
        tmp = df1[df1['stock'] == stock_list[i]]
        tmp = tmp.sort_values(['mddate'])
        tmp['1Day_return'] = tmp['vwap_badj'].pct_change(1).shift(-2).iloc[:-2]
        df = df.append(tmp) 
        
    df = df.sort_values(['mddate','stock'])
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df = df.fillna(0)
    df = df.set_index(['mddate','stock'])
    if save_path != "":
        df.to_parquet(save_path)
    return df



def get_industry_code(stock_list, one_day):
    """
        获取股票行业分布，one-hot格式， 只能传入一天
        Parameters
        ----------
        stock_list: list 
            Record each stock code by string format
        one_day: string or int
            Sample day for assign industry to stock, and keep it same through time period
        decap_file_sw: DataFrame
            stock industry info by the format of one hot dataframe
               stock  code_6101  code_6102  ...  code_6132  code_6133  code_6134
    0  000416.SZ          0          0  ...          0          0          1
    1  000610.SZ          0          0  ...          0          0          0
    2  000663.SZ          0          0  ...          0          0          0
    """
    df = s.hsi(stock_list, one_day, 'SW', 1) # SW一级行业 默认不过滤NAN值
    df['industry_code'] = "code_" + df['industry_code']
    dic_sw = df.drop(columns=['industry_type','industry_name']).set_index('stock').to_dict()['industry_code']
    all_industry = ['code_6101', 'code_6102', 'code_6103', 'code_6104', 'code_6105', 'code_6108', 'code_6111', 'code_6112', 'code_6113', 'code_6114', 'code_6115', 'code_6116', 'code_6117', 'code_6118', 'code_6120', 'code_6121', 'code_6123', 'code_6124', 'code_6125', 'code_6126', 'code_6127', 'code_6128', 'code_6129', 'code_6130', 'code_6131', 'code_6132', 'code_6133', 'code_6134']

    decap_file_sw = pd.DataFrame()
    decap_file_sw["stock"] = dic_sw.keys()
    for industry in all_industry:
        tmp = []
        for key in dic_sw.keys():
            if dic_sw[key] == industry:
                tmp.append(1)
            else:
                tmp.append(0)
        decap_file_sw[industry] = tmp
    return decap_file_sw


def get_norm_size(stock_list, trading_day):
    """
        从xquant获取市值数据并处理成norm_size
        Parameters
        ----------
        stock_list: list 
            Record each stock code by string format
        one_day: string or int
            Sample day for assign industry to stock, and keep it same through time period
        norm_size_df: DataFrame
            Recode norm size which is used for y_pred_resi
    """
    size = s.get_factor_value('Basic_factor', stock_list, 
                                 mddate= trading_day, 
                                 factor_names = ['mkt_cap_ard'], fill_na=True)
    size = size.unstack(level = 1)
    size.columns = size.columns.droplevel(0)
    size = np.log(size)
    normalizer = Normalization2(axis=0)#标准化类的实例化,先处理极值再进行标准化处理（减去均值再除以标准差）
    norm_size = normalizer.norm_dataframe(size)
    norm_size_df = pd.DataFrame(norm_size.unstack()).rename(columns={0:"norm_size"}).reset_index()
    norm_size_df.rename(columns={'level_0':'stock', 'level_1':'mddate'},inplace=True)
    norm_size_df['mddate'] = norm_size_df['mddate'].astype("int64")
    norm_size_df = norm_size_df.sort_values(by = ['mddate','stock'])
    norm_size_df.set_index(['mddate', 'stock'], inplace=True)
    return norm_size_df



def make_decap(trading_day, stock_list, stock_sample_day, save_path = ""):
    """
        获取decap_file, 含有每个股票行业信息，每日是否合法，每日的中性化基准
        Parameters
        ----------
        stock_list: list 
            Record each stock code by string format
        trading_day: list
            Record trading day by int or string format [20220729, ....]    
        stock_sample_day: string or int
            Sample day for assign industry to stock, and keep it same through time period      
        save_path: string 
            The path where save the all_data_parquet
    """
    decap = pd.DataFrame()
    decap_file_sw = get_industry_code(stock_list, stock_sample_day)
    for i in tqdm(range(len(trading_day))):
        daily_filter = list(s.stock_filter(stock_list, trading_day[i], 'SSO')["stock"]) # 过滤每日停牌，开盘涨停，stpt股
        tmp = decap_file_sw.copy()
        tmp['mddate'] = [trading_day[i]] * len(decap_file_sw)
        tmp['valid']  = tmp['stock'].apply(lambda x: True if x in daily_filter else False)
        decap = pd.concat([decap, tmp])
        
    decap["mddate"] = decap["mddate"].astype("int64")    
    decap = decap.set_index(["mddate","stock"])
    norm_size = get_norm_size(stock_list, trading_day)
    #
    try:
        assert len(decap) == len(norm_size)
    except:
        print("ERROR! 数据长度不等", len(decap) , len(norm_size) )
    decap['norm_size'] = list(norm_size['norm_size'])  
    print('数据总数: %d 股票总数: %d 交易日总数：%d'  %(len(decap), len(stock_list), len(trading_day)))  
    if save_path != "":
        decap.to_parquet(save_path)
    return decap

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--save_path", help="please specify save_path")
    parser.add_argument("--json_path", help="please specify json_path")
    args = parser.parse_args()

    save_path = str(args.save_path).strip()
    json_path = str(args.json_path).strip()

    with open(json_path, 'r') as f:
        setup_json = json.load(f)
        f.close()

    # --save_path "../data/" --json_path "../setup/data_config/1.json"

    trading_day = s.tradingday(setup_json['time_sta'], setup_json['time_end'])
    # stock_list = list(s.hset('MARKET', setup_json['stock_sample_day'],'ALLA_HIS')['stock'])
    # 股票池包含hs300、zz500、zz1000、sz50
    stock_list = list(s.hset('INDEX', setup_json['stock_sample_day'], 'ZZ500')['stock']) \
                 + list(s.hset('INDEX', setup_json['stock_sample_day'], 'ZZ1000')['stock']) \
                 + list(s.hset('INDEX', setup_json['stock_sample_day'], 'HS300')['stock']) \
                 + list(s.hset('INDEX', setup_json['stock_sample_day'], 'SZ50')['stock'])

    start_time = time.time()
    decap_save_path = save_path+"decap_file.parquet"
    decap = make_decap(trading_day, stock_list, setup_json['stock_sample_day'], decap_save_path)
    print("save decap_file to {} , consume time = {} s" .format(decap_save_path, time.time() - start_time))

    start_time = time.time()
    data_save_path = save_path + "all_data.parquet"
    data = get_factor_data(stock_list, trading_day, setup_json['factor_name'], data_save_path)
    print("save all_data to {} , consume time = {} s" .format(data_save_path, time.time() - start_time))