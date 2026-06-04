# %%
import datetime
import re
from xquant.factordata import FactorData
from AutoMiningFrame.DataCaculation.entry.FactorCalcBatch import calc_per_factor_by_file
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from AutoMiningFrame.DataCaculation.entry.FactorResearch import sys_factor_calc_batch
from AutoMiningFrame.FactorBacktest.TickFactorBacktest import FactorBacktest
#%%
from AutoMiningFrame.DataCaculation.entry.FactorCalcBatch import calc_per_factor_by_file, calc_factors_by_config
import os
import pandas as pd
pd.set_option("display.max_colwidth", 1000)
pd.set_option("display.max_columns", None)
# pd.set_option("display.max_rows", None)

file_path = "/home/appadmin/server/modules/Factors/"
target_securities = ['688599.SH']
config_path = "/home/appadmin/server/factor_config.json"
start_date = "20220308"
end_date = "20220308"
return_mode = 'show'
study_scenario = "stock"
res = calc_factors_by_config(config_path, file_path, start_date, end_date, target_securities, return_mode, study_scenario=study_scenario)


print(res)
res.to_csv("~/compare_factor/res_batch_688599.csv",index=False)

# res1.to_csv("/data/user/quanttest007/backtest-algo/K0321763/科创板上线因子跑批/Factors/res_688363.csv")
