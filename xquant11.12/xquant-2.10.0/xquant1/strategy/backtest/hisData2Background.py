import math
import time
import numpy as np
import pymysql
import datetime
import json
import pandas as pd
import sys
from .mysqlConfig import host,user,password,db,port

class HisData2Background(object,):
    def __init__(self):
        self.conn = pymysql.connect(host=host,user=user,password=password,db=db,charset='utf8',port=port,cursorclass=pymysql.cursors.DictCursor)
        self.cursor = self.conn.cursor()
        self.commit = self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()

    def __handle_mysql(self,tablename,values,columns):
        sql = "insert into %s (%s)"%(tablename,columns) + " values("
        params = "%s," * len(values[0])
        sql = sql + params[:-1] + ")"
        # print(len(values[0]))
        # print(sql)
        # print(values)
        # return
        if len(values) == 1:
            self.cursor.execute(sql,values[0])
        else:
            self.cursor.executemany(sql,values)
        self.conn.commit()

    def __select_symbol_name(self,symbol_code):
        symbol_list = symbol_code.split(".")
        if symbol_list[1].lower() == "sz":
            exchange_code = "105"
        else:
            exchange_code = "101"
        new_symbol_code = symbol_list[0]
        sql = "select symbol_name from symbol_meta where symbol_code='%s' and exchange_code ='%s'"%(new_symbol_code,exchange_code)
        self.cursor.execute(sql)
        value = self.cursor.fetchone()
        symbol_name = value["symbol_name"]
        return symbol_name

    def __delete_nan(self,datalist):
        for value in datalist:
            for data in value:
                if type(data) == float:
                    if math.isnan(data):
                        value[value.index(data)] = None
        return datalist

    def back_test_job(self, myStrategy, start, end,stamp):
        columns = "back_test_id,job_id,user_account,Start_time,End_time"
        job_id = sys.argv[6]
        back_test_id = stamp + int(job_id)
        user_account = myStrategy.account_name
        Start_time = datetime.datetime.strptime(str(start), "%Y%m%d")
        End_time = datetime.datetime.strptime(str(end), "%Y%m%d")
        data_list = [(back_test_id,job_id, user_account, Start_time, End_time)]
        if data_list:
            self.__handle_mysql('back_test_job', data_list, columns)
#        print("back_test_job ok!")

    def back_test_instance(self,myStrategy,stamp):
        """
        存储策略实例表
        :param myStrategy: myStrategy类实例
        :param stamp: 时间戳
        :return:
        """
        job_id = sys.argv[6]
        back_test_id = stamp + int(job_id)
        benchmark = myStrategy.benchmark[0]
        commission = {'buycost':myStrategy.acount_commission.get_buycost(),
                      'sellcost':myStrategy.acount_commission.get_sellcost(),
                      'unit':myStrategy.acount_commission.get_unit()}
        slippage = {'value':myStrategy.account_slippage.get_value(),
                    'unit':myStrategy.account_slippage.get_unit()}
        init_dict = {'start':myStrategy.start,'end':myStrategy.end,'freq':myStrategy.freq,
                     'refresh_rate':myStrategy.refresh_rate,'universe':myStrategy.universe,
                     'benchmark':myStrategy.benchmark,'account_name':myStrategy.account_name,
                     'capital_base':myStrategy.capital_base,'position_base':myStrategy.position_base,
                     'cost_base':myStrategy.cost_base,'acount_commission':commission,
                     'account_slippage':slippage}
        json_str = json.dumps(init_dict)
        values = [[stamp,back_test_id,str(stamp),json_str,benchmark]]
        columns = "instance_id,back_test_id,instance_no,params,benchmark"
        if values:
            self.__handle_mysql('back_test_instance',values,columns)
