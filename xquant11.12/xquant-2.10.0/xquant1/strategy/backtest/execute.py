# -*- coding: utf-8 -*-
"""
Created on Thu Oct 18 17:22:28 2018
@author: 013150
"""
import os
from .date_util import time_standard, get_warehouse_transfer_day
from .Account import AccountConfig
from .Context import Context
from .record_util import History
from .hisData2Background import HisData2Background
import time
from .Performance import Performance

def add_history_record(context, account_name):
    account = context.get_account(account_name)
    current_price = context.history.current_price_his.loc[int(context.current_date)]
    #历史成交数据更新
    for pos_symbol in account.get_positions():
        account.update_position(pos_symbol, current_price[pos_symbol], verbose=0)
        context.history.add_position_his(context.current_date, account.get_positions()[pos_symbol])
    account.update_portfolio_value(current_price, verbose = 0)
    context.history.add_account_his(context.current_date, account)

def __instaction(myStrategy,context,start,end):
    """
    存储数据
    :param acount_name : 交易账户
    :param context:
    :return:
    """
    df_name = myStrategy.benchmark[0]
    rf = 0.02
    pf = Performance()
    t = time.time()
    stamp = int(t)
    HB = HisData2Background()
    HB.run(myStrategy,context,start,end,stamp,pf,df_name,rf)



def run(myStrategy):
    """
    接收实例化的Strategy衍生类对象，解析其策略参数，并执行回测逻辑。
    
    **参数**
    
        my
    """
    print('$statistic-log,module=backtest,platform=XQUANT-Cloud')
    stockList = myStrategy.universe
    
    start = myStrategy.start
    end = myStrategy.end
    freq = myStrategy.freq
    refresh_rate = myStrategy.refresh_rate
    
    account_name = myStrategy.account_name
    capital_base = myStrategy.capital_base
    position_base = myStrategy.position_base
    cost_base = myStrategy.cost_base
    acount_commission = myStrategy.acount_commission
    account_slippage = myStrategy.account_slippage
    
    
    startTime = time_standard(start)
    endTime = time_standard(end)
    
    tradingDays = get_warehouse_transfer_day(startTime, endTime, refresh_rate = 1)
    target_term = get_warehouse_transfer_day(startTime, endTime, refresh_rate)
    assert len(tradingDays) > 0 , "所选回测期间无交易日，无法回测，请重新输入！"

    previous_date = tradingDays[0]
    current_date = tradingDays[-1]
        

    accounts = {account_name: AccountConfig(
                    account_type='security', capital_base=capital_base, 
                    position_base = position_base, cost_base = cost_base, 
                    commission = acount_commission, slippage = account_slippage)
            }
    
    #历史信息记录
    history = History(stockList, tradingDays)
    context = Context(current_date, previous_date, tradingDays, accounts, history)
    

    #%%执行逻辑
    account = context.get_account(account_name)

    myStrategy.initialize(context)
   
    for current_date in tradingDays:
        if freq == "d":
            #开盘前操作
            context.update_date(current_date=current_date, previous_date=previous_date)
            if current_date in target_term:
                #盘中操作
                myStrategy.handle_data(context)
                
                #历史委托数据更新
                closing_price = context.history.current_price_his.loc[int(current_date)]#开盘价
                account._after_handle(closing_price, history, current_date)
                
                account = context.get_account(account_name)
                 #历史成交数据更新
                add_history_record(context, account_name)
                
                #盘后指标计算
                myStrategy.post_trading_day(context)
                previous_date = current_date
            else:
                add_history_record(context, account_name)
    # if not os.environ.get('IS_JUPYTER',False):
    #     __instaction(myStrategy,context,tradingDays[0],tradingDays[-1])
    
    print("回测完成！")