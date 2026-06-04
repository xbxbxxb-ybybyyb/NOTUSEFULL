from AutoMiningFrame.DataCaculation.entry.FactorCalcBatch import calc_factors_by_config,calc_per_factor_by_file
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from xquant.factordata import FactorData
import json
fd = FactorData()
import sys
import pandas as pd
user_id='016869'
fp = FactorProvider(user_id)
config_path = "./label_config.json"
start_date = sys.argv[1]
end_date = sys.argv[2]
target_securities = ['688012.SH']
return_mode='show'
#file_path = "/home/appadmin/DolphindbFactors/factors/new/new_factors"
#nonfactor_path = "/home/appadmin/DolphindbFactors/factors/new/new_nonfactors"
file_path = "/home/appadmin/DolphindbFactors/labels/InfoTech/Factors"

nonfactor_path = "/home/appadmin/DolphindbFactors/labels/InfoTech/NoneFactors"
#file_path = "/home/appadmin/DolphindbFactors/factors/InfoTech/StockMMRetV1Factors"
#nonfactor_path = "/home/appadmin/DolphindbFactors/factors/InfoTech/StockMMRetV1NoneFactor"

#file_path = "/home/appadmin/DolphindbFactors/data_update/CentralFactors"
#nonfactor_path = "/home/appadmin/DolphindbFactors/data_update/CentralNoneFactors/"
study_scenario = 'stock'
data_type = 'tick_l2p'
#for date in fd.tradingday(start_date,end_date):
#    df = fp.get_market_data(target_securities,date,date,'sh_stock_tick_enhanced')
#    print(date, df.shape)
#    if df.shape[0]<3000:
#        raise Exception()


# 根据json配置文件，批量计算因子值
res = calc_factors_by_config(config_path, file_path, start_date, end_date, target_securities, return_mode, non_factor_path=nonfactor_path, study_scenario=study_scenario, data_type=data_type)
print(res)

#上传因子值到公共库
#res = pd.read_parquet("factordata_20200101_20201231.parquet")
fp.save_public_data_to_dfs(res, factor_type='label', data_type=data_type)


# 根据因子名称计算因子
#factor_list =json.loads(open(config_path).read()).keys()
#factor_list = ['var_last1_1']
#print(len(factor_list))
#for factor in factor_list:
#    print(factor)
#    res = calc_per_factor_by_file(factor, file_path, start_date, end_date, target_securities, study_scenario='stock', data_type='enhanced_tick', non_factor_path=nonfactor_path)
#    print(res)
#res.to_parquet("factordata_{}_{}.parquet".format(start_date, end_date))


# 获取公共库的因子列表和因子值
#fac = fp.load_info_from_dfs('factor','public','enhanced_tick')
#df = fp.load_public_data_from_dfs(symbol=target_securities,factor_list = fac, start_time='20230505',end_time='20230505',factor_type='factor')
#print(df.head(41))
#df.to_parquet("dolphin_res_20230505.parquet")
