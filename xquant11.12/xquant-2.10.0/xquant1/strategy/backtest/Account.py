# -*- coding: utf-8 -*-
"""
Created on Thu Oct 18 14:57:20 2018
@author: 013150
"""
import datetime
from queue import Queue
import sys
import numpy as np


class Commission:
    """
    交易费用设置
    
    **成员变量**
    
        unit取值：perValue: 按照成交金额的百分比收取手续费。perShare: 按成交的股数收取手续费（仅用于期货账号配置），为int型
            
        buycost：买入手续费。
        
        cost：卖出手续费。
    """
    def __init__(self, buycost, sellcost, unit):
        self.__buycost = buycost
        self.__sellcost = sellcost
        self.__unit = unit
        
    def set_buycost(self, buycost):
        self.__buycost = buycost
        
    def set_sellcost(self, sellcost):
        self.__sellcost = sellcost
        
    def set_unit(self, unit):
        self.__unit = unit

    def get_buycost(self):
        return self.__buycost

    def get_sellcost(self):
        return self.__sellcost

    def get_unit(self):
        return self.__unit
    
    """
    按成交金额计算交易费
        **参数**：
        
            trading_amount：成交金额，为正表示买入，为负表示卖出
            
            direction: 交易方向，"buy"表示买入，"sell"表示卖出
            
        **返回**:
            
            交易费用
    """
    def get_perValue_fee(self, trading_amount, direction = "buy"):
        if direction=="buy":
            return np.round(trading_amount*self.__buycost, 2)
        elif direction=="sell":
            return np.round(trading_amount*self.__sellcost,2)
        else:
            print("Commission,get_perValue_fee errors: 计算交易费失败，请输入正确的交易方向!")
            sys.exit()
        

class Slippage:
    '''
    交易滑点设置，用于处理市场冲击问题。
    
    **成员变量**
    
        unit取值：
        perValue: 百分比滑点
        perShare: 固定值股价滑点
        
        value：滑点值，百分比滑点，value取float型，固定值股价滑点，value取int型。
    '''
    def __init__(self, value, unit):
        self.__value = value #
        self.__unit = unit
        
    def set_value(self, value):
        self.__value = value
    
    def set_unit(self, unit):
        self.__unit = unit

    def get_value(self):
        return self.__value

    def get_unit(self):
        return self.__unit



class Position:
    '''
    账户持仓信息，也记录委托单信息。
    
    **成员变量**
        symbol：证券名
        
        amount：持仓数量
        
        cost：平均开仓成本
        
        profit：持仓浮动盈亏
        
        value：持仓市值
        
        extend_amount：买单扩展的持仓，初始化为空list，存的是tuple（数量，价格）
        
        freeze_amount：卖单冻结的持仓，初始化为空list，存的是tuple（数量，价格）
    '''
    def __init__(self, symbol, amount, cost, profit, value):
        self._symbol = symbol
        self._amount = amount#当前时刻实际持仓
        self._extend_amount = Queue()#买单扩展的持仓
        self._freeze_amount = Queue()#卖单冻结的持仓
        self._cost = cost#花费
        self._profit = profit#利润
        self._value = value#总权益
        
    def get_symbol(self):
        return self._symbol
    
    def get_amount(self):
        return self._amount
    
    def get_available_amount(self):
        freeze_amount = 0
        for fz in list(self._freeze_amount.queue):
            freeze_amount = freeze_amount+fz[0]
        return self._amount-freeze_amount
    
    
    def get_extend_amount(self):
        return self._extend_amount
    
    def get_freeze_amount(self):
        return self._freeze_amount
    
    def get_cost(self):
        return self._cost
    
    def get_profit(self):
        return self._profit
    
    def get_value(self):
        return self._value
    
    def print_position(self):
        print("\t代码: %s" % self._symbol,end = ",")
        print("\t持仓数量: %d" % self._amount,end = ",")
        print("\t持仓单价: %.2f" % self._cost, end = ",")
        print("\t个股市值: %.2f" % self._value)


