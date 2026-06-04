import pandas as pd
import numpy as np
import os
import copy
import time as mytime
import my_fun as mf
from scipy import stats
import copy
import re
import shutil
import talib as ta
import pickle

BASE_DIR = r'D:/Work/遗传算法测试'

class Create_Data():
    def save_pkl(self):
        fn = BASE_DIR + r'/原始数据/000906.SH.csv'
        data = pd.read_csv(fn,encoding = 'gbk',index_col = 0,engine = 'python')
        label = ['trade_dt','s_dq_open','s_dq_high','s_dq_low','s_dq_close','s_dq_volume']
        data = data[label]
        data = data.set_index('trade_dt')
        data = data.sort_index()
        data = data.dropna(how = 'any',axis = 0)
        with open(BASE_DIR + r'/训练数据/000906.SH.pkl','wb') as file:
            pickle.dump(data,file)
    
    
CD = Create_Data()

aaa = CD.save_pkl()