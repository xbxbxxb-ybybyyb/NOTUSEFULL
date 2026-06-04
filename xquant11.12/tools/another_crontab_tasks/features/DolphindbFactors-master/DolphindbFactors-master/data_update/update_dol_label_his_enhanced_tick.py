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
    sh_config_path = "label_config_enhanced_tick_sh.json"
    se_config_path = "label_config_enhanced_tick_se.json"
    sh_config_file = os.path.join(config_path, sh_config_path)
    se_config_file = os.path.join(config_path, se_config_path)
    
    sh_stocks = [i for i in target_securities if i.endswith("SH")]
    se_stocks = [i for i in target_securities if i.endswith("SZ")]
    if len(sh_stocks)>0:
        sh_res = calc_factors_by_config(sh_config_file, file_path, start_date, end_date, sh_stocks, return_mode=return_mode, non_factor_path=non_factor_path, study_scenario=study_scenario, data_type=data_type)
        print(sh_res.shape)
        for stock in sh_stocks:
            sh_res_temp = sh_res[sh_res['M_HTSCSecurityID']==stock]
            if sh_res_temp.shape[0]>0:
                fp.save_public_data_to_dfs(sh_res_temp, factor_type='label', data_type=data_type)
    if len(se_stocks)>0:
        se_res = calc_factors_by_config(se_config_file, file_path, start_date, end_date, se_stocks, return_mode=return_mode, non_factor_path=non_factor_path, study_scenario=study_scenario, data_type=data_type)
        print(se_res.shape)
        for stock in se_stocks:
            se_res_temp = se_res[se_res['M_HTSCSecurityID']==stock]
            if se_res_temp.shape[0]>0:
                fp.save_public_data_to_dfs(se_res_temp, factor_type='label', data_type=data_type)
    return

# 生成配置文件
def gen_configs(config_path,file_path):
    a = open(os.path.join(config_path,"label_config_enhanced_tick_se.json"),'w')
    res_dict = {}
    for root,dir,files in os.walk(file_path):
        for file in files:
            contents = open(os.path.join(root,file),"r").read()
            if "M_NumOfferOrders" in contents or "M_NumBidOrders" in contents or "M_Withdraw" in contents or "TotalBidNumber" in contents or "TotalOfferNumber" in contents or "BidTradeMaxDuration" in contents or "OfferTradeMaxDuration" in contents:
                continue
            if file.endswith(".dos"):
                res_dict[file[:-4]] = [{}]
    a.write(json.dumps(res_dict))

    b = open(os.path.join(config_path, "label_config_enhanced_tick_sh.json"),'w')
    res_dict = {}
    for root,dir,files in os.walk(file_path):
        for file in files:
            contents = open(os.path.join(root,file),"r").read()
            if file.endswith(".dos"):
                res_dict[file[:-4]] = [{}]
    b.write(json.dumps(res_dict))
    return


def main(start_date, end_date, target_securities):
    
    file_path = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-2]), "labels/InfoTech/Factors")
    non_factor_path = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-2]), "labels/InfoTech/NoneFactors")
    config_path = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-2]), "data_update")
    gen_configs(config_path, file_path)    
    calc_and_save_factors(config_path, file_path, start_date, end_date, target_securities, non_factor_path, return_mode='show', study_scenario='stock', data_type='enhanced_tick')
    return

if __name__ == "__main__":
    target_securities =['508099.SH']
    start_month_list = sorted([str(i)+"0101" for i in range(2021,2025)]+[str(i)+"0701" for i in range(2021,2025)])
    end_month_list = sorted([str(i)+"0630" for i in range(2021,2025)]+[str(i)+"1231" for i in range(2021,2025)])
    month_list = sorted(list(set(zip(start_month_list,end_month_list))))
    for stock in target_securities:
        print(stock, target_securities.index(stock)/len(target_securities))
        for start_date,end_date in month_list:
            try: 
                main(start_date, end_date, target_securities)
            except:
                continue


