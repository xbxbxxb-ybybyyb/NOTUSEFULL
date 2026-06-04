import numpy as np 
import pandas as pd
import copy
import os
import time
import pickle
from xquant.factordata import FactorData
import datetime
from xquant.xqutils.helper import link
from config_path import *
factorData = FactorData()
date_list = factorData.tradingday(today,today)

am = []
pm = []
for day in date_list:
    print(day)
    amt = pd.read_pickle(basic_data_path+'minute/Amount/'+day+'.pkl')
    vol = pd.read_pickle(basic_data_path+'minute/Volume/'+day+'.pkl')
    amp = (amt[:120].sum()/vol[:120].sum()).to_frame().T
    pmp = (amt[120:].sum()/vol[120:].sum()).to_frame().T
    amp.index = [pd.Timestamp(day)]
    pmp.index = [pd.Timestamp(day)]
    am.append(amp)
    pm.append(pmp)

am_vwap = pd.concat(am)
pm_vwap = pd.concat(pm)
am_vwap[~np.isfinite(am_vwap)]=np.nan
pm_vwap[~np.isfinite(pm_vwap)]=np.nan

adj=pd.read_pickle(basic_data_path+'daily/adjfactor.pkl').loc['20140101':today]
am_vwap = am_vwap*adj
pm_vwap = pm_vwap*adj
am_vwap.to_pickle(basic_data_path+'daily/vwap_am_adj_cz.pkl')
pm_vwap.to_pickle(basic_data_path+'daily/vwap_pm_adj_cz.pkl')
print('Intro-day vwap data generated.')

lm = link.LinkMessage()
lm.sendMessage("{0} AM_PM Vwap Data Updated: {1}".format(today, today))

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
