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

file_path = "/home/appadmin/Factors/"
target_securities = ['688599.SH']
factor_name = "FactorTechIndicatorForOSC"
res = calc_per_factor_by_file(factor_name=factor_name, file_path=file_path, start_date='20220307',
                                                   end_date='20220307',
                                                   target_securities=target_securities, study_scenario='stock', data_type='enhanced_tick',
                                                   need_factorfunc=False)
print(res)
print(res[res['timestamp']=='2022-03-07 09:35:59'])

# res1.to_csv("/data/user/quanttest007/backtest-algo/K0321763/科创板上线因子跑批/Factors/res_688363.csv")
