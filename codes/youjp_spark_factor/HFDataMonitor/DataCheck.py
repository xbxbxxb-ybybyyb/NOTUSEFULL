#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/3/5 17:01
from HFDataLoader.Config import USER_ID
from HFDataLoader.Config import DAILY_SUFFIX, MINUTE_SUFFIX, TICK_SUFFIX, MOCK_TICK_SUFFIX
from HFDataLoader.Config import DailyMonitor, MinuteMonitor, TickMonitor
import Utils.HelpFunc as Util
import os
import time
import pandas as pd
import pickle
from xquant.factordata import FactorData
from xquant.xqutils.xqfile import HDFSFile
from xquant.compute.sparkmr import remote_print


class DataCheck:
    """
    检查stockList中一段交易日区间内数据缺失情况
    """
    def __init__(self, lib_name, code, start_date, end_date, daily=True, minute=True, tick=True, mock_tick=False,
                 save=True, save_path=None, env="Docker"):

        self.lib_name = lib_name
        self.code = code
        self.code_type = Util.get_code_type(self.code)
        self.indus_type = None
        if self.code_type == "INDUSTRY":
            self.indus_type = Util.get_industry_type(self.code)
        self.start_date = start_date
        self.end_date = end_date
        self.trading_day_list = Util.get_trading_day(self.start_date, self.end_date)
        self.daily = daily
        self.minute = minute
        self.tick = tick
        self.mock_tick = mock_tick

        self.fa = FactorData()

        self.save = save
        self.save_path = save_path
        self.env = env
        if self.save:
            if self.save_path is None:
                self.save_path = "HFDataCheck"
            self.hf = HDFSFile()

        self.is_executor = "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ

    def run_check(self):
        self.my_print("Start Check Data: {}-{}-{}, Daily: {}, Minute: {}, Tick:{}, Mock_Tick: {}".format(self.code,
                       self.start_date, self.end_date, self.daily, self.minute, self.tick, self.mock_tick))

        trade_status  = self.get_trade_status()
        if trade_status.empty:
            return None

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
        if self.mock_tick:
            mock_tick_flag = self.run_check_tick_data(valid_trade_dates, MOCK_TICK_SUFFIX)
            flag_df_list.append(mock_tick_flag)

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
        if self.mock_tick:
            invalid_date_list = self.check_trade_status(trade_status, MOCK_TICK_SUFFIX)
            if invalid_date_list:
                flag_dict.update({MOCK_TICK_SUFFIX: sorted(invalid_date_list)})

        if flag_dict:
            # self.dump_to_file(trade_status, "data_check_flag")
            self.dump_to_file(flag_dict, "invalid_date_list")

    def get_trade_status(self):
        """ 获取交易状态
        """
        if self.code_type == "STOCK":
            trade_status = self.fa.get_factor_value('Basic_factor', stock=[self.code], mddate=self.trading_day_list,
                                       factor_names=["trade_status"])
            if trade_status.empty:
                trade_status = pd.DataFrame(columns=["TradeStatus", "TradeFlag"])
            else:
                trade_status = trade_status.droplevel(1)
                trade_status.columns = ["TradeStatus"]
                trade_status["TradeFlag"] = ((~trade_status["TradeStatus"].isnull())
                                      & (trade_status["TradeStatus"] != "待核查")
                                      & (trade_status["TradeStatus"] != "停牌"))
            ### Only Keep Traded Days
            trade_status = trade_status[trade_status["TradeFlag"]==True]
            del trade_status["TradeStatus"]

        elif self.code_type == "INDEX":
            trade_status = pd.DataFrame(data=True, index=self.trading_day_list, columns=["TradeFlag"])

        elif self.code_type == "INDUSTRY":
            trade_status = pd.DataFrame(data=True, index=self.trading_day_list, columns=["TradeFlag"])

        elif self.code_type == "CBOND":
            trade_status = self.fa.get_factor_value('Basic_factor', stock=[self.code], mddate=self.trading_day_list,
                                       factor_names=["trade_status"], category="bond")
            if trade_status.empty:
                trade_status = pd.DataFrame(columns=["TradeStatus", "TradeFlag"])
            else:
                trade_status = trade_status.droplevel(1)
                trade_status.columns = ["TradeStatus"]
                trade_status["TradeFlag"] = ((~trade_status["TradeStatus"].isnull())
                                      & (trade_status["TradeStatus"] != "待核查")
                                      & (trade_status["TradeStatus"] != "停牌")
                                      & (trade_status["TradeStatus"] != "0"))
            ### Only Keep Traded Days
            trade_status = trade_status[trade_status["TradeFlag"]==True]
            del trade_status["TradeStatus"]

        # TODO
        elif self.code_type == "ETF" or self.code_type == "LOF":
            trade_status = pd.DataFrame(data=True, index=self.trading_day_list, columns=["TradeFlag"])

        else:
            raise Exception("Not Supported Yet: {}".format(self.code))

        return trade_status

    def run_check_daily_data(self, valid_trade_dates):
        daily_flag = pd.DataFrame(data=DailyMonitor.EMPTY.value, index=valid_trade_dates,
                                  columns=["{}_FlagValue".format(DAILY_SUFFIX)])
        try:
            data_flag = self.fa.get_factor_value(self.lib_name, "{0}_{1}".format(self.code, DAILY_SUFFIX), "20200102",
                                                  ["{}_Date".format(DAILY_SUFFIX)])
            has_data_dates = set(valid_trade_dates).intersection(data_flag["{}_Date".format(DAILY_SUFFIX)].tolist())
            has_data_dates = sorted(list(has_data_dates))
            if has_data_dates:
                daily_flag.loc[has_data_dates] = DailyMonitor.NORMAL.value
        except:
            pass

        return daily_flag

    def run_check_minute_data(self, valid_trade_dates):
        minute_flag = pd.DataFrame(data=MinuteMonitor.EMPTY.value, index=valid_trade_dates,
                                   columns=["{}_FlagValue".format(MINUTE_SUFFIX)])
        try:
            data_flag = self.fa.get_factor_value(self.lib_name, "{0}_{1}".format(self.code, MINUTE_SUFFIX), "20200102",
                                                ["{}_Date".format(MINUTE_SUFFIX)])
            has_data_dates = set(valid_trade_dates).intersection(data_flag["{}_Date".format(MINUTE_SUFFIX)].tolist())
            has_data_dates = sorted(list(has_data_dates))
            correct_data_shape_dates = []
            for date in has_data_dates:
                date_minute_df = data_flag[data_flag["{}_Date".format(MINUTE_SUFFIX)]==date]
                if date_minute_df.shape[0]==240: # 保证去掉早盘和尾盘集合竞价之后，分钟数为240根
                    correct_data_shape_dates.append(date)
                else:
                    self.my_print("Minute Data Missing: {}-{}-{}".format(self.code, date, date_minute_df.shape[0]))
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

    def run_daily_tick_flag(self, mddate, SUFFIX="T"):
        tick_flag = pd.DataFrame(data=TickMonitor.EMPTY.value, index=[mddate],
                                 columns=["{}_FlagValue".format(SUFFIX)])
        try:
            data_flag = self.fa.get_factor_value(self.lib_name, "{0}_{1}".format(self.code, SUFFIX), mddate,
                                 ["{}_Date".format(SUFFIX)])
            if not data_flag.empty:
                tick_flag.loc[mddate] = TickMonitor.NORMAL.value
        except:
            pass

        return tick_flag

    def check_trade_status(self, trade_status, SUFFIX):
        invalid_date_list = []
        if not trade_status.empty:
            COLUMN_NAMES = ["TradeFlag", "{}_FlagValue".format(SUFFIX)]
            trade_flag = trade_status[COLUMN_NAMES]
            Monitor = self.get_monitor_enum(SUFFIX)
            invalid_date_flag = trade_flag[(trade_flag["TradeFlag"].isin([True])) &
                                       (trade_flag["{}_FlagValue".format(SUFFIX)].isin([Monitor.EMPTY.value]))]
            invalid_date_list = invalid_date_flag.index.tolist()
        return invalid_date_list

    @staticmethod
    def get_monitor_enum(SUFFIX):
        if SUFFIX == DAILY_SUFFIX:
            return DailyMonitor
        elif SUFFIX == MINUTE_SUFFIX:
            return MinuteMonitor
        elif SUFFIX in [TICK_SUFFIX, MOCK_TICK_SUFFIX]:
            return TickMonitor
        else:
            raise Exception("Not Supported Data Type")

    def get_save_root_path(self):
        if self.env == "Docker":
            root = os.path.join("", self.save_path)
        else:
            root = os.path.join(USER_ID, self.save_path)
        return root

    def dump_to_file(self, df, file_type):
        path = self.get_save_root_path()
        file_name = os.path.join(path, "{}_{}.pkl".format(self.code, file_type))
        if not self.hf.exists(path):
            self.hf.mkdir(path)
        with self.hf.open(file_name, 'wb') as f:
            pickle.dump(df, f)

    def my_print(self, x_str):
        if self.is_executor:
            remote_print(x_str)
        else:
            print(x_str)


if __name__=="__main__":
    lib_name = "XHFDataLib"
    code = "b10101"
    start_date = "20200301"
    end_date = "20200306"
    daily = False
    minute= False
    tick = True
    mock_tick = False
    save = True
    save_path = "HFDataCheck"
    env = "Docker"

    t1 = time.time()
    instance = DataCheck(lib_name, code, start_date, end_date, daily, minute, tick, mock_tick, save, save_path, env)
    instance.run_check()
    print("Time Cost: ", str(time.time() - t1))


    




