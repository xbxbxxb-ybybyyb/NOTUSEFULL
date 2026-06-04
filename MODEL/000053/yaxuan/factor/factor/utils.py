import numpy as np
import pandas as pd
from datetime import datetime
import warnings
import os 
import shutil
import tempfile
import contextlib
from typing import Optional, Text, IO, Union
from pathlib import Path
import logging
import pickle
import multiprocessing
from sklearn import preprocessing
from multiprocessing.pool import Pool
import matplotlib.pyplot as plt
import sys
from collections import defaultdict
from scipy.stats import rankdata
import psutil
from collections import Counter
from sklearn.linear_model import LinearRegression
from pickle import UnpicklingError
from indicators import ind_recall



root = '/data/user/000053/yaxuan/'
share = '/data/user/018187/InternData/RawData/'
# from preprocess import *
warnings.filterwarnings('ignore')


def fill_(df,type_='all'):
    if type_=='all':
        return df.ffill().bfill().fillna(0)
    elif type_=='ffill':
        return df.ffill()
    elif type_=='ffill+bfill':
        return df.ffill().bfill()
    elif type_=='None':
        return df
    else:
        raise AttributeError('type_should be all or ffill or ffill+bfill or None')

def drop_(df):
    df = df[~df.T.isin([np.nan, np.inf, -np.inf]).any()]
    return df
        
    
def nan_check(df):
    df[df==np.inf] = np.nan
    df[df==-np.inf] = np.nan
    df_nan = df.isna().sum()
    df_nan = df_nan[df_nan>0]
    if len(df_nan)>0:
        print('NaNs: ',df_nan,df.shape)

def fill_zeros(s,fill_num):
    s[s==0] = fill_num
    return s

def winsor(s,up_bar=None,down_bar=None):
    if up_bar:
        s[s>up_bar] = up_bar
    if down_bar:
        s[s<down_bar] = down_bar
    return s

def fill_nan_and_inf(df,feature_cols=[]):
    if not len(feature_cols):
        if type(df) == pd.core.frame.DataFrame:
            idx = df.index.values
            cols = df.columns.values
            values = df.values
            df = pd.DataFrame(fill_nan_and_inf(values),columns=cols,index=idx)
            df = df.dropna()
            return df
        else:
            df[df==np.inf] = np.nan
            df[df==-np.inf] = np.nan
            np.nan_to_num(df,0)
            return df
    else:
        df_copy = df[feature_cols].copy()
        return fill_nan_and_inf(df_copy)
    
              
def get_value(data):
    if type(data) in [pd.core.frame.DataFrame,pd.core.series.Series]:
        data = data.values
    return data