import pandas as pd
import os
import json
from AutoMiningFrame.DataCaculation.entry.FactorCalcBatch import calc_factors_by_config,calc_per_factor_by_file
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from xquant.factordata import FactorData
import json
import dolphindb as ddb
fd = FactorData()
import sys

def calc_and_save_factors(config_path, file_path, start_date, end_date, target_securities, non_factor_path, return_mode='show', study_scenario='stock', data_type='enhanced_tick'):
    calc_data_type = data_type
    save_data_type = data_type
    
    if data_type == 'enhanced_tick_norm':
        calc_data_type = 'enhanced_tick'
        save_data_type = 'enhanced_tick_norm'    
    fp = FactorProvider()
    sh_config_path = "factor_config_enhanced_tick_norm_sh.json"
    se_config_path = "factor_config_enhanced_tick_norm_se.json"
    sh_config_file = os.path.join(config_path, sh_config_path)
    se_config_file = os.path.join(config_path, se_config_path)
    
    sh_stocks = [i for i in target_securities if i.endswith(".SH")]
    se_stocks = [i for i in target_securities if i.endswith(".SZ")]
    if len(sh_stocks)>0:
        sh_res = calc_factors_by_config(sh_config_file, file_path, start_date, end_date, sh_stocks, return_mode=return_mode, non_factor_path=non_factor_path, study_scenario=study_scenario, data_type=calc_data_type)
        print(sh_res.head())
        for stock in sh_stocks:
            sh_res_temp = sh_res[sh_res['M_HTSCSecurityID']==stock]
            if sh_res_temp.shape[0]>0:
                fp.save_public_data_to_dfs(sh_res_temp, factor_type='factor', data_type=save_data_type)

    if len(se_stocks)>0:
        se_res = calc_factors_by_config(se_config_file, file_path, start_date, end_date, se_stocks, return_mode=return_mode, non_factor_path=non_factor_path, study_scenario=study_scenario, data_type=calc_data_type)
        print(se_res.head())
        for stock in se_stocks:
            se_res_temp = se_res[se_res['M_HTSCSecurityID']==stock]
            if se_res_temp.shape[0]>0:
                fp.save_public_data_to_dfs(se_res_temp, factor_type='factor', data_type=save_data_type)
    return

# 生成配置文件
def gen_configs(config_path,file_path, factor_list=None):
    a = open(os.path.join(config_path,"factor_config_enhanced_tick_norm_se.json"),'w')
    res_dict = {}
    for root,dir,files in os.walk(file_path):
        for file in files:
            if factor_list:
                if file[:-4] not in factor_list:
                    continue
            contents = open(os.path.join(root,file),"r").read()
            #if file.startswith("FactorT") and file[7].isupper():
            #    continue
            if "M_NumOfferOrders" in contents or "M_NumBidOrders" in contents or "M_Withdraw" in contents or "TotalBidNumber" in contents or "TotalOfferNumber" in contents or "BidTradeMaxDuration" in contents or "OfferTradeMaxDuration" in contents:
                continue
            if file.endswith(".dos"):
                res_dict[file[:-4]] = [{}]
    a.write(json.dumps(res_dict))

    b = open(os.path.join(config_path, "factor_config_enhanced_tick_norm_sh.json"),'w')
    res_dict = {}
    for root,dir,files in os.walk(file_path):
        for file in files:
            if factor_list:
                if file[:-4] not in factor_list:
                    continue
            contents = open(os.path.join(root,file),"r").read()
            if file.endswith(".dos"):
                res_dict[file[:-4]] = [{}]
    b.write(json.dumps(res_dict))
    return

def get_stock_list():
    s = ddb.session()
    s.connect("168.17.250.49", 8902, 'admin', '123456')
    dbname="dfs://CustomData/sz_stock_tick_enhanced"
    tbname = "sz_stock_tick_enhanced"
    se_stocks = s.run(f"""
    dbname = '{dbname}'
    tbname = `{tbname}
    stocks = exec distinct(M_HTSCSecurityID) from loadTable(dbname, tbname)
    stocks
    """)
    se_stocks = list(se_stocks)

    dbname="dfs://CustomData/sh_stock_tick_enhanced"
    tbname = "sh_stock_tick_enhanced"
    sh_stocks = s.run(f"""
    dbname = '{dbname}'
    tbname = `{tbname}
    stocks = exec distinct(M_HTSCSecurityID) from loadTable(dbname, tbname)
    stocks
    """)
    sh_stocks = list(sh_stocks)
    stocks = se_stocks+sh_stocks
    return stocks


def main(start_date, end_date, target_securities,factor_list=None):
    
    file_path = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-2]), "factors/norm_factors/new_factors")
    non_factor_path = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-2]), "factors/norm_factors/new_non_factors")
    config_path = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-2]), "data_update")
    gen_configs(config_path, file_path,factor_list)    
    calc_and_save_factors(config_path, file_path, start_date, end_date, target_securities, non_factor_path, return_mode='show', study_scenario='stock', data_type='enhanced_tick_norm')
    return

if __name__ == "__main__":
    import time
    factor_list = ['FactorNSWMountValleyWeightMidPx', 'FactorNSWOrderNumRatioTrend', 'FactorNSWOrderWeightRatioTrend', 'FactorNSWOrderWeightRatioCount', 'FactorNSWOrderBuyWeightRatioTrend', 'FactorNSWBuySellOrderDeltaAmountRatio', 'FactorNSWBuyWeightPriceSkew', 'FactorNSWSellOrderQtySkew', 'FactorNSWOrderNumRatio', 'FactorNSWSellOrderExRet', 'FactorNSWBuyOrderExRet', 'FactorNSWActiveSmallBuyAmtStrength', 'FactorNSWSellAmtPreTradeMA', 'FactorNSWBuyAmtPreTradeMA', 'FactorNSWBuyOrderPriceRetCorr']
    target_securities = sorted(get_stock_list())
    start_month_list = sorted([str(i)+"0101" for i in range(2020,2025)]+[str(i)+"0701" for i in range(2020,2025)])
    end_month_list = sorted([str(i)+"0630" for i in range(2020,2025)]+[str(i)+"1231" for i in range(2020,2025)])
    month_list = sorted(list(set(zip(start_month_list,end_month_list))))
    for stock in target_securities:
        print(stock, target_securities.index(stock)/len(target_securities))
        for start_date,end_date in month_list:
            try:
  
                main(start_date, end_date, [stock],factor_list)
            except:
                print("{} {} {} 无数据".format(stock,start_date,end_date))
