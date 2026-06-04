# -*- coding: utf-8 -*-
"""
Created on 2018/11/9
@author: 011669
"""


import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis
import datetime as dt
from sklearn.linear_model import LinearRegression
from functools import partial
import pickle

def adj_date_format(df,dt_name='dt',Ticker_name='Ticker'):
    tmp_df = df.reset_index()
    tmp_df[dt_name] = tmp_df[dt_name].apply(lambda x:int(x.strftime('%Y%m%d')))
    output = tmp_df.set_index([dt_name,Ticker_name])
    return output

def save_pickle(save_dict,save_path):
    with open(save_path, 'wb') as input:
        pickle.dump(save_dict,input,protocol=pickle.HIGHEST_PROTOCOL)
    return