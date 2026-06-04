import os
import pandas as pd
from config_path import *
path = basic_data_path+'quarter/'
qts = (os.listdir(path))
# qts=[q[:-4] for q in qts]
for q in qts:
    temp = pd.read_pickle(path+q)
    if temp.iloc[-1,:].notnull().sum() < 1:
        temp.iloc[-1,:]=temp.iloc[-2,:]
        temp.to_pickle(path+q)