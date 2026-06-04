# -*- coding: utf-8 -*-
import pickle
import sys
import pandas as pd
import numpy as np
import os
sys.path.insert(0,'update_factor/')
from update_factor_exector import *

if __name__=='__main__':

    assert len(sys.argv)==5,'update_factor_no_depend has less parameters'
    f = str(sys.argv[1])
    print(f)
    f_type = str(sys.argv[2])
    start_date = str(sys.argv[3])
    end_date = str(sys.argv[4])
    df_update = cal_single_factor(f, f_type, start_date, end_date)
    if(isinstance(df_update,dict) or isinstance(df_update,pd.DataFrame)):
        save_data(f,df_update, f_type)