#        print("back_test_instance Completed !")

    def daily_fund_real(self,myStrategy,stamp,context):
        """
        存储每日盘后资金表
        :param account_name: 账户名
        :param stamp: 时间戳
        :param account_his: 账户历史明细
        :return:
        """
        account_his = context.history.account_his
        account_df = account_his.copy()
        account_df["fund_account"] = myStrategy.account_name
        account_df["instance_id"] = stamp
        account_df.rename(columns={'cash':'enable_amount','order_cash':'frozen_amount'},inplace=True)
        account_df["market_value"] = account_df["portfolio_value"] - account_df["enable_amount"]
        label_list = ["instance_id","fund_account","enable_amount","frozen_amount","market_value","clear_date"]
        dataSet = []
        for index,d_data in account_df.iterrows():
            index = datetime.datetime.strptime(str(index),"%Y%m%d")
            day_data = []
            for i in label_list:
                if i == "clear_date":
                    day_data.append(index)
                elif i == "enable_amount" or i == "frozen_amount" or i == "market_value":
                    day_data.append(round(float(d_data[i]),2))
                else:
                    day_data.append(d_data[i])
            dataSet.append(list(day_data))
        columns = "instance_id,fund_account,enable_amount,frozen_amount,market_value,clear_date"
        dataSet = self.__delete_nan(dataSet)
        if dataSet:
            dataSet = self.__delete_nan(dataSet)
            self.__handle_mysql('daily_fund_real',values=dataSet,columns=columns)
#        print('daily_fund_real Completed !')

    def fund_account(self, stamp, myStrategy, context):
        '''
         存储账户资金表
         :param stamp: 时间戳
         :param myStrategy: myStrategy类实例
         :param context: context类实例
        :return:
        '''
        columns = "instance_id,fund_account,account_type,money_type," \
                  "current_amount,init_amount,enable_amount,frozen_amount," \
                  "market_value,commission,slippage"
        data = context.history.account_his
        instance_id = stamp
        fund_account = myStrategy.account_name
        account_type = 0
        money_type = 1
        current_amount = round(float(data.iloc[-1].loc["cash"]),2)
        init_amount = myStrategy.capital_base
        enable_amount = round(float(data.iloc[-1].loc["cash"] - data.iloc[-1].loc["order_cash"]),2)
        frozen_amount = round(float(data.iloc[-1].loc["order_cash"]),2)
        market_value = round(float(data.iloc[-1].loc["portfolio_value"]),2)
        commission_dict = {
            "buycost": myStrategy.acount_commission.get_buycost(),
            "sellcost": myStrategy.acount_commission.get_sellcost(),
            "unit": myStrategy.acount_commission.get_unit()
        }
        commission_json = json.dumps(commission_dict)
        slippage_dict = {
            "value": myStrategy.account_slippage.get_value(),
            "unit": myStrategy.account_slippage.get_unit()
        }
        slippage_json = json.dumps(slippage_dict)
        data_list = [
            [instance_id, fund_account, account_type, money_type,
             current_amount, init_amount, enable_amount, frozen_amount,
             market_value, commission_json, slippage_json]
        ]
        data_list = self.__delete_nan(data_list)
        if data_list:
            self.__handle_mysql("fund_account", data_list, columns)
#        print("fund_account ok!")


    def stock_real(self,myStrategy,context,stamp):
        '''
        存储账户持仓表
        :param myStrategy: myStrategy类实例
        :param context: context类实例
        :param stamp: 时间戳
        :return:
        '''
        columns = "instance_id,fund_account,market_type,stock_code,stock_name," \
                  "current_amount,enable_amount,frozen_amount," \
                  "average_price,close_price,market_value"
        data_list = []
        account_price = context.history.current_price_his
        account_panel = context.history.position_his
        instance_id = stamp
        fund_account = myStrategy.account_name
        market_type = 0
        date = account_panel.index.levels[0][-1]
        symbols = account_panel.loc[date].index
        for symbol in symbols:
            stock_code = symbol
            stock_name = self.__select_symbol_name(symbol)
            current_amount = float(account_panel.loc[date].loc[symbol].loc["amount"])
            enable_amount = float(account_panel.loc[date].loc[symbol].loc["amount"] - account_panel.loc[date].loc[symbol].loc["freeze_amount"])
            frozen_amount = float(account_panel.loc[date].loc[symbol].loc["freeze_amount"])
            average_price = round(float(account_panel.loc[date].loc[symbol].loc["cost"]),2)
            close_price = round(float(account_price.loc[date].loc[symbol]),2)
            market_value = float(account_price.loc[date].loc[symbol] * account_panel.loc[date].loc[symbol].loc["amount"])
            data_list.append(
                [
                    instance_id,
                    fund_account,
                    market_type,
                    stock_code,
                    stock_name,
                    current_amount,
                    enable_amount,
                    frozen_amount,
                    average_price,
                    close_price,
                    market_value
                ])
        if data_list:
            data_list = self.__delete_nan(data_list)
            new_datalist = data_list[:]
            for data in new_datalist:
                if not data[-6]:
                    data_list.remove(data)
            self.__handle_mysql("stock_real",data_list,columns)
