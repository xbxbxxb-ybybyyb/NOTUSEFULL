#-*- coding:utf-8 -*-
# author: 015629
# datetime:2022/12/13 15:45
import pandas as pd
from xquant.factordata import FactorData
from SignalEns.SignalConfigManager import SignalConfigManager
from Utils.HelpFunc import MyPrint, get_code_type, get_trading_day


class SignalEnsemble(object):
    def __init__(self, code, start_date, end_date, ensemble_mode, library_list, tag_type_list, save, save_library, save_tag_type, check, update_missing):
        self.code = code
        self.code_type = get_code_type(self.code)
        self.start_date = start_date
        self.end_date = end_date
        self.ensemble_mode = ensemble_mode
        self.library_list = library_list
        self.tag_type_list = tag_type_list
        self.save = save
        self.save_library = save_library
        self.save_tag_type = save_tag_type
        self.check = check
        self.update_missing = update_missing

        self.scm = SignalConfigManager(self.library_list, self.tag_type_list, self.save_library, self.save_tag_type)
        self.weight = 1.0 / len(self.library_list)
        self.ensemble_columns = self.scm.get_signal_columns(self.save_library)

        self.fa = FactorData()

    def get_daily_signal_data(self, date, library):
        hbase_columns = ["timestamp"] + self.scm.get_signal_columns(library) + self.scm.get_tag_columns(library)
        rename_dict = self.scm.get_columns_dict(library, self.save_library, ["Signal", "Tag"])
        try:
            signal = self.fa.get_factor_value(library, self.code, date, hbase_columns)
        except:
            signal = pd.DataFrame(columns=hbase_columns)
        signal = signal.rename(columns=rename_dict)
        signal = signal.reindex(columns=["timestamp"] + self.scm.get_signal_columns(self.save_library) + self.scm.get_tag_columns(self.save_library))

        return signal

    def load_valid_trade_dates(self, trading_day_list):
        """ 获取交易状态
        """

        if self.code_type == "STOCK":
            trade_status = self.fa.get_factor_value("Basic_factor", stock=[self.code], mddate=trading_day_list,
                                       factor_names=["trade_status", "volume", "stpt", "pct_chg"])
            if trade_status.empty:
                trade_status = pd.DataFrame(columns=["mddate", "trade_flag"])
            else:
                trade_status = trade_status.droplevel(1).reset_index()
                trade_status["trade_flag"] = ((~trade_status["trade_status"].isnull())
                                              & (trade_status["trade_status"] != "待核查")
                                              & (trade_status["trade_status"] != "停牌")
                                              & (trade_status["volume"] != 0))
                                              #& (trade_status["stpt"] != "1"))
            ### Only Keep Traded Days
            trade_status = trade_status[trade_status["trade_flag"] == True]

        elif self.code_type == "CBOND":
            trade_status = self.fa.get_factor_value("Basic_factor", stock=[self.code], mddate=trading_day_list,
                                       factor_names=["trade_status", "volume"], category="bond")
            if trade_status.empty:
                trade_status = pd.DataFrame(columns=["mddate", "trade_flag"])
            else:
                trade_status = trade_status.droplevel(1).reset_index()
                trade_status["trade_flag"] = ((~trade_status["trade_status"].isnull())
                                               & (trade_status["trade_status"] != "待核查")
                                               & (trade_status["trade_status"] != "停牌")
                                               & (trade_status["trade_status"] != "0")
                                               & (trade_status["volume"] != 0))
            ### Only Keep Traded Days
            trade_status = trade_status[trade_status["trade_flag"] == True]
        else:
            raise Exception(" Not Supported Yet: {} ".format(self.code))

        return sorted(trade_status["mddate"].tolist())

    def run_check_signal_data(self, valid_trade_dates):
        missing_trade_dates = []
        for date in valid_trade_dates:
            data_exist = self.run_check_daily_signal_data(date)
            if not data_exist:
                missing_trade_dates.append(date)
        return missing_trade_dates

    def run_check_daily_signal_data(self, date):
        hbase_columns = ["timestamp"] + self.scm.get_signal_columns(self.save_library)
        data_exist = False
        try:
            tick_data = self.fa.get_factor_value(self.save_library, self.code, date, hbase_columns)
            if not tick_data.empty and tick_data.shape[1] == len(hbase_columns):
                data_exist = True
        except:
            pass

        return data_exist

    def run(self):
        date_list = get_trading_day(self.start_date, self.end_date)
        valid_date_list = self.load_valid_trade_dates(date_list)

        if self.check:
            missing_trade_dates = self.run_check_signal_data(valid_date_list)
            if len(missing_trade_dates) > 0:
                MyPrint(" Check Signal Data: {}-{}-{}, Missing Dates: {} ".format(self.code, self.start_date, self.end_date, missing_trade_dates))
            valid_date_list = missing_trade_dates

        if self.check and not self.update_missing:
            return

        ensemble_df_dict = dict()

        for date in valid_date_list:
            daily_ensemble_df = self.run_daily(date)
            if daily_ensemble_df.empty:
                continue
            ensemble_df_dict.update({date: daily_ensemble_df})
            if self.save:
                self.fa.update_factor_value(self.save_library, daily_ensemble_df, self.code, date)

        MyPrint(" Ensemble Signal Data Done: {}-{}-{}-{} ".format(self.code, self.start_date, self.end_date, "-".join(self.library_list)))

        return ensemble_df_dict

    def run_daily(self, date):
        """"""
        ensemble_list = []
        common_times = set()
        for i, library in enumerate(self.library_list):
            signal_df = self.get_daily_signal_data(date, library)
            if i == 0:
                common_times = set(signal_df["timestamp"].tolist())
            else:
                common_times = common_times.intersection(signal_df["timestamp"].tolist())

            if not signal_df.empty:
                ensemble_list.append(signal_df)
            else:
                MyPrint(" Signal Empty: {}-{}-{} ".format(library, self.code, date))

        if self.ensemble_mode == "Weight":
            if len(ensemble_list) > 0:
                ensemble_list = [sv[sv["timestamp"].isin(common_times)].reset_index(drop=True) for sv in ensemble_list]

        if len(ensemble_list) != len(self.library_list):
            MyPrint(" Signal Missing to {}/{}: {}-{} ".format(len(ensemble_list), len(self.library_list), self.code, date))
            return pd.DataFrame()

        if self.ensemble_mode == "Weight":
            for i, signal in enumerate(ensemble_list):
                if i == 0:
                    signal_ensemble = signal.copy()
                    signal_ensemble[self.ensemble_columns] = signal[self.ensemble_columns] * self.weight
                else:
                    signal_ensemble[self.ensemble_columns] = signal_ensemble[self.ensemble_columns] + signal[self.ensemble_columns] * self.weight

        elif self.ensemble_mode == "Concat":
            signal_ensemble = pd.concat(ensemble_list, axis=0).sort_values(by="timestamp").reset_index(drop=True)

        return signal_ensemble


if __name__  == "__main__":
    code = "000001.SZ"
    start_date = "20221123"
    end_date = "20221125"
    ensemble_mode = "Weight"
    library_list = ["Albest20220201Order036Signals", "LightGBMRegr_DataSZ_Ev20220201Sample_036"]
    tag_type_list = ["Common", "NChangeTime"]
    save = False
    save_library = "Albest20220201_LightGBMRegr_EvSample_036"
    save_tag_type = "Common"
    check = False
    update_missing = True

    se = SignalEnsemble(code, start_date, end_date, ensemble_mode, library_list, tag_type_list, save, save_library, save_tag_type, check, update_missing)
    ensemble_dict = se.run()
    print(ensemble_dict)

