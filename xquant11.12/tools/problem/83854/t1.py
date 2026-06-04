import pandas as pd
import numpy as np
#import helper
from sklearn.linear_model import*
import matplotlib.pyplot as plt
from sklearn.decomposition import *
from multiprocessing import Pool
import time
from xquant.factordata import FactorData
import os
import xquant.thirdpartydata.marketdata as tick_api
from xquant.strategy.trademocker import ExchangeHouse
from xquant.strategy.trademocker import Order
import datetime

ma = tick_api.MarketData()
s= FactorData()
root_path = '/data/user/013150'
#root_path = '/app/data/013150'
def mkdir(path):
    path=path.strip()
    path=path.rstrip("\\")
    isExists=os.path.exists(path)
    if not isExists:
        os.makedirs(path) 
        print(path+' 创建成功')
        return True
    else:
        print(path+' 目录已存在')
        return False

def get_pairs(date,target_day,industry):
    pairs = ind_universe[industry]
    mkt_data = mkt_dict[target_day].dropna(axis=1)
    regression_sample = mkt_dict[date].loc[:,mkt_data.columns].dropna(axis=1)
    mkt_data = mkt_data.loc[:,regression_sample.columns]
    max_,pair = get_max(industry,date,mkt_data.columns.tolist())
    pair_mkt = mkt_data[pair]
    return pair_mkt,regression_sample[pair],max_

def get_max(industry,date,stk_list):
    adf_df = pd.read_pickle('%s/corr_analysis/%s/%s.pkl'%(root_path,industry,date))
    min_= None
    target_pair = None
    for i in range(adf_df.shape[0]):
        if adf_df.index[i] not in stk_list:
            continue
        for j in range(i+1,adf_df.shape[0]):
            if adf_df.index[j] not in stk_list:
                continue
            if min_==None:
                min_ = adf_df.loc[adf_df.index[i],adf_df.index[j]]
                target_pair = [adf_df.index[i],adf_df.index[j]]
            else:
                if min_ > adf_df.loc[adf_df.index[i],adf_df.index[j]]:
                    min_ = adf_df.loc[adf_df.index[i],adf_df.index[j]]
                    target_pair = [adf_df.index[i],adf_df.index[j]]
    return min_,target_pair


def get_sharpe(series,rf):
    m = series.pct_change().mean()
    v = series.pct_change().std()
    return (244**0.5)*(m-((1+rf)**(1./244))+1)/v
def get_return_and_annual_return(series):
    r = series[-1]/series[0]-1
    ar = (1+r)**(244./len(series))-1
    return r,ar
def get_volatility(series):
    return (244./len(series))*series.pct_change().std()


def MaxDrawdown(return_list):
    '''最大回撤率'''
    i = np.argmax((np.maximum.accumulate(return_list) - return_list) / np.maximum.accumulate(return_list))  # 结束位置
    if i == 0:
        return 0
    j = np.argmax(return_list[:i])  # 开始位置
    return (return_list[j] - return_list[i]) / (return_list[j])


def get_evaluation(net):
    net_daily = net.resample('1D').last().fillna(method='pad')
     
    sr = get_sharpe(net_daily['account_value'],0.03)
    r,ar = get_return_and_annual_return(net_daily['account_value'])
    v = get_volatility(net_daily['account_value'])
    mdd = MaxDrawdown(net_daily['account_value'])
    
    evaluate = pd.DataFrame(columns = ['Return','Annual Return','Volatility','Sharpe','MDD'])
    evaluate.loc[0,:] = [r,ar,v,sr,mdd]
    evaluate['trading_day'] = net_daily['account_value'].pct_change().apply(lambda x:x!=0).sum()
    evaluate['daily_win_rate']=net_daily['account_value'].pct_change().apply(lambda x:x>0).sum()/evaluate['trading_day']
    #evaluate['daily_signal_avg'] = stat['total'].sum()/evaluate['trading_day']
    #evaluate['total_day'] = len(chosed_clust_by_predict)-1
    #evaluate['trade_minutes'] = stat['trade_minutes'].sum()/evaluate['trading_day']
    return evaluate