#        print("stock_real ok!")


    def daily_stock_real(self,myStrategy,stamp,context):
        '''
        存储每日持仓表
        :param myStrategy: myStrategy类实例化
        :param stamp: 时间戳
        :param context：Context类实例化
        :return:
        '''
        position_his = context.history.position_his
        current_price_his = context.history.current_price_his
        position_df = position_his.copy()
        position_df.rename(columns={"amount":"enable_amount","freeze_amount":"frozen_amount","cost":"average_price",
                                     "value":"market_value"},inplace=True)
        position_df["instance_id"] = stamp
        position_df["fund_account"] = myStrategy.account_name
        position_df["current_amount"] = position_df["enable_amount"] + position_df["frozen_amount"]
        position_df["market_type"] = 0
        label_list = ["instance_id","fund_account","market_type","stock_code","stock_name","current_amount",
                      "enable_amount","frozen_amount","average_price","daily_close_price",
                       "market_value","clear_date"]
        position_df.dropna(thresh=6, inplace=True)
        sort_key = list(position_df.index.levels[0]).index
        date_index = sorted(list(set(position_df.index.droplevel(1))), key=sort_key)
        dataSet = []
        for day_date in date_index:
            day_Set = []
            for stock,d_data in position_df.loc[day_date].iterrows():
                clear_date = datetime.datetime.strptime(str(day_date), "%Y%m%d")
                stock_Set = []
                for i in label_list:
                    if i == "stock_code":
                        stock_Set.append(stock)
                    elif i == "stock_name":
                        stock_Set.append(self.__select_symbol_name(stock))
                    elif i == "clear_date":
                        stock_Set.append(clear_date)
                    elif i == "daily_close_price":
                        stock_Set.append(float(current_price_his.loc[day_date,stock]))
                    elif i == "average_price":
                        stock_Set.append(float(d_data[i]))
                    elif i == "market_value":
                        stock_Set.append(round(float(d_data[i]),2))
                    else:
                        stock_Set.append(d_data[i])
                day_Set.append(list(stock_Set))
            dataSet.extend(day_Set)
        columns = "instance_id,fund_account,market_type,stock_code,stock_name," \
                  "current_amount,enable_amount,frozen_amount," \
                  "average_price,daily_close_price,market_value,clear_date"
        if dataSet:
            dataSet = self.__delete_nan(dataSet)
            self.__handle_mysql("daily_stock_real",dataSet,columns)
#        print("daily_stock_real Complete !")


    def trade_entrust(self,stamp,myStrategy,context):
        """
        存储委托表
        :param stamp: 时间戳
        :param myStrategy: myStrategy类实例
        :param context: Context类实例
        :return:
        """
        order_his = context.history.order_his
        order_df = order_his.copy()
        order_df["instance_id"] = stamp
        order_df["fund_account"] = myStrategy.account_name
        order_df["market_type"] = 0
        order_df["entrust_type"] = 0
        order_df["entrust_status"] = 8
        order_df["price_type"] = 0
        # 暂无撤单
        order_df["withdraw_amount"] = 0
        order_df["brokerage"] = order_df["clear_balance"] - order_df["business_balance"]
        stock_names = []
        for stock in order_df["stock_code"]:
            stock_names.append(self.__select_symbol_name(stock))
        order_df["stock_name"] = stock_names
        label_list = ["instance_id","fund_account","market_type","stock_code","stock_name",
                      "entrust_price","entrust_amount","entrust_bs","entrust_type","entrust_status","price_type","entrust_no","business_price",
                      "business_amount","business_balance","clear_balance","withdraw_amount","trade_date","brokerage"]
        dataSet = []
        for index, d_data in order_df.iterrows():
            day_data = []
            for i in label_list:
                if i == "trade_date":
                    day_data.append(datetime.datetime.strptime(str(d_data[i]), "%Y%m%d"))
                else:
                    day_data.append(d_data[i])
            dataSet.append(list(day_data))
        columns = "instance_id,fund_account,market_type,stock_code,stock_name," \
                  "entrust_price,entrust_amount,entrust_bs,entrust_type,entrust_status,price_type,entrust_no,business_price," \
                  "business_amount,business_balance,clear_balance,withdraw_amount,trade_date,brokerage"
        if dataSet:
            dataSet = self.__delete_nan(dataSet)
            self.__handle_mysql("trade_entrust",dataSet,columns)
