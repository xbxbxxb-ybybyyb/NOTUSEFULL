import sys
import os
import pandas as pd
import numpy as np
import datetime
from xquant.xqutils.helper import link
from config_path import *
#today = '20211011'
paths = basic_data_path+'minute/'
close = pd.read_pickle(paths + 'Close/' + today + '.pkl')
volume = pd.read_pickle(paths + 'Volume/' + today + '.pkl')

cc = close.notnull().sum()
n1 = cc[(cc == 0)].count()
vv = volume.notnull().sum()
n2 = vv[(vv == 0)].count()

lm = link.LinkMessage()
lm.sendMessage("{0} No Close Price Data Stocks In Total : {1}".format(today,n1))
lm.sendMessage("{0} No Volume Data Stocks In Total : {1}".format(today,n2))

if close.iloc[120:].shape[0]<1:
    lm.sendMessage('No PM Minute Data.')
else:
    cc = close.iloc[120:].notnull().sum()
    n3 = cc[(cc == 0)].count()
    lm.sendMessage("{0} No PM Close Price Data Stocks In Total : {1}".format(today,n3))