def get_tick_mkt(pair_mkt):

    date = str(pair_mkt.index[0]).replace('-','').replace(' ','').replace(':','')[:6]
    X_tick = pd.read_pickle('%s/pair_trading_tick_mkt_data/%s/%s.pkl'%(root_path,pair_mkt.columns[1],date))
    y_tick = pd.read_pickle('%s/pair_trading_tick_mkt_data/%s/%s.pkl'%(root_path,pair_mkt.columns[0],date))
    #X_tick['datetime'] = (X_tick['MDDate']+X_tick['MDTime']).apply(lambda x : datetime.datetime.strptime(x[:-3],'%Y%m%d%H%M%S'))
    #y_tick['datetime'] = (y_tick['MDDate']+y_tick['MDTime']).apply(lambda x : datetime.datetime.strptime(x[:-3],'%Y%m%d%H%M%S'))
    return X_tick,y_tick
def get_tick_mkt_(pair_mkt):
    X_tick = ma.getMDSecurityTickDataFrame(pair_mkt.columns[1],\
                    str(pair_mkt.index[0]).replace('-','').replace(' ','').replace(':',''),\
                    str(pair_mkt.index[-1]).replace('-','').replace(' ','').replace(':',''),1)
    y_tick = ma.getMDSecurityTickDataFrame(pair_mkt.columns[0],\
                    str(pair_mkt.index[0]).replace('-','').replace(' ','').replace(':',''),\
                    str(pair_mkt.index[-1]).replace('-','').replace(' ','').replace(':',''),1)
    
    X_tick['datetime'] = (X_tick['MDDate']+X_tick['MDTime']).apply(lambda x : datetime.datetime.strptime(x[:-3],'%Y%m%d%H%M%S'))
    y_tick['datetime'] = (y_tick['MDDate']+y_tick['MDTime']).apply(lambda x : datetime.datetime.strptime(x[:-3],'%Y%m%d%H%M%S'))
    return X_tick,y_tick

def get_pair_trading(industry,date_list,initial_money,\
                         cost_rate=0.001,OPEN_THRESHOLD=3,CLOSE_THRESHOLD=1,STOP_THRESHOLD=5):
    keys  = date_list
    keys.sort()
#    result = dict()
#    net = pd.DataFrame()
    result = dict()
    net_whole = pd.DataFrame()
    money = initial_money
    stat = pd.DataFrame(columns=['signal_count','trading_time'])
    corr_selected = pd.DataFrame(index = date_list,columns=['corr'])
    for i in range(len(keys)-1):
        #i = 4
        print(i,money)
        history_data,mkt_data,corr_max = get_pairs(keys[i],keys[i+1],industry)
        history_data,mkt_data = history_data.fillna(method='pad').dropna(),mkt_data.fillna(method='pad').dropna()
        if history_data.corr().values[0,1]<0.8:
            print('low corr:',history_data.corr().values[0,1])
            continue
        corr_selected.loc[keys[i],'corr'] = mkt_data.corr().values[0,1]
        if history_data.shape[0]==0 or mkt_data.shape[0]==0:
            continue
        
        net = pd.DataFrame(0,index=mkt_data.index,columns=['account_value'])
        cash = float(money)#/history_data.shape[1]
        #result[keys[i+1]] = dict()
        trading_time = pd.Series(0,index=mkt_data.index)
        signal_count = 0
        
        #for each in mkt_data.columns:
        #each = mkt_data.columns[0]
        regression_sample = history_data#pd.concat([transformed_history,history_data[[each]]],axis=1)
        pair_mkt = mkt_data#pd.concat([transformed_mkt,mkt_data[[each]]],axis=1)
        X = regression_sample[regression_sample.columns[1]].values.reshape(-1,1)
        y = regression_sample[regression_sample.columns[0]]
        lr = LinearRegression()
        lr.fit(X,y)
        res = lr.predict(X)-y
        res_std = pd.Series(res).std()
        X_test = pair_mkt[pair_mkt.columns[1]].values.reshape(-1,1)
        y_test = pair_mkt[pair_mkt.columns[0]]
        #lr.score(X=X_test,y=y_test)
        e1 = time.time()
        check = get_daily_back_test(pair_mkt,lr,res_std, cash,cost_rate,OPEN_THRESHOLD,\
                        CLOSE_THRESHOLD,STOP_THRESHOLD)
        print('当天运行时间:',time.time() - e1)
        cash = check['account_value'].tolist()[-1]
        result[keys[i+1]] = check
        net['account_value'] = net['account_value']+check['account_value'].astype(float)
        #net = pd.concat([net,check[['account_value']]])