#        print("trade_entrust Complete !")


    def trade_real(self,stamp,myStrategy,context):
        '''
        存储成交表
        :param stamp: 时间戳
        :param myStrategy: myStrategy类实例
        :param context: context类实例
        :return:
        '''
        columns = "instance_id,fund_account,market_type,stock_code,stock_name," \
                  "business_price,business_amount,business_balance," \
                  "clear_balance,business_time,real_type,real_status,entrust_bs," \
                  "entrust_type,price_type,entrust_no,business_no,trade_date,brokerage"
        data_list = []
        transaction_his = context.history.transaction_his
        instance_id = stamp
        fund_account = myStrategy.account_name
        market_type = 0
        real_type = 0
        real_status = 0
        entrust_type = 0
        price_type = 0
        business_no = "B" + str(stamp)
        for num in range(len(transaction_his)):
            stock_code = transaction_his.iloc[num]["stock_code"]
            entrust_no = transaction_his.iloc[num]["order_id"]
            stock_name = self.__select_symbol_name(stock_code)
            business_price = round(float(transaction_his.iloc[num]["business_price"]),2)
            business_amount = float(transaction_his.iloc[num]["business_amount"])
            business_balance = round(float(transaction_his.iloc[num]["business_balance"]),2)
            clear_balance = round(float(transaction_his.iloc[num]["clear_balance"]),2)
            brokerage = clear_balance - business_balance
            trade_date = datetime.datetime.strptime(str(transaction_his.iloc[num]["date"]), "%Y%m%d")
            business_time = datetime.datetime.strptime(str(transaction_his.iloc[num]["date"]) + " 09:30:00", "%Y%m%d %H:%M:%S")
            entrust_bs = transaction_his.iloc[num]["entrust_bs"]
            data_list.append(
                [
                    instance_id, fund_account, market_type, stock_code,stock_name,
                    business_price, business_amount, business_balance,
                    clear_balance, business_time, real_type, real_status, entrust_bs,
                    entrust_type, price_type, entrust_no, business_no, trade_date, brokerage
                ]
            )
        if data_list:
            data_list = self.__delete_nan(data_list)
            self.__handle_mysql("trade_real", data_list,columns)
