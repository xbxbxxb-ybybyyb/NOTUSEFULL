#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/4/6 17:02
import json
import pickle
from xquant.xqutils.xqfile import HDFSFile


def collect_check_result(check_path="ZeusDataCheck/"):
    hf = HDFSFile()

    check_result_dict = dict()

    files = hf.listdir(check_path)
    if len(files) > 0:
        for file in files:
            with hf.open(check_path + file, "rb") as f:
                data = f.read()
                data = pickle.loads(data)

                symbol = file.split("_")[0]
                if symbol == "601360.SH":
                    continue
                if len(data) > 0:
                    check_result_dict.update({symbol: data})

    return check_result_dict


if __name__ == "__main__":
    check_path = "ZeusDataCheck/"
    check_result_dict = collect_check_result(check_path)
    if len(check_result_dict) > 0:
        with open("/data/user/015629/MISC/tick_tran_order_check_result.json", "w+", encoding="UTF-8") as f:
            json.dump(check_result_dict, f, ensure_ascii=False, indent=4)
            f.close()
    print(check_result_dict)