#            check['account_value'].plot()
#            plt.title(keys[i+1]+' '+each)
#            plt.show()
        #print(check)
        #print(mkt_data)
        trading_time = trading_time + check[mkt_data.columns[0]].astype(float).apply(lambda x : x!=0)
        signal_count = signal_count+check['pos_signal'].sum() + check['neg_signal'].sum()
            
            
        money = net['account_value'][-1]
        #net.plot()
        #plt.show()
        net_whole = pd.concat([net_whole,net])
        stat.loc[keys[i+1],'signal_count'] = signal_count
        stat.loc[keys[i+1],'trading_time'] = trading_time.apply(lambda x : x>0).sum()
    #net_whole.plot()
    evaluation = get_evaluation(net_whole)
    stat_mean = pd.DataFrame(stat.sum().astype(float)/len(result))
    evaluation = pd.concat([evaluation,stat_mean.T],axis=1).rename(columns=\
                          {'trading_time':'avg_daily_trading_minutes','signal_count':'daily_signal_count'})
    #evaluation['trading_days'] = len(result)
    evaluation['total_period'] = len(keys)-1
    return evaluation,result,net_whole,stat,corr_selected



def get_order_result(order_symbol, tick_mkt, order_qty, order_flag):
    print(111111111111111111111111)
    filled_qty = 0
    filled_cash = 0
    if order_flag == 'B':
        col = 'Sell%dPrice'
    elif order_flag == 'S':
        col = 'Buy%dPrice'
    else:
        print('Wrong order type')
        assert (1 == 2)
    orders_count = 0
    for i in tick_mkt.index:
        if filled_qty >= order_qty:
            print('done')
            break
        temp_order_price = tick_mkt.loc[i, col%1]
        temp_order = Order(stock_code=order_symbol, order_time=i, \
                           order_price=temp_order_price, \
                           order_volume=order_qty - filled_qty, \
                           bs_flag=order_flag)
        print('--------------------------')
        exchange_house2 = ExchangeHouse(mode='TRANS')
        exchange_house2.send(orders=[temp_order])
        print('--------------------------')
        record = temp_order.get_record()
        filled_qty += record['volume']
        filled_cash += record['accMount']
        print('--------------------------')
        print('filled_vol:', filled_qty, 'filled_cash', filled_cash)
        print('--------------------------')
        orders_count += 1
    print(2222222222222222222)
    return filled_qty, filled_cash, filled_qty >= order_qty,i,(i-tick_mkt.index[0]).seconds,orders_count