#        print("trade_real ok!")


    def cost_benefit_analysis(self, stamp, myStrategy, context,pf,df_name,rf):
        '''
        存储收益分析表
        :param stamp: 时间戳
        :param myStrategy: myStrategy类实例
        :param context: context类实例
        :param end: 终止日期
        :param pf: Performance类实例
        :param df_name:
        :param rf: 无风险收益率
        :return:
        '''
        columns = "Instance_id,fund_account,clear_date,market_value," \
                  "current_balance,asset_value,last1m_return_rate," \
                  "last3m_return_rate,last6m_return_rate,last12m_return_rate," \
                  "last1m_benchmark_return_rate,last3m_benchmark_return_rate," \
                  "last6m_benchmark_return_rate,last12m_benchmark_return_rate," \
                  "last1m_excess_return_rate,last3m_excess_return_rate," \
                  "last6m_excess_return_rate,last12m_excess_return_rate," \
                  "last1m_alpha,last3m_alpha,last6m_alpha,last12m_alpha,last1m_beta," \
                  "last3m_beta,last6m_beta,last12m_beta,last1m_sharpe,last3m_sharpe," \
                  "last6m_sharpe,last12m_sharpe,last1m_volatility,last3m_volatility," \
                  "last6m_volatility,last12m_volatility,last1m_info_ratio," \
                  "last3m_info_ratio,last6m_info_ratio,last12m_info_ratio," \
                  "last1m_max_drawdown,last3m_max_drawdown,last6m_max_drawdown," \
                  "last12m_max_drawdown"
        account_df = context.history.account_his
        data_Annualized = account_df["portfolio_value"]
        account_price = context.history.current_price_his
        data_Benchmark = account_price[df_name]
        tradingDays = context.tradingDays[::-20]
        if context.tradingDays.index(tradingDays[-1])<19:
            tradingDays = tradingDays[:-1]
        values = []
        for end in tradingDays:
            tradingday = context.tradingDays[:context.tradingDays.index(end)+1]
            start_date_list = []
            try:
                start_date_list.append(tradingday[-20])
            except:
                start_date_list.append(0)
            try:
                start_date_list.append(tradingday[-60])
            except:
                start_date_list.append(0)
            try:
                start_date_list.append(tradingday[-120])
            except:
                start_date_list.append(0)
            try:
                start_date_list.append(tradingday[-240])
            except:
                start_date_list.append(0)
            Pr = []
            Bn = []
            beta = []
            alpha = []
            SR = []
            vol = []
            InformationRatio = []
            MaxDrawDown = []
            Instance_id = stamp
            fund_account = myStrategy.account_name
            clear_date = datetime.datetime.strptime(str(end), "%Y%m%d")
            market_value = round(float(account_df.loc[end].loc["portfolio_value"] - account_df.loc[end].loc["cash"]), 2)
            current_balance = round(float(account_df.loc[end].loc["cash"]), 2)
            asset_value = round(float(account_df.loc[end].loc["portfolio_value"]),2)
            for start_date in start_date_list:
                if not start_date:
                    Pr.append(None)
                    Bn.append(None)
                    beta.append(None)
                    alpha.append(None)
                    SR.append(None)
                    vol.append(None)
                    InformationRatio.append(None)
                    MaxDrawDown.append(None)
                else:
                    Pr.append(float(pf.Annualized_Returns(data_Annualized, end,start_date)[0]))
                    Bn.append(float(pf.Benchmark_Returns(data_Benchmark,end,start_date)[0]))
                    beta.append(float(pf.Beta(data_Annualized, data_Benchmark, end, start_date)[0]))
                    alpha.append(float(pf.Alpha(data_Annualized, data_Benchmark, end, rf, start_date)[0]))
                    SR.append(float(pf.Sharpe_Ratio(data_Annualized, end, rf,start_date)[0]))
                    vol.append(float(pf.Volatility(data_Annualized, end,start_date)[0]))
                    InformationRatio.append(float(pf.Information_Ratio(data_Annualized, data_Benchmark, end, start_date)[0]))
                    MaxDrawDown.append(float(pf.Max_Drawdown(data_Annualized,end,start_date)[0]))
            last1m_return_rate = Pr[0]
            last3m_return_rate = Pr[1]
            last6m_return_rate = Pr[2]
            last12m_return_rate = Pr[3]
            last1m_benchmark_return_rate = Bn[0]
            last3m_benchmark_return_rate = Bn[1]
            last6m_benchmark_return_rate = Bn[2]
            last12m_benchmark_return_rate = Bn[3]
            last1m_excess_return_rate = alpha[0]
            last3m_excess_return_rate = alpha[1]
            last6m_excess_return_rate = alpha[2]
            last12m_excess_return_rate = alpha[3]
            last1m_alpha = alpha[0]
            last3m_alpha = alpha[1]
            last6m_alpha = alpha[2]
            last12m_alpha = alpha[3]
            last1m_beta = beta[0]
            last3m_beta = beta[1]
            last6m_beta = beta[2]
            last12m_beta = beta[3]
            last1m_sharpe = SR[0]
            last3m_sharpe = SR[1]
            last6m_sharpe = SR[2]
            last12m_sharpe = SR[3]
            last1m_volatility = vol[0]
            last3m_volatility = vol[1]
            last6m_volatility = vol[2]
            last12m_volatility = vol[3]
            last1m_info_ratio = InformationRatio[0]
            last3m_info_ratio = InformationRatio[1]
            last6m_info_ratio = InformationRatio[2]
            last12m_info_ratio = InformationRatio[3]
            last1m_max_drawdown = MaxDrawDown[0]
            last3m_max_drawdown = MaxDrawDown[1]
            last6m_max_drawdown = MaxDrawDown[2]
            last12m_max_drawdown = MaxDrawDown[3]
            values.append(
                [
                    Instance_id,fund_account,clear_date,market_value,
                    current_balance,asset_value,last1m_return_rate,
                    last3m_return_rate, last6m_return_rate, last12m_return_rate,
                    last1m_benchmark_return_rate,last3m_benchmark_return_rate,
                    last6m_benchmark_return_rate,last12m_benchmark_return_rate,
                    last1m_excess_return_rate,last3m_excess_return_rate,
                    last6m_excess_return_rate,last12m_excess_return_rate,
                    last1m_alpha, last3m_alpha, last6m_alpha, last12m_alpha, last1m_beta,
                    last3m_beta, last6m_beta, last12m_beta, last1m_sharpe, last3m_sharpe,
                    last6m_sharpe, last12m_sharpe, last1m_volatility, last3m_volatility,
                    last6m_volatility, last12m_volatility, last1m_info_ratio,
                    last3m_info_ratio, last6m_info_ratio, last12m_info_ratio,
                    last1m_max_drawdown, last3m_max_drawdown, last6m_max_drawdown,
                    last12m_max_drawdown
                ]
            )
            context.history.add_benefit_monthly(
                Pr, Bn, beta, alpha, SR, vol, InformationRatio, MaxDrawDown, clear_date
            )
        if values:
            values = self.__delete_nan(values)
            self.__handle_mysql("cost_benefit_analysis", values,columns)
