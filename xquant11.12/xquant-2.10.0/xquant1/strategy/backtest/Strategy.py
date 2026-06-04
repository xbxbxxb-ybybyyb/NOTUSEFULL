# -*- coding: utf-8 -*-
"""
Created on Mon Oct  8 15:04:21 2018
@author: 013150
"""
from abc import ABCMeta,abstractmethod

"""
用户可调用函数
"""
class Strategy(metaclass=ABCMeta):
    
    def __init__(self):
        self.start = None
        self.end = None
        self.universe  = None
        self.freq = None
        self.refresh_rate = None
        self.account_name = None
        self.benchmark = None
        
        self.capital_base = None
        self.position_base = None#{'600232.SH':10000, '600252.SH':10000}
        self.cost_base = None#{'600232.SH':10.05, '600252.SH':9.85}
        self.acount_commission = None#self.Commission(buycost=0.001, sellcost=0.002, unit='perValue')
        self.account_slippage = None#self.Slippage(value=0.0, unit='perValue')

        self.__load_moudles()
        
        
    def __load_moudles(self):
        from .Account import Commission, Slippage
        
        self.Commission = Commission
        self.Slippage = Slippage
        
    @abstractmethod
    def initialize(context):
        '''
        策略执行前初始化，只调用一次
        '''
        pass
    
    @abstractmethod
    def handle_data(context):
        '''
        执行策略，每个换仓日调用一次
        '''
        pass
    
    @abstractmethod
    def post_trading_day(context):
        '''
        策略盘后处理逻辑，如当日交易总结，预计算因子等，handle_data之后执行
        '''
        pass