class AccountConfig(Position):
    '''
    回测框架的交易账户配置函数，框架支持多种交易品种，多个交易账户同时进行回测
    
    **成员变量**
    包含7个参数：
        account_type：账户类型，为枚举’security’
        
        capital_base：初始资金，为int型
        
        position_base：初始持仓，为字典型，key为证券名称，value为股数。
        
        cost_base：初始持仓成本，为字典型，key为证券名称，value为float型。
        
        cash：实时总现金
        
        order_cash：下单产生的资金变动，正为卖出订单，负为买入订单
        
        portfolio_value：实时总权益，现金加持仓权益
        
        position：实时仓位
        
        commission：Commission类对象。
        
        slippage：Slippage对象。
        
        margin_rate：保证金比例。为float型。
    ''' 
    def __init__(self, account_type, capital_base, position_base, cost_base, commission, slippage, margin_rate = None):
        self.__account_type = account_type #账户类型
        self.__capital_base = float(capital_base) #初始资金
        self.__position_base = position_base # 初始持仓
        self.__cost_base = cost_base #初始持仓成本
        self.__commission = commission #交易费用
        self.__slippage = slippage #交易滑点
        self.__margin_rate = margin_rate #保证金比例
        
        #实时总现金

        self.__cash = float(capital_base)
        #下单产生的资金变动,正为卖出订单，负为买入订单（）当为正时，代表有一部分资金被冻结

        self.__order_cash = 0.0
        #完成交易产生的交易费用

        self.__transaction_fee = 0.0
        #实时总权益，现金加持仓权益
        self.__portfolio_value = self.__cash
        #实时仓位
        self.__positions = {}
        for symbol,amount in self.__position_base.items():
            assert symbol in self.__cost_base.keys(),"初始持仓和初始成本的证券不统一，position_base, cost_base"
            pos = Position(symbol = symbol, amount = amount, cost = self.__cost_base[symbol], profit = 0, value = 0)
            self.__positions[symbol] = pos
     
    def get_cash(self):
        return self.__cash
    def get_order_cash(self):
        return self.__order_cash
    def get_transaction_fee(self):
        return self.__transaction_fee
    def get_portfolio_value(self):
        return self.__portfolio_value
    def get_positions(self):
        return self.__positions

    def _after_handle(self, opening_price, history, current_date):
        '''
        在执行handle_data后，清算证券交易信息，并根据当天收盘价更新账户权益信息和持仓信息
        **参数**
        
            opening_price:股票池中股票的收盘价
            
            history: 储存回测历史变量信息
            
            current_date：清算日期
        
        **返回**
        
            订单编号
        '''
        # 对每个股票，判断amount和available_amount是否为零，不为零，说明有委托单。然后按全部成交，更护账户和持仓信息。
        for symbol, sub_post in self.__positions.items():
            extend_amount = sub_post.get_extend_amount()
            freeze_amount = sub_post.get_freeze_amount()
            while not extend_amount.empty():
                ex_amount = extend_amount.get()
                buy_cost = ex_amount[0] * ex_amount[1]  # 买入花费cost
                buy_fee = self.__commission.get_perValue_fee(buy_cost, direction="buy")  # 交易费用fee
                if self.__cash - buy_cost - buy_fee < 0:
#                    print("【成交】: transaction warning, 成交失败！买入证券资金不足！清算失败！")
                    return
                
                # 该证券的平均每股交易费用
                sub_post._cost = (sub_post.get_cost() * sub_post.get_amount() + buy_cost + buy_fee) / \
                                 (sub_post.get_amount() + ex_amount[0])
                # 买入股数amount
                sub_post._amount = sub_post.get_amount() + ex_amount[0]
                # 更新总的交易费用
                self.__transaction_fee = buy_fee + self.__transaction_fee
                # 更新持仓信息
                sub_post._extend_amount = extend_amount
                self.__positions[symbol] = sub_post
                # 更改总账户的资金和下单资金
                self.__cash = self.__cash - buy_cost - buy_fee
                self.__order_cash = self.__order_cash - buy_cost - buy_fee

                # 赞为更改value和profit数据，需要依赖实时价格