#        print("cost_benefit_analysis ok!")

    def daily_cost_benefit(self,myStrategy,stamp,context,df_name,pf,start_date,end_date):
        '''
        存储每日收益表
        :param myStrategy: 实例化myStrategy类
        :param stamp: 时间戳
        :param account_his: 账户的历史明细
        :param current_price_his: 股票收盘价
        :param df_name:
        :param pf: Performance类实例化
        :param start_date: 回测开始日期
        :param end_date: 回测结束日期
        :return:
        '''
        account_his = context.history.account_his
        data_Annualized = account_his["portfolio_value"]
        current_price_his = context.history.current_price_his
        data_Benchmark = current_price_his[df_name]
        account_df = account_his.copy()
        account_df["instance_id"] = stamp
        account_df["fund_account"] = myStrategy.account_name
        account_df["benchmark_price"] = current_price_his[df_name]
        account_df["day_return_rate"] = pf.get_Strategic(data_Annualized,start_date,end_date)
        account_df["return_rate"] = (account_df["day_return_rate"]+1).cumprod()-1
        account_df["day_benchmark_return_rate"] = pf.get_benchmark(data_Benchmark,start_date, end_date)
        account_df["benchmark_return_rate"] = (account_df["day_benchmark_return_rate"]+1).cumprod()-1
        account_df["alpha_return_rate"] = account_df["return_rate"] - account_df["benchmark_return_rate"]
        account_df.rename(columns={'portfolio_value': 'asset_value'}, inplace=True)
        label_list = ['instance_id','fund_account','asset_value','benchmark_price',
                      'return_rate','benchmark_return_rate','alpha_return_rate','clear_date']
        dataSet = []
        for index,d_data in account_df.iterrows():
            index = datetime.datetime.strptime(str(index),"%Y%m%d")
            day_data = []
            for i in label_list:
                if i == "clear_date":
                    day_data.append(index)
                elif i == "instance_id" or i == "fund_account":
                    day_data.append(d_data[i])
                elif i == "asset_value":
                    day_data.append(round(float(d_data[i]), 2))
                else:
                    day_data.append(float(d_data[i]))
            dataSet.append(list(day_data))
        columns = "instance_id,fund_account,asset_value,benchmark_price," \
                  "return_rate,benchmark_return_rate,alpha_return_rate,clear_date"
        context.history.add_daily_cost_benefit(dataSet)
        if dataSet:
            dataSet = self.__delete_nan(dataSet)
            self.__handle_mysql('daily_cost_benefit', values=dataSet, columns=columns)
