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
lm = link.LinkMessage()


isvalid = pd.read_pickle(basic_data_path+'daily/is_valid.pkl')
try:
    cc = isvalid.loc[today].sum()
    lm.sendMessage("{0} Number of is_valid: {1}".format(today,cc))
except KeyError:
    lm.sendMessage("is_valid not updated today")


stpt = pd.read_pickle(basic_data_path+'daily/stpt.pkl')
try:
    cc = stpt.loc[today].astype('float').sum()
    lm.sendMessage("{0} Number of stpt stocks: {1}".format(today,cc))
except KeyError:
    lm.sendMessage("stpt not updated today")



adjf = pd.read_pickle(basic_data_path+'daily/adjfactor.pkl')
try:
    cc = len(set(adjf.loc[today].dropna().tolist()))
    lm.sendMessage("{0} Number of different adjfactors: {1}".format(today,cc))
except KeyError:
    lm.sendMessage("adjfactor not updated today")



    