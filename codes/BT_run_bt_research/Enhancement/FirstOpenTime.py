"""第一次开仓时候的形态分析"""

import pandas as pd
import time
import os
from xquant.factordata import FactorData


fa = FactorData()


def main():
    bt_path = "/data/user/011668/bt_test/results/20200601-20200831/bt-20200601-20200831-WuKong-ProductionExecutor-2/"
    FirstOpenTime(bt_path).main()
    print("end")


class FirstOpenTime:
    def __init__(self, bt_path):
        self.bt_path = bt_path
        self.save_path = "/data/user/011668/other/big_loss"
        os.makedirs(self.save_path, exist_ok=True)
        self.factor_lib = "FactorJS_CB"

    def main(self):
        data = pd.read_csv("{}/{}".format(self.save_path, "bt_sum_js.csv"))
        data2 = pd.read_csv("{}/{}".format(self.save_path, "bt_sum_js2.csv"))
        # 前一波跌幅大，且在日内低点
        a = data[data["pct1"] < -0.01]
        res_a = self.acc_profit(a, [-0.01, 0.3, 0.5, 1])

        a2 = data2[data2["pct1"] < -0.01]
        res_a2 = self.acc_profit(a2, [-0.01, 0.3, 0.5, 1])

        b = data2[data2["pct1"] > 0.01]
        res_b = self.acc_profit(b, [-0.01, 0.3, 0.5, 0.8, 1])
        print("")

    def collect_first_open_time_bt(self):
        res_list = []

        all_file_name = os.listdir(self.bt_path)
        all_code = list(filter(lambda x: x.endswith(".SH.xls") or x.endswith(".SZ.xls"), all_file_name))
        for i, code in enumerate(all_code):
            data = pd.read_excel("{}/{}".format(self.bt_path, code), sheet_name="orders")
            code = code[0:9]
            for j in range(data.shape[0]):
                trade_date = int(data.at[j, "date"].replace("-", ""))
                st_time = data.at[j, "startTime"]
                ed_time = data.at[j, "endTime"]
                profit = data.at[j, "afterCostProfit"]
                amt = data.at[j, "cumAmount"]
                a = self.get_factor_value(code, trade_date, st_time)
                if a is not None:
                    res_list.append([code, trade_date, st_time, ed_time, profit, amt] + list(a))
            print("{}/{}".format(i + 1, len(all_code)))
        res_df = pd.DataFrame(res_list, columns=["code", "date", "st_time", "ed_time", "profit", "amt",
                                                 "pct1", "pct2", "pct5", "per"])
        res_df = res_df.sort_values(by="profit")
        res_df.to_csv("{}/{}".format(self.save_path, "bt_sum_js2.csv"), index=False)

    @staticmethod
    def acc_profit(data, classify_value):
        res = []
        for i in range(len(classify_value) - 1):
            text_s = "{}-{}".format(classify_value[i], classify_value[i + 1])
            data_s = data[(data["per"] > classify_value[i]) & (data["per"] <= classify_value[i + 1])]
            profit_sum_s = data_s["profit"].sum()
            count_s = data_s.shape[0]
            res.append([text_s, count_s, profit_sum_s])
        res_df = pd.DataFrame(res, columns=["classify", "sample", "profit"])
        return res_df

    def get_factor_value(self, code, date, s_time):
        tss1 = "{}-{}-{} {}".format(str(date)[0:4], str(date)[4:6], str(date)[6:8], s_time)
        time_timestamp = int(time.mktime(time.strptime(tss1, "%Y-%m-%d %H:%M:%S")))
        TICK_COLUMNS = ["timestamp", "factorPct1min", "factorPct2min", "factorPct5min", "factorPricePercentile"]
        try:
            data = fa.get_factor_value(self.factor_lib, code, str(date), TICK_COLUMNS).set_index('timestamp')
            return data.loc[:time_timestamp].iloc[-1, :].values
        except:
            return


if __name__ == '__main__':
    main()


