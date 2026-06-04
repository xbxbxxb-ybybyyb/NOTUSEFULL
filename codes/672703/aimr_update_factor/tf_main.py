from xquant.compute.aimr import AIMR
import json
import pandas as pd
import datetime
import numpy as np
import pandas as pd
from itertools import chain
import os
path ='/data/group/800020/AlphaExperiment/own_factors_neu/'
factor_list = sorted([f[:-4] for f in os.listdir(path)])
factor_value = np.arange(len(factor_list)).tolist()
map_dict = {}
num = 10
count = int(len(factor_list)/num)+1
map_dict={}
for i in range(num):
    map_dict[i] = factor_list[i*count:(i+1)*count]
pd.to_pickle(map_dict,'/data/user/013546/rubbish/map_dict.pkl')
params = {
    "parallel_list": sorted(list(map_dict.keys())),   
    "tag":"xquant",
    "cpu":15,
    "gpu":0,
    "memory":20000
}
AIMR.runTasks('aimr_update_factor/test_check_factor.py',json.dumps(params))