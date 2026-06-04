#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/3/5 17:01
from DataInterface.Config import USER_ID
from DataInterface.Config import DAILY_SUFFIX, MINUTE_SUFFIX, TICK_SUFFIX, TRANSACTION_SUFFIX, ORDER_SUFFIX
from DataInterface.Config import TICK_STOCK_HBASE_COLUMNS, TRANSACTION_STOCK_HBASE_COLUMNS, ORDER_STOCK_HBASE_COLUMNS
from DataInterface.Config import TICK_CBOND_HBASE_COLUMNS, TRANSACTION_CBOND_HBASE_COLUMNS, ORDER_CBOND_HBASE_COLUMNS
from DataInterface.Config import TICK_FUND_HBASE_COLUMNS, TRANSACTION_FUND_HBASE_COLUMNS, ORDER_FUND_HBASE_COLUMNS
from DataInterface.Config import TICK_FUTURE_HBASE_COLUMNS, TICK_INDEX_HBASE_COLUMNS
from DataMonitor.Monitor import DailyMonitor, MinuteMonitor, TickMonitor, TransactionMonitor, OrderMonitor
from Utils.HelpFunc import my_print, get_code_type, get_industry_type, get_trading_day

import os
import time
import pandas as pd
import pickle
from xquant.factordata import FactorData
from xquant.xqutils.xqfile import HDFSFile


