# -*- coding: utf-8 -*-
"""
Created on Mon Nov  5 16:20:29 2018
@author: 013150
"""

import pandas as pd
import copy
import itertools

class History:
    """
    **参数**
    account_his：账户的历史信息，包括每个换仓期的账户现金，下单冻结资金，和账户总权益
    position_his：账户的历史持仓信息，包括每个换仓期，每只股票的数量、交易价格、收益、当前价值，和冻结股数
    benchmark_his：历史的基准信息
    """
    
    def __init__(self, stockList, target_term):
        self.account_his = pd.DataFrame(index=target_term, columns=["cash", "order_cash", "portfolio_value"])
        
        m_index1=pd.Index(list(itertools.product(target_term, stockList)),name=["dateTime","symbol"])
        self.position_his = pd.DataFrame(index = m_index1,
                                columns = ["amount", "cost", "profit", "value", "freeze_amount"])
        
        self.benchmark_his = None
        self.current_price_his = None
        self.order_his = pd.DataFrame(columns=["stock_code", "entrust_price", "entrust_amount",
                                               "entrust_bs","entrust_no","business_price", "business_amount",
                                               "business_balance", "clear_balance", "trade_date"])
        self.transaction_his = pd.DataFrame(columns=["date", "stock_code", "business_price", "business_amount",
                                                     "business_balance", "clear_balance","entrust_bs","order_id"])
        self.benefit_monthly = pd.DataFrame(columns=[
            "clear_date","last1m_return_rate","last3m_return_rate","last6m_return_rate",
            "last12m_return_rate","last1m_benchmark_return_rate","last3m_benchmark_return_rate",
            "last6m_benchmark_return_rate","last12m_benchmark_return_rate",
            "last1m_alpha","last3m_alpha","last6m_alpha","last12m_alpha",
            "last1m_beta","last3m_beta","last6m_beta","last12m_beta","last1m_sharpe",
            "last3m_sharpe","last6m_sharpe","last12m_sharpe","last1m_volatility",
            "last3m_volatility","last6m_volatility","last12m_volatility","last1m_info_ratio",
            "last3m_info_ratio","last6m_info_ratio","last12m_info_ratio","last1m_max_drawdown",
            "last3m_max_drawdown","last6m_max_drawdown","last12m_max_drawdown"
        ])

        self.daily_cost_benefit = pd.DataFrame(columns=["instance_id", "fund_account", "asset_value",
                                                        "benchmark_price", "return_rate", "benchmark_return_rate",
                                                        "alpha_return_rate", "clear_date"])

        self.instance_cost_benefit = pd.DataFrame()

    def add_account_his(self, dateTime, account):
        #记录账户信息
        cash, order_cash, portfolio_value = account.get_cash(), account.get_order_cash(), account.get_portfolio_value()
        self.account_his.loc[dateTime] = [cash, order_cash, portfolio_value]

        
        
    def add_position_his(self, dateTime, position):
        #记录持仓信息
        symbol, amount,freeze_amount,cost,profit,value = position.get_symbol(), position.get_amount(), \
            position.get_freeze_amount(), position.get_cost(), position.get_profit(), position.get_value()
        tmp_freeze_amount = copy.copy(freeze_amount)
        self.position_his.loc[dateTime, symbol] = [amount,cost,profit,value, sum(list(tmp_freeze_amount.queue))]

    def add_order_his(self,trade_date,stock_code,entrust_price,entrust_amount,entrust_bs,buy_fee,entrust_no):
        # 记录委托下单信息
        business_price = entrust_price
        business_amount = entrust_amount
        business_balance = business_amount * business_price
        clear_balance = entrust_amount * entrust_price + buy_fee
        order_info_dict = {"stock_code":[stock_code],"entrust_price":[entrust_price],"entrust_amount":[entrust_amount],
                           "entrust_bs":[entrust_bs],"entrust_no":[entrust_no],"business_price":[business_price],"business_amount":[business_amount],
                           "business_balance":[business_balance],"clear_balance":[clear_balance],"trade_date":[trade_date]}
        self.order_his = self.order_his.append(pd.DataFrame(order_info_dict),ignore_index=True)


    def add_transaction_his(self,stock_code,business_price,business_amount,business_balance,clear_balance,date,entrust_bs,order_id):
        self.transaction_his = self.transaction_his.append(pd.DataFrame({
            "date":date,
            "stock_code":[stock_code],
            "business_price":[business_price],
            "business_amount":[business_amount],
            "business_balance":[business_balance],
            "clear_balance":[clear_balance],
            "entrust_bs":[entrust_bs],
            "order_id":[order_id]
        }))

    def add_benefit_monthly(self,Pr,Bn,beta,alpha,SR,vol,InformationRatio,MaxDrawDown,clear_date):
        self.benefit_monthly = self.benefit_monthly.append(
            pd.DataFrame(
                {
                "clear_date":[clear_date],
                "last1m_return_rate":[Pr[0]],
                "last3m_return_rate":[Pr[1]],
                "last6m_return_rate":[Pr[2]],
                "last12m_return_rate":[Pr[3]],
                "last1m_benchmark_return_rate":[Bn[0]],
                "last3m_benchmark_return_rate":[Bn[1]],
                "last6m_benchmark_return_rate":[Bn[2]],
                "last12m_benchmark_return_rate":[Bn[3]],
                "last1m_alpha":[alpha[0]],
                "last3m_alpha":[alpha[1]],
                "last6m_alpha":[alpha[2]],
                "last12m_alpha":[alpha[3]],
                "last1m_beta":[beta[0]],
                "last3m_beta":[beta[1]],
                "last6m_beta":[beta[2]],
                "last12m_beta":[beta[3]],
                "last1m_sharpe":[SR[0]],
                "last3m_sharpe":[SR[1]],
                "last6m_sharpe":[SR[2]],
                "last12m_sharpe":[SR[3]],
                "last1m_volatility":[vol[0]],
                "last3m_volatility":[vol[1]],
                "last6m_volatility":[vol[2]],
                "last12m_volatility":[vol[3]],
                "last1m_info_ratio":[InformationRatio[0]],
                "last3m_info_ratio":[InformationRatio[1]],
                "last6m_info_ratio":[InformationRatio[2]],
                "last12m_info_ratio":[InformationRatio[3]],
                "last1m_max_drawdown":[MaxDrawDown[0]],
                "last3m_max_drawdown":[MaxDrawDown[1]],
                "last6m_max_drawdown":[MaxDrawDown[2]],
                "last12m_max_drawdown":[MaxDrawDown[3]]
        }
            )
        )

    def add_daily_cost_benefit(self,dataSet):
        # 记录每日收益数据
        df = pd.DataFrame(dataSet,columns = ["instance_id","fund_account","asset_value",
                                                         "benchmark_price","return_rate","benchmark_return_rate",
                                                         "alpha_return_rate","clear_date"])

        self.daily_cost_benefit = self.daily_cost_benefit.append(df,ignore_index=True)
        self.daily_cost_benefit.set_index("clear_date",inplace=True)

    def add_instance_cost_benefit(self,df):
        # 实例收益表
        self.instance_cost_benefit = self.instance_cost_benefit.append(df,ignore_index=True)