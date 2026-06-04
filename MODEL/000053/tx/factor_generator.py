import pandas as pd
import numpy as np
from DATA import * 
from bisect import bisect_left
from datetime import datetime

import statsmodels.api as sm
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

COST = 0.001
tick = 0.01

def pool_factorizer_map(nums, nprocs):
    with ProcessPoolExecutor(max_workers = nprocs) as executor:
        for num, factors in zip(nums, executor.map(mp_test, nums)):

            print(num)
            
            
            
nprocs = 1

START = '20220105'
END = '20230621'

s = FactorData()
trade_date = s.tradingday(START, END) 

def main():
    pool_factorizer_map(DATE, nprocs)
    
len(trade_date)



DATE = trade_date
if __name__ == '__main__':
    main()
    
    
    
def mp_test(stock):
    ic = []
    IMB = pd.DataFrame([])
    Taglong = pd.DataFrame([])
    for i in range(len(data_date)):
        date = data_date[i]
        
        df = read_daily_one_stcok_tick(stock, date, data_date, paths)
        if len(df) !=0:
            imb = volume_imb_generator(df)
            
            imb, return_long = input_pair_dropna(imb, return_long)    
            ic.append(imb.corr(return_long))
            
    IC_mean.append(np.mean(np.array(ic)))
    IC.append(IMB.corrwith(Taglong).values[0])