def get_daily_back_test(pair_mkt_, lr, res_std, cash, cost_rate=0.001, OPEN_THRESHOLD=3, \
                        CLOSE_THRESHOLD=1, STOP_THRESHOLD=5):
    cash_part = cash
    pair_mkt = pair_mkt_.dropna()
    X_series = pair_mkt[pair_mkt.columns[1]]
    y_series = pair_mkt[pair_mkt.columns[0]]
    ma = tick_api.MarketData()
    # df = ma.getMDSecurityTickDataFrame("601688.SH","20171201090000","20171201100000",0)
    e1 = time.time()
    X_tick = None
    y_tick = None
    y_symbol, X_symbol = pair_mkt.columns.tolist()
    spread_series = y_series - lr.predict(X_series.values.reshape(-1, 1))
    spread_series = pd.DataFrame(spread_series)
    spread_series.columns = ['spread']
    spread_series = spread_series['spread']
    record = pd.DataFrame(columns=pair_mkt.columns.tolist() + ['pos_signal', 'neg_signal', 'X_cost', 'y_cost', 'cash', \
                                                               'pos_open_threshold', 'neg_open_threshold',
                                                               'pos_stop_threshold', 'neg_stop_threshold', \
                                                               'pos_close_threshold', 'neg_close_threshold',
                                                               'signal_price_X', 'signal_price_y', \
                                                               'actual_price_X', 'actual_price_y',\
                                                               'X_filled_timestamp','y_filled_timestamp',\
                                                               'X_delay','y_delay','X_orders_count','y_orders_count'],
                          index=spread_series.index)
    if np.isnan(cash):
        print('cash is nan')
        print(1)
    shareX = int(cash * 0.6 / X_series[0])
    sharey = int(cash * 0.6 / y_series[0])

    has_pos = 0
    has_neg = 0

    # 买入X，卖出y
    pos_open_signal = 0
    # 买入y，卖出X
    neg_open_signal = 0
    pos_stop_signal = 0
    neg_stop_signal = 0
    pos_close_signal = 0
    neg_close_signal = 0

    X_position = 0
    y_position = 0
    stop_trading = False
    print('节点一', time.time() - e1)
    date = spread_series.index[0].date().strftime('%Y%m%d')

    for i in range(len(spread_series)):
        each = spread_series.index[i]
        X_cost = 0
        y_cost = 0


        if spread_series[each] > res_std * OPEN_THRESHOLD:
            pos_open_signal = 1
        if spread_series[each] < -res_std * OPEN_THRESHOLD:
            neg_open_signal = 1
        if each >= spread_series.index[-15]:
            stop_trading = True

        pos_sig = X_position == 0 and pos_open_signal == 1 and spread_series[
            each] > res_std * OPEN_THRESHOLD and not stop_trading
        neg_sig = y_position == 0 and neg_open_signal == 1 and spread_series[
            each] < -res_std * OPEN_THRESHOLD and not stop_trading
        close_pos = X_position > 0 and (
                    spread_series[each] < res_std * CLOSE_THRESHOLD or spread_series[each] > res_std * STOP_THRESHOLD)
        close_neg = y_position > 0 and (
                    spread_series[each] > -res_std * CLOSE_THRESHOLD or spread_series[each] < -res_std * STOP_THRESHOLD)
        if pos_sig or neg_sig or close_pos or close_neg:
            if type(X_tick) == type(None) or type(y_tick) == type(None):
                X_tick, y_tick = get_tick_mkt(pair_mkt)
                X_tick = X_tick[X_tick['MDDate'].eq(date)]
                y_tick = y_tick[y_tick['MDDate'].eq(date)]
                print('节点二', time.time() - e1)
            if each != spread_series.index[-2]:
                temp_X = X_tick[X_tick['datetime'] > spread_series.index[i + 1]]
                temp_y = y_tick[y_tick['datetime'] > spread_series.index[i + 1]]
                if each < spread_series.index[-15]:
                    temp_X = temp_X[temp_X['datetime'] < spread_series.index[i + 2]]  # .set_index('datetime')
                    temp_y = temp_y[temp_y['datetime'] < spread_series.index[i + 2]]  # .set_index('datetime')

                if temp_X.shape[0]==0:
                    temp_X = X_tick[X_tick['datetime'] > spread_series.index[i + 1]]
                if temp_y.shape[0]==0:
                    temp_y = y_tick[y_tick['datetime'] > spread_series.index[i + 1]]

                temp_X = temp_X.set_index('datetime')
                temp_y = temp_y.set_index('datetime')




        if each >= spread_series.index[-15]:

            stop_trading = True
            if X_position > 0:
                temp_X = X_tick[X_tick['datetime'] > spread_series.index[i + 1]].set_index('datetime')
                temp_y = y_tick[y_tick['datetime'] > spread_series.index[i + 1]].set_index('datetime')
                X_pos, X_cash, X_filled,X_filled_timestamp,X_delay,X_order_count = get_order_result(X_symbol, temp_X, X_position, 'S')
                y_pos, y_cash, y_filled,y_filled_timestamp,y_delay,y_order_count = get_order_result(y_symbol, temp_y, abs(y_position), 'B')
                record.loc[each, ['X_delay', 'y_delay', 'X_orders_count', 'y_orders_count']] = [X_delay, y_delay,
                                                                                                X_order_count,
                                                                                                y_order_count]
                X_position = X_position - X_pos
                y_position = y_position + y_pos
                X_cost += X_cash * cost_rate
                cash_part = cash_part + X_cash - y_cash

                record.loc[each, 'signal_price_X'] = pair_mkt.loc[each, X_symbol]
                record.loc[each, 'signal_price_y'] = pair_mkt.loc[each, y_symbol]
                record.loc[each, 'actual_price_X'] = X_cash / X_pos if X_pos > 0 else np.nan
                record.loc[each, 'actual_price_y'] = y_cash / y_pos if y_pos > 0 else np.nan
                record.loc[each, 'X_filled_timestamp'] = X_filled_timestamp
                record.loc[each, 'y_filled_timestamp'] = y_filled_timestamp
                if X_position != 0 or y_position != 0:
                    print(X_position, X_pos)
                    print(y_position, y_pos)
                    print('2NOT BALANCE!!!!!!!!!!!!!')
                    break
                record.loc[each, 'pos_close_threshold'] = 1
            if y_position > 0:
                temp_X = X_tick[X_tick['datetime'] > spread_series.index[i + 1]].set_index('datetime')
                temp_y = y_tick[y_tick['datetime'] > spread_series.index[i + 1]].set_index('datetime')
                X_pos, X_cash, X_filled, X_filled_timestamp,X_delay,X_order_count = get_order_result(X_symbol, temp_X, abs(X_position), 'B')
                y_pos, y_cash, y_filled, y_filled_timestamp,y_delay,y_order_count = get_order_result(y_symbol, temp_y, y_position, 'S')
                record.loc[each,['X_delay','y_delay','X_orders_count','y_orders_count']] = [X_delay,y_delay,X_order_count,y_order_count]
                X_position = X_position + X_pos
                y_position = y_position - y_pos
                # X_cost += X_cash*cost_rate
                y_cost += y_cash * cost_rate
                cash_part = cash_part + y_cash - X_cash
                if X_position != 0 or y_position != 0:
                    print(X_position, X_pos)
                    print(y_position, y_pos)
                    print('1NOT BALANCE!!!!!!!!!!!!!')
                    break

                record.loc[each, 'signal_price_X'] = pair_mkt.loc[each, X_symbol]
                record.loc[each, 'signal_price_y'] = pair_mkt.loc[each, y_symbol]
                record.loc[each, 'actual_price_X'] = X_cash / X_pos if X_pos > 0 else np.nan
                record.loc[each, 'actual_price_y'] = y_cash / y_pos if y_pos > 0 else np.nan
                record.loc[each, 'neg_close_threshold'] = 1
                record.loc[each, 'X_filled_timestamp'] = X_filled_timestamp
                record.loc[each, 'y_filled_timestamp'] = y_filled_timestamp


        # 买入X，卖出y
        if X_position == 0 and pos_open_signal == 1 and spread_series[
            each] > res_std * OPEN_THRESHOLD and not stop_trading:
            print('buy_signal')
            X_pos, X_cash, X_filled, X_filled_timestamp,X_delay,X_order_count = get_order_result(X_symbol, temp_X, shareX, 'B')
            y_pos, y_cash, y_filled, y_filled_timestamp,y_delay,y_order_count = get_order_result(y_symbol, temp_y, sharey, 'S')
            record.loc[each, ['X_delay', 'y_delay', 'X_orders_count', 'y_orders_count']] = [X_delay, y_delay,X_order_count,y_order_count]
            X_position = X_pos
            y_position = -y_pos
            # X_cost += X_cash*cost_rate
            y_cost += y_cash * cost_rate
            cash_part = cash_part + y_cash - X_cash
            record.loc[each, 'pos_signal'] = 1
            record.loc[each, 'signal_price_X'] = pair_mkt.loc[each, X_symbol]
            record.loc[each, 'signal_price_y'] = pair_mkt.loc[each, y_symbol]
            record.loc[each, 'actual_price_X'] = X_cash / X_pos if X_pos > 0 else np.nan
            record.loc[each, 'actual_price_y'] = y_cash / y_pos if y_pos > 0 else np.nan
            record.loc[each, 'X_filled_timestamp'] = X_filled_timestamp
            record.loc[each, 'y_filled_timestamp'] = y_filled_timestamp
        # 买入y，卖出X
        if y_position == 0 and neg_open_signal == 1 and spread_series[
            each] < -res_std * OPEN_THRESHOLD and not stop_trading:
            print('sell_signal')
            # break
            X_pos, X_cash, X_filled, X_filled_timestamp,X_delay,X_order_count = get_order_result(X_symbol, temp_X, shareX, 'S')
            y_pos, y_cash, y_filled, y_filled_timestamp,y_delay,y_order_count = get_order_result(y_symbol, temp_y, sharey, 'B')
            record.loc[each, ['X_delay', 'y_delay', 'X_orders_count', 'y_orders_count']] = [X_delay, y_delay,
                                                                                            X_order_count,
                                                                                            y_order_count]
            X_position = -X_pos
            y_position = y_pos
            X_cost += X_cash * cost_rate
            cash_part = cash_part + X_cash - y_cash
            record.loc[each, 'neg_signal'] = 1

            record.loc[each, 'signal_price_X'] = pair_mkt.loc[each, X_symbol]
            record.loc[each, 'signal_price_y'] = pair_mkt.loc[each, y_symbol]
            record.loc[each, 'actual_price_X'] = X_cash / X_pos if X_pos > 0 else np.nan
            record.loc[each, 'actual_price_y'] = y_cash / y_pos if y_pos > 0 else np.nan
            record.loc[each, 'X_filled_timestamp'] = X_filled_timestamp
            record.loc[each, 'y_filled_timestamp'] = y_filled_timestamp

        # if each != spread_series.index[-1] and type(X_tick) != type(None) and type(y_tick) != type(None):
        #     temp_X = X_tick[X_tick['datetime'] > spread_series.index[i + 1]]
        #     temp_y = y_tick[y_tick['datetime'] > spread_series.index[i + 1]]
        #     temp_X = temp_X.set_index('datetime')
        #     temp_y = temp_y.set_index('datetime')
        # 平仓，卖出X，买入y
        if X_position > 0 and (spread_series[each] < res_std * CLOSE_THRESHOLD or spread_series[each] > res_std * STOP_THRESHOLD):
            X_pos, X_cash, X_filled,X_filled_timestamp,X_delay,X_order_count = get_order_result(X_symbol, temp_X, X_position, 'S')
            y_pos, y_cash, y_filled,y_filled_timestamp,y_delay,y_order_count = get_order_result(y_symbol, temp_y, abs(y_position), 'B')
            record.loc[each, ['X_delay', 'y_delay', 'X_orders_count', 'y_orders_count']] = [X_delay, y_delay,
                                                                                            X_order_count,
                                                                                            y_order_count]
            X_position = X_position - X_pos
            y_position = y_position + y_pos
            X_cost += X_cash * cost_rate
            cash_part = cash_part + X_cash - y_cash

            record.loc[each, 'signal_price_X'] = pair_mkt.loc[each, X_symbol]
            record.loc[each, 'signal_price_y'] = pair_mkt.loc[each, y_symbol]
            record.loc[each, 'actual_price_X'] = X_cash / X_pos if X_pos > 0 else np.nan
            record.loc[each, 'actual_price_y'] = y_cash / y_pos if y_pos > 0 else np.nan
            record.loc[each, 'X_filled_timestamp'] = X_filled_timestamp
            record.loc[each, 'y_filled_timestamp'] = y_filled_timestamp

            if X_position != 0 or y_position != 0:
                print(X_position, X_pos)
                print(y_position, y_pos)
                print('2NOT BALANCE!!!!!!!!!!!!!')
                break
            if spread_series[each] < res_std * CLOSE_THRESHOLD:
                record.loc[each, 'pos_close_threshold'] = 1
            if spread_series[each] > res_std * STOP_THRESHOLD:
                record.loc[each, 'pos_stop_threshold'] = 1
                stop_trading = True
        # 平仓，卖出y，买入X
        if y_position > 0 and (spread_series[each] > -res_std * CLOSE_THRESHOLD or spread_series[each] < -res_std * STOP_THRESHOLD):
            # print('buy_signal')
            X_pos, X_cash, X_filled, X_filled_timestamp,X_delay,X_order_count = get_order_result(X_symbol, temp_X, abs(X_position), 'B')
            y_pos, y_cash, y_filled, y_filled_timestamp,y_delay,y_order_count = get_order_result(y_symbol, temp_y, y_position, 'S')
            record.loc[each, ['X_delay', 'y_delay', 'X_orders_count', 'y_orders_count']] = [X_delay, y_delay,
                                                                                            X_order_count,
                                                                                            y_order_count]
            X_position = X_position + X_pos
            y_position = y_position - y_pos
            # X_cost += X_cash*cost_rate
            y_cost += y_cash * cost_rate
            cash_part = cash_part + y_cash - X_cash
            if X_position != 0 or y_position != 0:
                print(X_position, X_pos)
                print(y_position, y_pos)
                print('1NOT BALANCE!!!!!!!!!!!!!')
                break
            if spread_series[each] > -res_std * CLOSE_THRESHOLD:
                record.loc[each, 'neg_close_threshold'] = 1
            if spread_series[each] < -res_std * STOP_THRESHOLD:
                record.loc[each, 'neg_stop_threshold'] = 1
                stop_trading = True

            record.loc[each, 'signal_price_X'] = pair_mkt.loc[each, X_symbol]
            record.loc[each, 'signal_price_y'] = pair_mkt.loc[each, y_symbol]
            record.loc[each, 'actual_price_X'] = X_cash / X_pos if X_pos > 0 else np.nan
            record.loc[each, 'actual_price_y'] = y_cash / y_pos if y_pos > 0 else np.nan

            record.loc[each, 'X_filled_timestamp'] = X_filled_timestamp
            record.loc[each, 'y_filled_timestamp'] = y_filled_timestamp
        if (X_position == 0 and y_position != 0) or (X_position != 0 and y_position == 0):
            print('error~')
            break

        record.loc[each, [X_symbol, y_symbol]] = [X_position, y_position]
        record.loc[each, ['X_cost', 'y_cost']] = [X_cost, y_cost]
        record.loc[each, 'cash'] = cash_part
    print('节点三', time.time() - e1)
    position_value = (pair_mkt * record[pair_mkt.columns]).rename(
        columns={X_symbol: X_symbol + '_value', y_symbol: y_symbol + '_value'})
    check = pd.concat([position_value, record], axis=1)
    check['account_value'] = check['cash'] + check[X_symbol + '_value'] + check[y_symbol + '_value'] - \
                             check['X_cost'].cumsum() - check['y_cost'].cumsum()
    return check



