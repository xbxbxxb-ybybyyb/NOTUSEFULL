"""持仓时候的收益率分析（最大浮盈，最大回撤）"""

import pandas as pd
import os
from xquant.factordata import FactorData


fa = FactorData()


def main():
    bt_path = "/data/user/011668/bt_test/results/20200601-20200831/bt-20200601-20200831-WuKong-ProductionExecutor-2/"
    HoldingRet(bt_path).main()
    print("end")


class HoldingRet:
    def __init__(self, bt_path):
        self.bt_path = bt_path
        self.save_path = "/data/user/011668/other/big_loss"
        os.makedirs(self.save_path, exist_ok=True)

    def main(self):
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
                a = self.get_factor_value(code, trade_date, st_time, ed_time)
                if a is not None:
                    res_list.append([code, trade_date, st_time, ed_time, profit, amt] + list(a))
            print("{}/{}".format(i + 1, len(all_code)))
        res_df = pd.DataFrame(res_list, columns=["code", "date", "st_time", "ed_time", "profit", "amt",
                                                 "pct1", "pct2", "pct5", "per"])
        res_df = res_df.sort_values(by="profit")
        res_df.to_csv("{}/{}".format(self.save_path, "bt_sum_js2.csv"), index=False)
        print("")

    def get_factor_value(self, code, date, st_time, ed_time):
        TICK_COLUMNS = ["T_Time", "T_BidPrice"]
        st_time_int, ed_time_int = int(st_time.replace(":", "")), int(ed_time.replace(":", ""))
        try:
            data = fa.get_factor_value("XHFDataLib", code + "_T", str(date), TICK_COLUMNS).set_index('T_Time')
            data["T_BidPrice"] = [x[0] if x is not None else 0 for x in data["T_BidPrice"]]
            data.index = [int(x) / 1000 for x in data.index]
            select_data = data.loc[st_time_int:ed_time_int]
            return select_data
        except:
            return


if __name__ == '__main__':
    main()


