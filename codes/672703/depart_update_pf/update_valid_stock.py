import numpy as np
import pandas as pd
from xquant.factordata import FactorData
import datetime
import os
import pickle
import config_path
from xquant.xqutils.helper import link
lm = link.LinkMessage()

invalid_stk_list = ['601598.SH', '300482.SZ', '600518.SH', '002308.SZ'] + \
    ['000010.SZ',
     '000018.SZ',
     '000760.SZ',
     '000868.SZ',
     '000971.SZ',
     '002005.SZ',
     '002249.SZ',
     '002354.SZ',
     '002445.SZ',
     '002502.SZ',
     '002512.SZ',
     '002519.SZ',
     '002668.SZ',
     '300090.SZ',
     '300269.SZ',
     '300291.SZ',
     '600079.SH',
     '600117.SH',
     '600166.SH',
     '600240.SH',
     '600470.SH',
     '600682.SH',
     '601038.SH',
     '601127.SH']
def update_valid_stock(today,time,invalid_stk=None,pool_stock_path='',label_test=False):
    s = FactorData()
    result1 = s.tradingday(today,-2)
    last_date = result1[-2]
    today_date = result1[-1]
    print('#setting#:',last_date,today_date,time)
    # quant_pool
    files = os.listdir(pool_stock_path)
    files.sort()
    pool_file = files[-1]
    print('pool_file:',pool_file)
    q_pool = pd.read_excel(pool_stock_path+pool_file, sheet_name=0, header=0, squeeze=False, converters={'证券代码':str})
    q_pool_stk = (q_pool['证券代码'][q_pool['市场名称']==2] + '.SZ').values.tolist() + (q_pool['证券代码'][q_pool['市场名称']==1] + '.SH').values.tolist()
    with open(config_path.weight_path + 'pool_stock.pkl','wb') as f1:
        pickle.dump(q_pool_stk,f1)
    q_pool = pd.DataFrame(index=q_pool['证券代码'], columns=['证券名称', '市场名称'], data=q_pool[['证券名称', '市场名称']].values)
    q_pool.index.name = None
    # black list
    # black = pd.read_excel(pool_stock_path+'black_list_20190905.xls', converters={'证券代码':str})
    # black_stk = (black['证券代码'][black['市场名称']=='2'] + '.SZ').values.tolist() + (black['证券代码'][black['市场名称']=='1'] + '.SH').values.tolist()
    # black.index = black['证券代码']
    # black.index.name = None
    # # restrict list
    # restrict = pd.read_excel(pool_stock_path+'restrict_list_20190905.xls', converters={'证券代码':str})
    # restrict_stk = [stk + '.SH' if stk[0]=='6' else stk + '.SZ' for stk in restrict['证券代码'].values]
    # restrict.index = restrict['证券代码']
    # restrict.index.name = None
    # # invalid
    # if invalid_stk is None:
        # invalid_stk = invalid_stk_list
    # all stock
    stk_list = s.hset('MARKET', last_date, 'ALLA')
    stk_list = stk_list['stock'].values.tolist()
    # trade stock
    df = s.get_factor_value('Wind_vip',stk_list,[today_date],['trade_status'])
    trade_stk = [i[1] for i in df[df['trade_status']=='交易'].index.tolist()]
    
    # valid stock
    # valid_stk = list((set(q_pool_stk).intersection(trade_stk) - set(black_stk)) - set(monitor_stk))
    valid_stk = sorted((set(q_pool_stk) & set(trade_stk)))
    # valid_stk = sorted((set(q_pool_stk) & set(trade_stk)) - set(black_stk) - set(restrict_stk) - set(invalid_stk))
    # valid_stk_str = ''
    # for i in valid_stk:
    #     valid_stk_str += i + ','
    # valid_stk_str = valid_stk_str[:-1]
    
    # preclose of valid stock
    valid_pre_close = s.get_factor_value('Wind_vip',valid_stk,[today_date],['pre_close'])
    tmp = valid_pre_close.loc[today_date,:]['pre_close']
    # valid_pre_close = w.wss(valid_stk_str, 'pre_close', 'tradeDate=' + today_date + ';priceAdj=U;cycle=D')
    valid_pre_close = pd.Series(index=list(tmp.index), data=tmp.values)
    valid_pre_close.sort_index(inplace=True)
    
    # max up or down stock
    if time == '0930':
        close = s.get_factor_value('Basic_factor',stk_list,[last_date],['close'])
        pre_close = s.get_factor_value('Basic_factor',stk_list,[last_date],['pre_close'])
        close = pd.DataFrame(close['close'].values,index=list(close.loc[last_date,:].index))
        pre_close = pd.DataFrame(pre_close['pre_close'].values,index=list(pre_close.loc[last_date,:].index))
        ret = (close-pre_close)/pre_close
        maxup_stk = list(ret[0][ret[0]>=0.098].index)
        maxdown_stk = list(ret[0][ret[0]<=-0.098].index)        
        # maxupordown = s.get_factor_value('Basic_factor',stk_list,[last_date],['maxupordown'])
        # maxup_stk = [i[1] for i in maxupordown['maxupordown'][maxupordown['maxupordown']==1].index]
        # maxdown_stk = [i[1] for i in maxupordown['maxupordown'][maxupordown['maxupordown']==-1].index]
    elif time == '1300':
        close = pd.read_pickle(config_path.basic_data_path + 'minute/Close/%s.pkl' % today_date)
        stocks_use = list(close.columns)
        pre_close = s.get_factor_value('Wind_vip',stocks_use,[today_date],['pre_close'])
        pre_close = pd.DataFrame(pre_close['pre_close'].values,index=list(pre_close.loc[today_date,:].index))

        ret = close.iloc[119]/pre_close[0]-1
        maxup_stk = list(ret[ret>=0.098].index)
        maxdown_stk = list(ret[ret<=-0.098].index)
        
    amt = pd.read_pickle(config_path.basic_data_path + 'daily/amt_by_yuan.pkl')

    amt_ = (amt.loc[:last_date].iloc[-5:]).mean(axis=0)
    stocksAmtLowerThan5QianWan = amt_[amt_<=5e7].index.tolist()
    stocksAmtLowerThan3QianWan = amt_[amt_<=3e7].index.tolist()
        
        
    print('number of allll stock :', len(stk_list))
    print('number of trade stock :', len(trade_stk))
    print('number of quant stock :', len(q_pool_stk))
    print('number of valid stock :', len(valid_stk))
    print('number of maxup stock :', len(maxup_stk))
    print('number of maxdn stock :', len(maxdown_stk))
    print('number of Amt<5e7 stock :', len(stocksAmtLowerThan5QianWan))
    str_send = \
    'number of allll stock :' + str(len(stk_list)) + '\n'+ \
    'number of trade stock :' + str(len(trade_stk)) + '\n'+ \
    'number of valid stock :' + str(len(valid_stk)) + '\n'+ \
    'number of maxup stock :' + str(len(maxup_stk)) + '\n'+ \
    'number of maxdn stock :' + str(len(maxdown_stk)) + '\n'+ \
    'number of Amt<5e7 stock :' + str(len(stocksAmtLowerThan5QianWan))
    
    valid_stk = {'trade_stk':valid_stk, 'maxup_stk':maxup_stk, 'maxdown_stk':maxdown_stk, \
    'valid_pre_close':valid_pre_close,'stocksAmtLowerThan5QianWan':stocksAmtLowerThan5QianWan,\
    'stocksAmtLowerThan3QianWan':stocksAmtLowerThan3QianWan}

    
    if not label_test:
        np.save(config_path.valid_stock_path + 'valid_stock_' + today_date + '_' + time + '.npy', valid_stk)
    lm.sendMessage(str_send)