corr_dict = pd.read_pickle('%s/corr_analysis/corr_dict.pkl'%root_path)
mkt_dict = pd.read_pickle('%s/corr_analysis/mkt_dict.pkl'%root_path)


portfolio_info = pd.read_excel('%s/沪深300反转策略0812.xls'%root_path).T.set_index(0).T
portfolio_info['证券代码'] = portfolio_info['证券代码'].apply(lambda x : str(x).zfill(6)+'.SZ' if float(x)<400000 else str(x)+'.SH')
universe_info = pd.read_excel('%s/研究股票池及沪深300成分股.xlsx'%root_path,sheetname='研究股票池').set_index('代码')
#portfolio_info['一级行业'] = portfolio_info['证券代码'].apply(lambda x : universe_info.loc[x,'一级行业'])
check = pd.concat([portfolio_info.set_index('证券代码'),universe_info],axis=1,join_axes=[portfolio_info.set_index('证券代码').index])

check = check[['一级行业','细分行业']]
ind_list = check.groupby('一级行业').count().index.tolist()
ind_universe = {}
for ind in ind_list:
    ind_universe[ind] = check[check['一级行业']==ind].index.tolist()
    
trading_list = s.tradingday(startTime = '20180801',\
                            endTime = '20190101', frequency='DAY', dayType=None, dateType='TRADINGDAYS')

