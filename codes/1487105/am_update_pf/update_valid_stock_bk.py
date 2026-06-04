import numpy as np
import pandas as pd
from xquant.factordata import FactorData
s = FactorData()
import datetime
import os
import pickle
import config_path
from xquant.xqutils.helper import link
from xquant.thirdpartydata.marketdata import MarketData
ma = MarketData()
lm = link.LinkMessage()

def update_valid_stock(today,time,invalid_stk=None,pool_stock_path='',test_label=False,\
    limit = 0.098):
#    black_list = ['002647.SZ','300312.SZ','600722.SH','000606.SZ','002075.SZ','300343.SZ']
#    black_list = ['300343.SZ','300813.SZ'] # 20210728
#    black_list = ['605020.SH','300343.SZ','300813.SZ'] # 20210729
#    black_list = ['605020.SH','300343.SZ','300813.SZ','300705.SZ'] # 20210730
#    black_list = ['605020.SH','300343.SZ','300813.SZ','300705.SZ','600338.SH'] # 20210814
#    black_list = ['300343.SZ','300705.SZ','300813.SZ','600218.SH','600338.SH','605020.SH'] # 20210819
#    black_list = ['300350.SZ','300712.SZ','600112.SH','600218.SH','600306.SH','600338.SH','603032.SH','605020.SH'] # 20210820
#    black_list = ['300350.SZ','300712.SZ','600112.SH','600218.SH','600306.SH','600338.SH','603032.SH','603396.SH','605020.SH'] # 20210830
#    black_list = ['300350.SZ','600112.SH','600218.SH','600306.SH','603032.SH','603396.SH'] # 20210903
#    black_list = ['300350.SZ','300688.SZ','600112.SH','600218.SH','600306.SH','603032.SH','603396.SH'] # 20210906
#    black_list = ['300350.SZ','300688.SZ','600112.SH','600218.SH','600306.SH','603032.SH','603396.SH','600968.SH'] # 20210917
#    black_list = ['300052.SZ','300350.SZ','300437.SZ','300688.SZ','600112.SH','600218.SH','600306.SH','603032.SH','603396.SH','600968.SH'] # 20210922
#    black_list = ['300052.SZ','300350.SZ','300437.SZ','600112.SH','600218.SH','600306.SH','603032.SH','600968.SH'] # 20210923
#    black_list = ['000415.SZ','000564.SZ','000585.SZ','000616.SZ','000796.SZ','300052.SZ','300350.SZ','300437.SZ','600112.SH','600218.SH','600221.SH','600306.SH','600387.SH','600515.SH','600555.SH','600751.SH','603032.SH','600968.SH'] # 20210928
#    black_list = ['000415.SZ','000564.SZ','000585.SZ','000616.SZ','000796.SZ','300052.SZ','300350.SZ','300437.SZ','600112.SH','600218.SH','600221.SH','600306.SH','600387.SH','600515.SH','600555.SH','600751.SH','600968.SH','603032.SH','605286.SH'] # 20211103
    black_list = ['000415.SZ','000564.SZ','000585.SZ','000616.SZ','000796.SZ','300052.SZ','300350.SZ','300437.SZ','600112.SH','600218.SH','600221.SH','600306.SH','600387.SH','600515.SH','600555.SH','600751.SH','600968.SH','603032.SH','605286.SH'] # 20211108
    black_sell_list = ['600968.SH'] # 20210917
    # 002075 20210708 重组失败
    
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
    q_pool_stk = list(set(q_pool_stk)-set(black_list))
    q_pool_stk.sort()
