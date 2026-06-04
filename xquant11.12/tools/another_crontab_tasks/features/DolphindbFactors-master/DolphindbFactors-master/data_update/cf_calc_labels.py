from AutoMiningFrame.DataCaculation.entry.FactorCalcBatch import calc_factors_by_config,calc_per_factor_by_file
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from xquant.factordata import FactorData
import json
fd = FactorData()
import sys

user_id='016869'
fp = FactorProvider(user_id)
config_path = "./label_config_future.json"
start_date = sys.argv[1]#"20230505"
end_date = sys.argv[2]#"20230505"
target_securities = [sys.argv[3]] #['00001.HK']
return_mode='show'
file_path = "/home/appadmin/DolphindbFactors/labels/InfoTech/future/Factors"
nonfactor_path = "/home/appadmin/DolphindbFactors/labels/InfoTech/future/NoneFactors"
study_scenario = 'future'
data_type = 'tick'
 
# 根据json配置文件，批量计算因子值
res = calc_factors_by_config(config_path, file_path, start_date, end_date, target_securities, return_mode, non_factor_path=nonfactor_path, study_scenario=study_scenario, data_type=data_type)
print(res)
#res.to_parquet("label_{}_{}_{}.parquet".format(target_securities[0],start_date, end_date))
#上传因子值到公共库
fp.save_public_data_to_dfs(res, factor_type='label', data_type='future_tick')