def seek_para(each):
    print(each)
    cash_ = 1000000
    cost_rate=0.001
    mkdir('%s/pair_trading_tick_adf/seek_para_cost_0.001/'%root_path)
    file_name = 'evaluation_%s.xlsx'%('_'.join(list(map(str,each))))
    file_list = os.listdir('%s/pair_trading_tick_adf/seek_para_cost_0.001/'%root_path)
    if file_name in file_list:
        print(file_name,'exist')
        return 0
    if os.path.exists('%s/pair_trading_tick_adf/seek_para_cost_0.001/evaluation_%s.xlsx'%(root_path,'_'.join(list(map(str,each))))):
        print('exist')
        return 0
    chosed_clust_train = trading_list
    #pd.read_pickle('selected_stk_in_sample.pk')
    try:
        evaluation_train,result_train,net_value_train,stat,_ = get_pair_trading(each[2],chosed_clust_train,cash_,\
                         cost_rate,OPEN_THRESHOLD=each[0],CLOSE_THRESHOLD=each[0]-each[1],STOP_THRESHOLD=each[0]+each[1])
    except:
        return 0
    evaluation_train.index = [str(each)]
    
    evaluation_train.to_excel('%s/pair_trading_tick_adf/seek_para_cost_0.001/evaluation_%s.xlsx'%(root_path,'_'.join(list(map(str,each)))))
    pd.to_pickle(result_train,'%s/pair_trading_tick_adf/seek_para_cost_0.001/result_%s.pkl'%(root_path,'_'.join(list(map(str,each)))))

if __name__=="__main__":
    
    print('start')
    para = []
    for i in range(40,55):
        for j in range(25,35):
            para.append([round(i*0.1,1),round(j*0.1,1),'非银金融'])
            
    for i in range(20,31):
        for j in range(18,28):
            para.append([round(i*0.1,1),round(j*0.1,1),'国防军工'])
    
    for i in range(45,55):
        for j in range(20,31):
            para.append([round(i*0.1,1),round(j*0.1,1),'银行'])
            
    #seek_para(para[0])
    print('start')
    e = time.time()
    pool = Pool(25)
    r = pool.map(seek_para,para)
    pool.close()
    pool.join()
    e1 = time.time()
    print('执行时间:',e1 - e)


    
    


