import os
import json
from xquant.pyfile import Pyfile


def main(today):
    production_param_path = "/data/user/666888/Apollo/parameters/Apollo_{}/".format(today)
    output_path = "Apollo/bt_params/{}/".format(today)
    portfolios = ["5162001", "5161101"]

    py = Pyfile()
    for portfolio in portfolios:
        file_list = os.listdir(production_param_path + portfolio)
        for file in file_list:
            with open(production_param_path + portfolio + "/" + file, "r", encoding="utf-8") as f:
                production_param = json.load(f)

            bt_param = {"Timetable": {today: []}, "TargetQtyInterval": {today: []}}
            if 300000 <= int(file[0:6]) <= 399999:
                bt_param["Holo"] = "true"
            else:
                bt_param["Holo"] = "false"

            for pair in production_param["目标持仓"]:
                bt_param["Timetable"][today].append(pair["Time"])
                bt_param["TargetQtyInterval"][today].append(abs(int(pair["TargetQty"])))

            with py.open(output_path + portfolio + "/" + file, "wb") as f:
                json.dump(bt_param, f)


if __name__ == "__main__":
    today = "20191209"
    main(today)