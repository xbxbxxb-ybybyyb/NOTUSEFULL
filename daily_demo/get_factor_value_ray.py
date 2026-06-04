import ray
from xquant.factordata import FactorData
import time

fa = FactorData()
days = fa.tradingday("20200401", '20200610')
from xquant.bonddata import BondData
bd = BondData()
bond_list = bd.get_bond_set("20200330", 'kzz')
stocks = bond_list
print(stocks)
#WuKongProductionSignals
factors = fa.get_library_info()['ray_hq_factor']
print(factors)
t1 = time.time()
df = fa.get_factor_value_ray(1, 'ray_hq_factor', stocks, days, factors)
#print(df)
print(time.time()-t1)

import pickle
pickle.dump(df, open('df2.pickle','wb'))
