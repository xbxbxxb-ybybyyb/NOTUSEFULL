import ray
from xquant.bonddata import BondData
import numpy as np
import os
os.environ['use_cmo'] = 'True'
# from xquant.model.cmo import tracking as cmo_tracking
# from xquant.model.tracking import *
from xquant.model import auto_log
# from xquant.model.cmo.platform.huatai import *
import os
print(os.environ.get("use_cmo"))

bd = BondData()
df3 = bd.get_bond_data("204028.SH", "20220215 090000000",
                                       "20220215 200000000", 'TICK')
print(df3)


# from xquant.bonddata import BondData
# bd = BondData()
# result = bd.get_bond_data_day('SH', '20220215', 'Tick')