class DataCheck:
    """
    检查stockList中一段交易日区间内数据缺失情况
    """
    def __init__(self, library, code, start_date, end_date, daily=True, minute=True, tick=True, tran=True, order=True,
                 save=True, save_path=None):

        self.library = library
        self.code = code
        self.code_type = get_code_type(self.code)
        self.indus_type = get_industry_type(self.code) if self.code_type == "INDUSTRY" else None
        self.start_date = start_date
        self.end_date = end_date
        self.trading_day_list = get_trading_day(self.start_date, self.end_date)
        self.daily = daily
        self.minute = minute
        self.tick = tick
        self.tran = tran
        self.order = order
        self.save = save
        self.save_path = save_path

        if self.code_type not in ["STOCK", "CBOND", "ETF", "LOF"]:
            self.tran = False
        if not (self.code.endswith(".SZ") and self.code_type in ["STOCK", "CBOND", "ETF", "LOF"]):
            self.order = False

        self.fa = FactorData()
        self.hf = HDFSFile()

    def run(self):
        my_print(" Start Check Data: {}-{}-{}, Daily: {}, Minute: {}, Tick:{}, Tran: {}, Order: {} ".format(self.code,
                       self.start_date, self.end_date, self.daily, self.minute, self.tick, self.tran, self.order))

        trade_status  = self.get_trade_status()
        if trade_status.empty:
            return

        valid_trade_dates = sorted(trade_status.index.tolist())

        flag_df_list = [trade_status]

        if self.daily:
            daily_flag = self.run_check_daily_data(valid_trade_dates)
            flag_df_list.append(daily_flag)
        if self.minute:
            minute_flag = self.run_check_minute_data(valid_trade_dates)
            flag_df_list.append(minute_flag)
        if self.tick:
            tick_flag = self.run_check_tick_data(valid_trade_dates, TICK_SUFFIX)
            flag_df_list.append(tick_flag)
        if self.tran:
            transaction_flag = self.run_check_tick_data(valid_trade_dates, TRANSACTION_SUFFIX)
            flag_df_list.append(transaction_flag)
        if self.order:
            order_flag = self.run_check_tick_data(valid_trade_dates, ORDER_SUFFIX)
            flag_df_list.append(order_flag)

        trade_status_df = pd.concat(flag_df_list, axis=1)

        if self.save:
            self.run_dump(trade_status_df)

    def run_dump(self, trade_status):
        flag_dict = {}
        if self.daily:
            invalid_date_list = self.check_trade_status(trade_status, DAILY_SUFFIX)
            if invalid_date_list:
                flag_dict.update({DAILY_SUFFIX: sorted(invalid_date_list)})
        if self.minute:
            invalid_date_list = self.check_trade_status(trade_status, MINUTE_SUFFIX)
            if invalid_date_list:
                flag_dict.update({MINUTE_SUFFIX: sorted(invalid_date_list)})
        if self.tick:
            invalid_date_list = self.check_trade_status(trade_status, TICK_SUFFIX)
            if invalid_date_list:
                flag_dict.update({TICK_SUFFIX: sorted(invalid_date_list)})
        if self.tran:
            invalid_date_list = self.check_trade_status(trade_status, TRANSACTION_SUFFIX)
            if invalid_date_list:
                flag_dict.update({TRANSACTION_SUFFIX: sorted(invalid_date_list)})
        if self.order:
            invalid_date_list = self.check_trade_status(trade_status, ORDER_SUFFIX)
            if invalid_date_list:
                flag_dict.update({ORDER_SUFFIX: sorted(invalid_date_list)})

        if flag_dict:
            self.dump_to_file(flag_dict, "invalid_date_list")

    def get_trade_status(self):
        """ 获取交易状态
        """
        if self.code_type == "STOCK":
            trade_status = self.fa.get_factor_value("Basic_factor", stock=[self.code], mddate=self.trading_day_list,
                                       factor_names=["trade_status", "volume"])
            if trade_status.empty:
                trade_status = pd.DataFrame(columns=["TradeFlag", "TradeStatus", "Volume"])
            else:
                trade_status = trade_status.droplevel(1)
                trade_status.columns = ["TradeStatus", "Volume"]
                trade_status["TradeFlag"] = ((~trade_status["TradeStatus"].isnull())
                                              & (trade_status["TradeStatus"] != "待核查")
                                              & (trade_status["TradeStatus"] != "停牌")
                                              &(trade_status["Volume"] != 0))
            ### Only Keep Traded Days
            trade_status = trade_status[trade_status["TradeFlag"] == True]
            del trade_status["TradeStatus"]
            del trade_status["Volume"]

        elif self.code_type == "INDEX":
            trade_status = pd.DataFrame(data=True, index=self.trading_day_list, columns=["TradeFlag"])

        elif self.code_type == "INDUSTRY":
            trade_status = pd.DataFrame(data=True, index=self.trading_day_list, columns=["TradeFlag"])

        elif self.code_type == "CBOND":
            trade_status = self.fa.get_factor_value('Basic_factor', stock=[self.code], mddate=self.trading_day_list,
                                       factor_names=["trade_status", "volume"], category="bond")
            if trade_status.empty:
                trade_status = pd.DataFrame(columns=["TradeStatus", "TradeFlag", "Volume"])
            else:
                trade_status = trade_status.droplevel(1)
                trade_status.columns = ["TradeStatus", "Volume"]
                trade_status["TradeFlag"] = ((~trade_status["TradeStatus"].isnull())
                                      & (trade_status["TradeStatus"] != "待核查")
                                      & (trade_status["TradeStatus"] != "停牌")
                                      & (trade_status["TradeStatus"] != "0")
                                      & (trade_status["Volume"] != 0))
            ### Only Keep Traded Days
            trade_status = trade_status[trade_status["TradeFlag"] == True]
            del trade_status["TradeStatus"]
            del trade_status["Volume"]

        # TODO
        elif self.code_type == "ETF" or self.code_type == "LOF":
            trade_status = pd.DataFrame(data=True, index=self.trading_day_list, columns=["TradeFlag"])

        else:
            raise Exception(" Not Supported Yet: {} ".format(self.code))

        return trade_status

    def run_check_daily_data(self, valid_trade_dates):
        daily_flag = pd.DataFrame(data=DailyMonitor.EMPTY.value, index=valid_trade_dates, columns=["{}_FlagValue".format(DAILY_SUFFIX)])
        try:
            data_flag = self.fa.get_factor_value(self.library, self.code, "20200102", ["{}_Date".format(DAILY_SUFFIX)])
            has_data_dates = set(valid_trade_dates).intersection(data_flag["{}_Date".format(DAILY_SUFFIX)].tolist())
            has_data_dates = sorted(list(has_data_dates))
            if has_data_dates:
                daily_flag.loc[has_data_dates] = DailyMonitor.NORMAL.value
        except:
            pass

        return daily_flag

    def run_check_minute_data(self, valid_trade_dates):
        minute_flag = pd.DataFrame(data=MinuteMonitor.EMPTY.value, index=valid_trade_dates, columns=["{}_FlagValue".format(MINUTE_SUFFIX)])
        try:
            data_flag = self.fa.get_factor_value(self.library, self.code, "20200102", ["{}_Date".format(MINUTE_SUFFIX)])
            has_data_dates = set(valid_trade_dates).intersection(data_flag["{}_Date".format(MINUTE_SUFFIX)].tolist())
            has_data_dates = sorted(list(has_data_dates))
            correct_data_shape_dates = []
            for date in has_data_dates:
                date_minute_df = data_flag[data_flag["{}_Date".format(MINUTE_SUFFIX)] == date]
                if date_minute_df.shape[0] == 240: # 保证去掉早盘和尾盘集合竞价之后，分钟数为240根
                    correct_data_shape_dates.append(date)
                else:
                    my_print(" Minute Data Missing: {}-{}-{} ".format(self.code, date, date_minute_df.shape[0]))
            if correct_data_shape_dates:
                minute_flag.loc[correct_data_shape_dates] = MinuteMonitor.NORMAL.value
        except:
            pass

        return minute_flag

    def run_check_tick_data(self, valid_trade_dates, SUFFIX):
        tick_flag_list = []
        for trading_day in valid_trade_dates:
            daily_tick_flag = self.run_daily_tick_flag(trading_day, SUFFIX)
            tick_flag_list.append(daily_tick_flag)
        tick_flag = pd.concat(tick_flag_list, axis=0)
        return tick_flag

    def run_daily_tick_flag(self, date, SUFFIX):
        monitor = self.get_monitor_enum(SUFFIX)
        hbase_columns = self.get_hbase_columns(SUFFIX)
        tick_flag = pd.DataFrame(data=monitor.EMPTY.value, index=[date], columns=["{}_FlagValue".format(SUFFIX)])
        try:
            data_flag = self.fa.get_factor_value(self.library, self.code, date, hbase_columns)
            if not data_flag.empty and data_flag.shape[1] == len(hbase_columns):
                tick_flag.loc[date] = monitor.NORMAL.value
        except:
            pass

        return tick_flag

    def check_trade_status(self, trade_status, SUFFIX):
        invalid_date_list = []
        if not trade_status.empty:
            COLUMN_NAMES = ["TradeFlag", "{}_FlagValue".format(SUFFIX)]
            trade_flag = trade_status[COLUMN_NAMES]
            Monitor = self.get_monitor_enum(SUFFIX)
            invalid_date_flag = trade_flag[(trade_flag["TradeFlag"].isin([True])) & (trade_flag["{}_FlagValue".format(SUFFIX)].isin([Monitor.EMPTY.value]))]
            invalid_date_list = invalid_date_flag.index.tolist()

        return invalid_date_list

    @staticmethod
    def get_monitor_enum(SUFFIX):
        if SUFFIX == DAILY_SUFFIX:
            return DailyMonitor
        elif SUFFIX == MINUTE_SUFFIX:
            return MinuteMonitor
        elif SUFFIX == TICK_SUFFIX:
            return TickMonitor
        elif SUFFIX == TRANSACTION_SUFFIX:
            return TransactionMonitor
        elif SUFFIX == ORDER_SUFFIX:
            return OrderMonitor
        else:
            raise Exception(" Not Supported Check Data Type ")

    def get_hbase_columns(self, SUFFIX):
        if SUFFIX == TICK_SUFFIX:
            if self.code_type == "STOCK":
                hbase_columns = TICK_STOCK_HBASE_COLUMNS
            elif self.code_type == "CBOND":
                hbase_columns = TICK_CBOND_HBASE_COLUMNS
            elif self.code_type in ["ETF", "LOF"]:
                hbase_columns = TICK_FUND_HBASE_COLUMNS
            elif self.code_type == "FUTURE":
                hbase_columns = TICK_FUTURE_HBASE_COLUMNS
            elif self.code_type in ["INDEX", "INDUSTRY"]:
                hbase_columns = TICK_INDEX_HBASE_COLUMNS

        elif SUFFIX == TRANSACTION_SUFFIX:
            if self.code_type == "STOCK":
                hbase_columns = TRANSACTION_STOCK_HBASE_COLUMNS
            elif self.code_type == "CBOND":
                hbase_columns = TRANSACTION_CBOND_HBASE_COLUMNS
            elif self.code_type in ["ETF", "LOF"]:
                hbase_columns = TRANSACTION_FUND_HBASE_COLUMNS

        elif SUFFIX == ORDER_SUFFIX and self.code.endswith(".SZ"):
            if self.code_type == "STOCK":
                hbase_columns = ORDER_STOCK_HBASE_COLUMNS
            elif self.code_type == "CBOND":
                hbase_columns = ORDER_CBOND_HBASE_COLUMNS
            elif self.code_type in ["ETF", "LOF"]:
                hbase_columns = ORDER_FUND_HBASE_COLUMNS
        else:
            raise Exception(" Not Supported Data Type: {} ".format(SUFFIX))

        return hbase_columns

    def dump_to_file(self, df, file_type):
        if "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ:
            path = os.path.join(USER_ID, self.save_path)
        else:
            path = self.save_path

        file_name = os.path.join(path, "{}_{}.pickle".format(self.code, file_type))
        if not self.hf.exists(path):
            self.hf.mkdir(path)

        with self.hf.open(file_name, "wb") as f:
            pickle.dump(df, f)


if __name__=="__main__":
    library = "XHFDataLib"
    code = "b10101"
    start_date = "20200301"
    end_date = "20200306"
    daily = False
    minute= False
    tick = True
    tran = False
    order = False
    save = True
    save_path = "HFDataCheck"

    t1 = time.time()
    instance = DataCheck(library, code, start_date, end_date, daily, minute, tick, tran, order, save, save_path)
    instance.run()
    print("Time Cost: ", str(time.time() - t1))


    




