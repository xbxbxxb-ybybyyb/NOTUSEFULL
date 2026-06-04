import pandas as pd
import os
import json
from AutoMiningFrame.DataCaculation.entry.FactorCalcBatch import calc_factors_by_config,calc_per_factor_by_file
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from xquant.factordata import FactorData
import json
fd = FactorData()
import sys

def calc_and_save_factors(config_path, file_path, start_date, end_date, target_securities, non_factor_path, return_mode='show', study_scenario='stock', data_type='enhanced_tick'):
    
    fp = FactorProvider()
    sh_config_path = "factor_config_enhanced_tick_sh.json"
    se_config_path = "factor_config_enhanced_tick_se.json"
    sh_config_file = os.path.join(config_path, sh_config_path)
    se_config_file = os.path.join(config_path, se_config_path)
    
    sh_stocks = [i for i in target_securities if i.endswith(".SH")]
    se_stocks = [i for i in target_securities if i.endswith(".SZ")]
    if len(sh_stocks)>0:
        sh_res = calc_factors_by_config(sh_config_file, file_path, start_date, end_date, sh_stocks, return_mode=return_mode, non_factor_path=non_factor_path, study_scenario=study_scenario, data_type=data_type)
        print(sh_res.head())
        for stock in sh_stocks:
            sh_res_temp = sh_res[sh_res['M_HTSCSecurityID']==stock]
            if sh_res_temp.shape[0]>0:
                fp.save_public_data_to_dfs(sh_res_temp, factor_type='factor', data_type=data_type)

    if len(se_stocks)>0:
        se_res = calc_factors_by_config(se_config_file, file_path, start_date, end_date, se_stocks, return_mode=return_mode, non_factor_path=non_factor_path, study_scenario=study_scenario, data_type=data_type)
        print(se_res.head())
        for stock in se_stocks:
            se_res_temp = se_res[se_res['M_HTSCSecurityID']==stock]
            if se_res_temp.shape[0]>0:
                fp.save_public_data_to_dfs(se_res_temp, factor_type='factor', data_type=data_type)
    return

# 生成配置文件
def gen_configs(config_path,file_path):
    a = open(os.path.join(config_path,"factor_config_enhanced_tick_se.json"),'w')
    res_dict = {}
    for root,dir,files in os.walk(file_path):
        for file in files:
            contents = open(os.path.join(root,file),"r").read()
            #if file.startswith("FactorT") and file[7].isupper():
            #    continue
            if "M_NumOfferOrders" in contents or "M_NumBidOrders" in contents or "M_Withdraw" in contents or "TotalBidNumber" in contents or "TotalOfferNumber" in contents or "BidTradeMaxDuration" in contents or "OfferTradeMaxDuration" in contents:
                continue
            if file.endswith(".dos"):
                res_dict[file[:-4]] = [{}]
    a.write(json.dumps(res_dict))

    b = open(os.path.join(config_path, "factor_config_enhanced_tick_sh.json"),'w')
    res_dict = {}
    for root,dir,files in os.walk(file_path):
        for file in files:
            #if file.startswith("FactorT") and file[7].isupper():
            #    continue
            contents = open(os.path.join(root,file),"r").read()
            if file.endswith(".dos"):
                res_dict[file[:-4]] = [{}]
    b.write(json.dumps(res_dict))
    return


def main(start_date, end_date, target_securities):
    
    file_path = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-2]), "factors/all/all_factors")
    non_factor_path = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-2]), "factors/all/all_non_factors")
    config_path = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-2]), "data_update")
    gen_configs(config_path, file_path)    
    calc_and_save_factors(config_path, file_path, start_date, end_date, target_securities, non_factor_path, return_mode='show', study_scenario='stock', data_type='enhanced_tick')
    return

if __name__ == "__main__":
    import time
    #target_securities = pd.read_excel("stocks_new.xlsx")['stock'].values.tolist()
    #target_securities = pd.read_excel("All_dol.xlsx",header=None)[0].values.tolist()
    #having_stocks = pd.read_csv("having_sz_stocks.csv")['distinct_M_HTSCSecurityID'].values.tolist()
    #target_securities = sorted(list(set(set(target_securities)-set(having_stocks))))[::-1]
    #start_date_list = sorted([str(i)+"0101" for i in range(2020,2024)]+[str(i)+"0701" for i in range(2020,2024)]) 
    #end_date_list = sorted([str(i)+"0630" for i in range(2020,2024)]+[str(i)+"1231" for i in range(2020,2024)]) 
    #date_list = sorted(list(set(zip(start_date_list, end_date_list))))
    #for stock in target_securities:    
    #    print(stock, target_securities.index(stock), len(target_securities))
    #    for sd,ed in date_list:
    #        try:
    #            start= time.time()
    #            print(sd, ed)
    #            main(target_securities=[stock], start_date=sd, end_date=ed)
    #            end = time.time()
    #            print("total cost :{}".format(end-start))
    #        except:
    #            #raise Exception()
    #            continue
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--target_securities', nargs="+", default="688599.SH", type=str, help='input the stock list')
    parser.add_argument('-s', '--start_date', default="20200301", type=str, help='input the start date')
    parser.add_argument('-e', '--end_date', default="20230301", type=str, help='input the end date')
    parser.add_argument('-f', '--factor_list', nargs="+", default=None, type=str, help='input the factor list')
    args = parser.parse_args()
    start_date = args.start_date
    end_date = args.end_date
    factor_list = args.factor_list
    target_securities = args.target_securities
    assert target_securities, "target_securities 不能为空"
    assert type(start_date)==str, "开始日期不为空，且必须是str"
    assert type(end_date)==str, "结束日期不为空，且必须是str"
    main(start_date, end_date, target_securities)