#                print("【成交】成交买入证券%s，成交买入数量%d，成交单价%.2f，" % (symbol, ex_amount[0], ex_amount[1]))
                history.add_transaction_his(symbol, ex_amount[1], ex_amount[0],
                                             buy_cost, buy_cost + buy_fee, current_date,1,ex_amount[2])
                
            while not freeze_amount.empty():
                fr_amount = freeze_amount.get()
                sell_cost = fr_amount[0] * fr_amount[1]  # 卖出收入
                sell_fee = self.__commission.get_perValue_fee(sell_cost, direction="sell")
                if  sub_post._amount - fr_amount[0] < 0:
#                    print("【成交】: transaction warning, 卖出股票数超出持仓！清算失败！")
                    return
                
                # 买入股数amount
                sub_post._amount = sub_post._amount - fr_amount[0]
                # 更新总的交易费用
                self.__transaction_fee = sell_fee + self.__transaction_fee
                # 更新持仓信息
                sub_post._freeze_amount = freeze_amount
                self.__positions[symbol] = sub_post
                # 更改总账户的资金
                self.__cash = self.__cash + sell_cost - sell_fee

                # 赞为更改value和profit数据，需要依赖实时价格
#                print("【成交】成交卖出证券%s，成交卖出数量%d，成交单价%.2f，" % (symbol, fr_amount[0], fr_amount[1]))
                history.add_transaction_his(symbol, fr_amount[1], -fr_amount[0],
                                            -sell_cost, -sell_cost + sell_fee, current_date,2,fr_amount[2])
        print("- - - - - - - - - - - - - - - - -"+str(current_date)+"- - - - - - - - - - - - - - - ")
        self.print_accounts(opening_price)
        
    
  
    def order(self, symbol, amount, price, context,order_type = "market", offset_flag = None):
        '''
        下单函数
        
        **参数**
        
            symbol:证券代码
            
            amount: 证券数量，买入为正，卖出为负
            
            price：限价单时为挂单价，市价单时为实时行情
            
            current_date：当前交易日
            
            context：回测上下文变量
            
            order_type:"market"市价单，"limit"限价单
            
            offset_flag:期货平仓方向，仅用于期货策略，"open"开仓，"close"平仓
        
        **返回**
        
            订单编号
        '''
        amount = int(amount)#股数为整数
        order_id = "E" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")#全局唯一，包含时间顺序
        if offset_flag == None:
            #股票下单
            if order_type=="market":
                if symbol in self.__positions.keys():
                    post= self.__positions[symbol]
                    if amount > 0:
                        #预计下单金额
                        expect_buy_cost = amount*price
                        expect_buy_fee = self.__commission.get_perValue_fee(expect_buy_cost, direction = "buy")#交易费用fee
                        if self.__cash-expect_buy_cost-expect_buy_fee < 0:
                            print("【警告】: 对证券%s的委托买单金额为%.2f元，资金不足！下单失败！" % (symbol,expect_buy_cost))
                            return
                        #增加委托买单和冻结资金
                        post._extend_amount.put((amount, price,order_id))
                        self.__order_cash = self.__order_cash+expect_buy_cost+expect_buy_fee#资金冻结
                    
                        context.history.add_order_his(context.current_date, symbol, price, amount, 1, expect_buy_fee,order_id)
                        print("【当日委托】买入证券%s，买入数量%d，价格%.2f。" % (symbol, amount, price))
                    elif amount<0:
                        #预计下单金额
                        expect_sell_cost = -amount*price
                        expect_sell_fee = self.__commission.get_perValue_fee(expect_sell_cost, direction = "sell")#交易费用fee
                        if post._amount+amount<0:
                            print("【警告】: 对证券%s的委托卖单为%d股，已超出持仓！下单失败！" % (symbol, -amount))
                            return
                        #增加委托卖单
                        post._freeze_amount.put((-amount, price,order_id))
                        context.history.add_order_his(context.current_date, symbol, price, amount, 2, expect_sell_fee,order_id)
                    
                        print("【当日委托】卖出证券%s，卖出数量%d，价格%.2f。" % (symbol, -amount, price))
                    else:
                        return

                else:
                    if amount > 0:
                        #预计下单金额
                        expect_buy_cost = amount*price
                        expect_buy_fee = self.__commission.get_perValue_fee(expect_buy_cost, direction = "buy")#交易费用fee
                        if self.__cash-expect_buy_cost-expect_buy_fee < 0:
                            print("【警告】: 对证券%s的委托买单金额为%.2f元，资金不足！下单失败！" % (symbol,expect_buy_cost))
                            return
                        #增加委托买单和冻结资金
                        self.__order_cash = self.__order_cash+expect_buy_cost+expect_buy_fee#资金冻结
                        self.__positions[symbol] = Position(symbol, 0, 0, 0, 0)
                        self.__positions[symbol]._extend_amount.put((amount, price,order_id))
                      
                        context.history.add_order_his(context.current_date, symbol, price, amount, 1, expect_buy_fee,order_id)
                        print("【当日委托】买入证券%s，买入数量%d，价格%.2f。。" % (symbol, amount, price))
                    else:
                        print("【警告】持仓不包含股票%s，无法执行委托卖单！" % symbol)
                
            elif order_type == "limit":
                pass
            else:
                sys.exit("【警告】下单失败！请输出正确的下单类型：market市价单，或limit限价单两种") 
                
        else:
            #期货下单
            pass
        return order_id
    

    def update_position(self, symbol, current_price, verbose=1):
        '''
        根据当前收盘价，计算某个股票权益和收益，并返回该股票的仓位。
        
        某个股票当前权益：value = current_price*position.amount
        
        某个股票当前的利润：profit = value-position.amount*position.cost
        
        **参数**
        
            symbol：证券名称
            current_price: 当前证券价格
            verbose：大于0，打印持仓信息
            
        **返回**
        
            Position对象
        '''
        post = self.__positions[symbol]
        post._value = post._amount*current_price
        post._profit = post._value-post._cost*post._amount
        self.__positions[symbol] = post
        if verbose>0:
            post.print_position()
        return post
    
    
    def print_accounts(self, current_price):
        '''
        输出当前股价下的账户信息，包括各个股票的持仓，实时掌账户金额，冻结资金，交易总手续费
        
        **参数**
        
            current_price_dict:当前时刻的股票股价
            
        '''
        print("【实时持仓】")
        for symbol, post in self.__positions.items():
            self.update_position(symbol, current_price[symbol], verbose = 1)
        print("【权益信息】")
        print("\t实时账户余额：%.2f" % self.__cash)
        print("\t持仓市值：%.2f" % (self.update_portfolio_value(current_price, verbose = 0)-self.__cash))
        print("\t实时交易总手续费：%.2f" % self.__transaction_fee)

        print("\t实时总权益： %.2f" % self.update_portfolio_value(current_price, verbose = 0))
        

    def update_portfolio_value(self, current_price, verbose = 0):
        '''
        获得当前股价下的账户总权益
        
        **参数**
        
            current_price: 当前时刻的股票股价。Series，columns为股票代码，值为收盘价。
            verbose: 大于零打印当前权益值。
            
        **返回**
            portfolio_value：当前股价下的账户总权益
        '''



        portfolio_value = self.__cash
        for symbol,post in self.__positions.items():
            tmp_price = 0
            try:
                tmp_price = current_price[symbol]
            except Exception as e:
                sys.exit("update_portfolio_value error: 获取实时账户权益失败！请正确传入持仓所有证券的当前价格！证券名称信息不存在。")
            portfolio_value = portfolio_value+post._amount*tmp_price
        self.__portfolio_value = portfolio_value
        
        if verbose>0:
            print("获得当前股价下的账户总权益为：%.2f" % portfolio_value)
        return self.__portfolio_value