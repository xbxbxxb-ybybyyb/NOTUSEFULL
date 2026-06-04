# -*- coding: utf-8 -*-
"""
Created on Fri Oct 19 09:42:00 2018

@author: 013150
"""
import sys

class Context:
    '''
    策略运行上下文，支持调用策略运行时的各种信息。
    '''

    def __init__(self, current_date, previous_date, tradingDays, accounts, history):
        self.now = None #策略运行的当前时刻
        pass
        self.current_date = current_date #当前回测日期
        self.previous_date = previous_date #当前回个日期的前一交易日
        self.accounts = accounts #交易账号
        self.history = history
        self.tradingDays = tradingDays
        

    def update_date(self, now=None, current_date=None, accounts = None, previous_date=None, tradingDays = None):
        '''
        更新策略运行的当前时间
        '''
        if now!=None:
            self.now = now
        if current_date!=None:
            self.current_date = current_date
        if previous_date!=None:
            self.previous_date = previous_date
        if accounts!=None:
            self.accounts = accounts
        if tradingDays!=None:
            self.tradingDays = tradingDays
        
    def set_account(self, account_name, accountConfig):
        '''
        设置交易账户
        '''
        self.accounts[account_name] = accountConfig
    
    def get_account(self, account_name):
        '''
        根据账户名获取交易账户
        
        **参数**
            account_name：账户名
            
        **返回**
            
            AccountConfig类对象
        '''
        try:
            return self.accounts[account_name]
        except:
            sys.exit("get_account error：获取账户失败！该账户名称不存在！")
            
    def update_account_commission(self, account_name, buycost=None, sellcost =None, unit = None):
        '''
        更新交易费用设置
        '''
        if buycost!=None:
            self.accounts[account_name].commission.set_buycost(buycost)
        if sellcost!=None:
            self.accounts[account_name].commission.set_sellcost(sellcost)
        if unit!=None:
            self.accounts[account_name].commission.set_unit(unit)
        
        
    def update_account_slippage(self, account_name, value = None, unit = None):
        '''
        更新滑点设置
        '''
        if value!=None:
            self.accounts[account_name].slippage.set_value(value)
        if unit!=None:
            self.accounts[account_name].slippage.set_unit(unit)
            

    def get_universe(self, plate_type, plate_ID, exclude_halt=False):
        '''
        参数：
            plate_type:资产类型，'stock'股票列表、'index'指数成分股列表
            plate_ID: 当plate_type为index时，plate_ID为1：沪深300,2：中证500,3：上证50。
            exclude_halt:去除资产池中的停牌股票，仅适用于股票，默认为False
        '''
        import xquant1.quant as xq
        t = []
        if plate_type=="stock":
            t = xq.hset(xq.PlateType.MARKET,str(self.current_date), xq.MarketType.ALLA)
        elif plate_type=="index":
            if plate_ID==1:
                t = xq.hset(xq.PlateType.INDEX, str(self.current_date), xq.IndexType.HS300)
            if plate_ID==2:
                t = xq.hset(xq.PlateType.INDEX, str(self.current_date), xq.IndexType.ZZ500)
            if plate_ID==3:
                t = xq.hset(xq.PlateType.INDEX, str(self.current_date), xq.IndexType.SH50)
        if exclude_halt==True:
            t = xq.stockFilter(t, str(self.current_date))
        return t[0]