#    invalid_stk_list = ['600291.SH']
    print('black_list:',black_list)
    assert  len(set(q_pool_stk) & set(black_list))==0

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
    #np.save(config_path.valid_stock_path + 'valid_stock_' + today_date + '_' + time + '.npy', valid_stk)    
    valid_stk_before = np.load(config_path.valid_stock_path + 'valid_stock_' + last_date + '_' + time + '.npy').tolist()

    # df = ma.get_am_mdc_constant()
    # adj_today=df['mdc_trade_status'][today_date].to_frame()
    # adj_today.dropna(inplace=True)
    # trade_stk = adj_today[np.array(adj_today['mdc_trade_status']!='8') \
    #         & np.array(adj_today['mdc_trade_status']!='6')\
    #         & np.array(adj_today['mdc_trade_status']!='')].index.tolist()   
            
    # adj_today=df['mdc_stpt'][today_date].to_frame()
    # adj_today.dropna(inplace=True)
    # trade_stk_noST = adj_today[np.array(adj_today['mdc_stpt']!='1')].index.tolist()  
    # trade_stk_ST = adj_today[np.array(adj_today['mdc_stpt']=='1')].index.tolist() 
    # trade_stk = sorted(list(set(trade_stk)&set(trade_stk_noST)))                                                                                   

    trade_stk = valid_stk_before['trade_stk']
    trade_stk_ST = valid_stk_before['stk_ST']
    # pre_close

    pre_close=pd.read_pickle(config_path.basic_data_path+'/daily/pre_close.pkl')
    pre_close_today = pd.read_pickle(config_path.basic_data_path_bk + 'pre_close_%s.pkl' % today_date)
    if pre_close.index[-1] == pd.to_datetime(today_date):
        pass
    else:
        pre_close_today = (pre_close_today.T).reindex(index=pre_close.columns).T
        pre_close_today.index=[pd.to_datetime(today_date)]
        pre_close = pre_close.append(pre_close_today)
        pd.to_pickle(pre_close,config_path.basic_data_path+'/daily/pre_close.pkl')


    # adjfactor
    close=pd.read_pickle(config_path.basic_data_path+'/daily/close.pkl')
    adj = pd.read_pickle(config_path.basic_data_path+'/daily/adjfactor.pkl')
    adj_today = close.loc[last_date]*adj.loc[last_date]/pre_close_today
    if adj.index[-1] == pd.to_datetime(today_date):
        pass
    else:
        adj_today = adj_today.reindex(index=pre_close.columns).T
        adj_today.index=[pd.to_datetime(today_date)]
        adj = adj.append(adj_today)
        pd.to_pickle(adj,config_path.basic_data_path+'/daily/adjfactor.pkl')        

    # valid stock
    # valid_stk = list((set(q_pool_stk).intersection(trade_stk) - set(black_stk)) - set(monitor_stk))
#    print('300023.SZ' in trade_stk)
    valid_stk = sorted((set(q_pool_stk) & set(trade_stk)))
#    print('300023.SZ' in valid_stk)
    valid_stk = list(set(valid_stk)-set(black_list))
