from AutoMiningFrame.DataCaculation.entry.FactorCalcBatch import calc_factors_by_config,calc_per_factor_by_file
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from xquant.factordata import FactorData
import os
import json
fd = FactorData()
import sys
import time
start = time.time()
user_id='016869'
fp = FactorProvider(user_id)
config_path = "./factor_config_cf_future.json"


start_date = sys.argv[1]#"20230505"
end_date = sys.argv[2]#"20230505"
target_securities = [sys.argv[3]] #['00001.HK']
return_mode='show'
file_path = "/home/appadmin/DolphindbFactors/factors/norm_factors/future_new_factors"
nonfactor_path = "/home/appadmin/DolphindbFactors/factors/norm_factors/future_new_non_factors"
study_scenario = 'future'
data_type = 'tick'



def create_future_cf(factor_path):
    a = open(config_path,'w')
    res_dict = {}
    for root,dir,files in os.walk(factor_path):
        for file in files:
            contents = open(os.path.join(root,file),"r").read()
            if not file.startswith("Factor"):
                continue
            if file.startswith("FactorT") and file[7].isupper():
                continue
            if "M_BuyQty" in contents or "M_SellQty" in contents or "M_SellCount" in contents or "M_BuyCount" in contents or "M_BuyMoney" in contents or "M_SellMoney" in contents:
                continue
            if "M_Trade" in contents:
                continue
            if "M_NumOfferOrders" in contents or "M_NumBidOrders" in contents or "M_Weighted" in contents or "M_NumTrades" in contents:
                continue
            if file.endswith(".dos"):
                res_dict[file[:-4]] = [{}]
    a.write(json.dumps(res_dict))
    return

create_future_cf(file_path)


# 根据json配置文件，批量计算因子值
res = calc_factors_by_config(config_path, file_path, start_date, end_date, target_securities, return_mode, non_factor_path=nonfactor_path, study_scenario=study_scenario, data_type=data_type)

#上传因子值到公共库
fp.save_public_data_to_dfs(res, factor_type='factor', data_type='future_tick')
end = time.time()
print("[FactorCalcBatch] total cost :{}".format(end-start))