#        print("daily_cost_benefit Complete !")


    def instance_cost_benefit(self,myStrategy,stamp,context,df_name,pf,start_date,end_date,rf):
        '''
        存储回测实例收益表
        :param myStrategy: myStrategy类实例化
        :param stamp: 时间戳
        :param account_his: 账户历史明细
        :param current_price_his: 股票收盘价
        :param df_name:
        :param pf: Performance类实例化
        :param start_date: 回测开始日期
        :param end_date: 回测结束日期
        :param rf: 无风险收益率
        :return:
        '''
        current_price_his = context.history.current_price_his
        data_Benchmark = current_price_his[df_name]
        account_his = context.history.account_his
        data_Annualized = account_his["portfolio_value"]
        value_dict = {}
        value_dict["Instance_id"] = stamp
        value_dict["fund_account"] = myStrategy.account_name
        init_value = myStrategy.capital_base
        value_dict["init_value"] = float(init_value)
        position_base = myStrategy.position_base
        cost_base = myStrategy.cost_base
        position_capital = 0.0
        for position_key in position_base:
            position_capital += position_base[position_key] * cost_base[position_key]
        asset_value = init_value + position_capital
        value_dict["asset_value"] = float(asset_value)
        value_dict["benchmark_base_price"] = float(current_price_his.loc[start_date,df_name])
        value_dict["return_rate"] = float(pf.Annualized_Returns(data_Annualized, end_date,start_date)[0])
        value_dict["benchmark_return_rate"] = float(pf.Benchmark_Returns(data_Benchmark, end_date, start_date)[0])
        value_dict["alpha_return_rate"] = float(pf.Alpha(data_Annualized,data_Benchmark,end_date,rf,start_date)[0])
        value_dict["sharpe"] = float(pf.Sharpe_Ratio(data_Annualized,end_date,rf,start_date)[0])
        vol = pf.Volatility(data_Annualized,end_date,start_date)
        if vol:
            value_dict["volatility"] = vol[0]
        else:
            value_dict["volatility"] = None
        value_dict["beta"] = float(pf.Beta(data_Annualized,data_Benchmark,end_date,start_date)[0])
        value_dict["info_ratio"] = float(pf.Information_Ratio(data_Annualized,data_Benchmark,end_date,start_date)[0])
        value_dict["max_drawdown"] = float(pf.Max_Drawdown(data_Annualized,end_date,start_date)[0])
        value_dict["annualized_return_rate"] = float(pf.Annualized_Returns(data_Annualized,end_date,start_date)[0])
        label_list = ["Instance_id","fund_account","init_value","asset_value",
                      "benchmark_base_price","return_rate","benchmark_return_rate",
                      "alpha_return_rate","sharpe","volatility","beta","info_ratio",
                      "max_drawdown","annualized_return_rate"]
        values = []
        columns = ""
        df_columns = []
        for label in label_list:
            if pd.isnull(value_dict[label]):
                continue
            else:
                columns += label + ","
                values.append(value_dict[label])
                df_columns.append(label)
        columns = columns[:-1]
        values = [tuple(values)]
        context.history.add_instance_cost_benefit(pd.DataFrame(values,columns=df_columns))
        if values:
            values = self.__delete_nan(values)
            self.__handle_mysql('instance_cost_benefit',values,columns)
#        print("instance_cost_benefit Complete !")


    def run(self,myStrategy,context,start,end,stamp,pf,df_name,rf):
        table_names = {
            "back_test_job": self.back_test_job(myStrategy, start, end ,stamp),
            "fund_account": self.fund_account(stamp, myStrategy, context),
            "cost_benefit_analysis":self.cost_benefit_analysis(stamp,myStrategy,context,pf,df_name,rf),
            "stock_real":self.stock_real(myStrategy,context,stamp),
            "back_test_instance": self.back_test_instance(myStrategy, stamp),
            "daily_fund_real": self.daily_fund_real(myStrategy, stamp, context),
            "daily_cost_benefit": self.daily_cost_benefit(myStrategy, stamp, context, df_name, pf, start, end),
            "instance_cost_benefit": self.instance_cost_benefit(myStrategy, stamp, context, df_name, pf, start, end,rf),
            "daily_stock_real": self.daily_stock_real(myStrategy, stamp, context),
            "trade_entrust": self.trade_entrust(stamp, myStrategy, context),
            "trade_real": self.trade_real(stamp, myStrategy, context)

        }
        for table_name in table_names.keys():
            table_names[table_name]
        self.close()