#    print('300023.SZ' in valid_stk)

    valid_pre_close = pd.read_pickle(config_path.basic_data_path+'/daily/pre_close.pkl').loc[last_date]
    valid_pre_close.sort_index(inplace=True)
    stk_cyb = [i for i in stk_list if i[0]=='3']

    # max up or down stock
    if time == '0930':
        close = s.get_factor_value('Basic_factor',stk_list,[last_date],['close'])
        pre_close = s.get_factor_value('Basic_factor',stk_list,[last_date],['pre_close'])
        close = pd.DataFrame(close['close'].values,index=list(close.loc[last_date,:].index))
        pre_close = pd.DataFrame(pre_close['pre_close'].values,index=list(pre_close.loc[last_date,:].index))
        ret = (close-pre_close)/pre_close
        ret = ret[0]
        maxup_stk = list(ret[ret>=limit].index)
        maxdown_stk = list(ret[ret<=-limit].index)                
        # maxupordown = s.get_factor_value('Basic_factor',stk_list,[last_date],['maxupordown'])
        # maxup_stk = [i[1] for i in maxupordown['maxupordown'][maxupordown['maxupordown']==1].index]
        # maxdown_stk = [i[1] for i in maxupordown['maxupordown'][maxupordown['maxupordown']==-1].index]
    elif time == '1300':
        close = pd.read_pickle(config_path.basic_data_path + 'minute/Close/%s.pkl' % today_date)
        stocks_use = list(close.columns)
        # pre_close = s.get_factor_value('Wind_vip',stocks_use,[today_date],['pre_close'])
        # pre_close = pd.DataFrame(pre_close['pre_close'].values,index=list(pre_close.loc[today_date,:].index))
        pre_close = s.get_factor_value('Basic_factor',stocks_use,[today_date],['mdc_pre_close'])
        pre_close = pd.DataFrame(pre_close['mdc_pre_close'].values,index=list(pre_close.loc[today_date,:].index))        
        ret = close.iloc[119]/pre_close[0]-1
        maxup_stk = list(ret[ret>=limit].index)
        maxdown_stk = list(ret[ret<=-limit].index)

    if today > '20200824' or (today == '20200824' and time not in ['0930']):  
        print('CYB Start')                      
        stk_cyb_max = list(set(stk_cyb) & set(maxup_stk +maxdown_stk))

        if len(stk_cyb_max) != 0:
            maxup_stk = list(set(maxup_stk) - set(stk_cyb_max))
            maxdown_stk = list(set(maxdown_stk) - set(stk_cyb_max))               
            stk_cyb_maxup = list(ret.loc[stk_cyb_max][ret.loc[stk_cyb_max]>=limit+0.1].index)            
            maxup_stk.extend(stk_cyb_maxup)

            stk_cyb_maxdown = list(ret.loc[stk_cyb_max][ret.loc[stk_cyb_max]<=-limit-0.1].index)
            maxdown_stk.extend(stk_cyb_maxdown)
        
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
#    print('300023.SZ' in valid_stk, len(valid_stk))
    valid_stk = {'trade_stk':valid_stk, 'maxup_stk':maxup_stk, 'maxdown_stk':maxdown_stk, \
    'valid_pre_close':valid_pre_close,'stocksAmtLowerThan5QianWan':stocksAmtLowerThan5QianWan,\
    'stocksAmtLowerThan3QianWan':stocksAmtLowerThan3QianWan,'stk_ST':trade_stk_ST}

    
    if not test_label:
        print('test_label',test_label)
        np.save(config_path.valid_stock_path + 'valid_stock_' + today_date + '_' + time + '.npy', valid_stk)    
        #500
        weigh500_his = pd.read_pickle(config_path.basic_data_path+'/daily/ZZ500_data_estimate.pkl')
        stock_team = list(weigh500_his.columns)
        weigh500_his.loc[pd.to_datetime(last_date)] = 0
        weight500  = s.hset('INDEX',today_date,'ZZ500',1)
        weight500.index = weight500['stock']#['stock']
        weight500_ = weight500.loc[list(set(weight500.index)&set(stock_team))]
    #    if len(weight500_)<=490:
    #        lm.sendMessage('zz500 data error:'+str(trade_stk))
        weigh500_his.loc[last_date,weight500_['stock']] = weight500_['weight']
        pd.to_pickle(weigh500_his,config_path.basic_data_path+'/daily/ZZ500_data_estimate.pkl')
        lm.sendMessage('zz500:'+str(weight500['weight'].sum()))
        
        #300
        weigh500_his = pd.read_pickle(config_path.basic_data_path+'/daily/HS300_data_estimate.pkl')
        stock_team = list(weigh500_his.columns)
        weigh500_his.loc[pd.to_datetime(last_date)] = 0
        weight500  = s.hset('INDEX',today_date,'HS300',1)
        weight500.index = weight500['stock']#['stock']
        weight500_ = weight500.loc[list(set(weight500.index)&set(stock_team))]
    #    if len(weight500_)<=290:
    #        lm.sendMessage('hs300 data error:'+len(weight500_))
        weigh500_his.loc[last_date,weight500_['stock']] = weight500_['weight']
        pd.to_pickle(weigh500_his,config_path.basic_data_path+'/daily/HS300_data_estimate.pkl')    
        lm.sendMessage('hs300:'+str(weight500['weight'].sum()))
        
    
    lm.sendMessage(str_send)