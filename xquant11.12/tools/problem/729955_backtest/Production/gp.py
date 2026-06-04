import os
import json
import zipfile
import pandas as pd
from copy import deepcopy
from xquant.factordata import FactorData
from xquant.pyfile import Pyfile
fa = FactorData()
py = Pyfile()

def main():
    next_trading_day = "20201029"
    last_trading_day = "20201028"

    portfolioName = "WuKong_{}.xlsx".format(next_trading_day)
    paramName = "WuKong_{}_UAT_Single.zip".format(next_trading_day)

    portfolio_path = "/data/user/666888/WuKong/portfolios/"
    output_path = "/data/user/666888/UAT/WuKong/parameters/WuKong_{}_UAT_Single/".format(next_trading_day)
    zipPath = "/data/user/666888/UAT/WuKong/parameters/{}".format(paramName)

    json_param = {
        "可转债因子计算上午开始时间": "09:30:15",
        "可转债因子计算上午结束时间": "11:29:59",
        "可转债因子计算下午开始时间": "13:00:15",
        "可转债因子计算下午结束时间": "14:56:59",
        "股票因子计算上午开始时间": "09:30:15",
        "股票因子计算上午结束时间": "11:29:59",
        "股票因子计算下午开始时间": "13:00:15",
        "股票因子计算下午结束时间": "14:56:59",
        "允许开仓起始时间": "09:30:00",
        "允许开仓结束时间": "15:00:00",
        "有效tick上午开始时间": "09:30:00",
        "有效tick上午结束时间": "11:30:00",
        "有效tick下午开始时间": "13:00:00",
        "有效tick下午结束时间": "15:00:00",
        "策略开始时间": "09:30:00",
        "策略结束时间": "15:00:00",
        "信号有效上午开始时间": "09:31:15",
        "信号有效上午结束时间": "11:30:00",
        "信号有效下午开始时间": "13:01:15",
        "信号有效下午结束时间": "15:00:00",
        "午盘平仓开始时间": "11:29:00",
        "午盘轻松平仓时间": "11:29:30",
        "午盘平仓结束时间": "11:30:00",
        "闭市平仓开始时间": "14:55:00",
        "闭市轻松平仓时间": "14:56:00",
        "闭市平仓结束时间": "15:00:00",
        "ChaosNum": "20",
        "止损参数": "-20",
        "最大价格偏离度": "0.012",
        "最大单笔委托金额": "500000",
        "最大单边总金额暴露": "1000000",
        "最大单边总张数暴露": "50000",
        "风控成交量统计范围秒数": "180",
        "成交量占比上限": "0.2",
        "最大需更新Tick数量": "3",
        "是否强制加载历史数据": "true",
        "模型目录": "resources/WuKongModel/big_cb_stock_20200701_20200413/",
        "是否使用通用模型": "true",
        "是否使用RemoveSelfOrder": "true",
        "FrozenConfig": "0x0a, 0x07, 0x0a, 0x03, 0x43, 0x50, 0x55, 0x10, 0x06",
        "最大可接受系统延迟秒数": "2000000",
        "活跃度指标": "0",
        "活跃度指标开始使用时间": "09:41:15",
        "upOffset": "5",
        "downOffset": "10",
        "unallowedOpenLossRatio": "-15",
        "风控成交额统计范围秒数": "180",
        "限时成交额上限": "1000000",
        "是否控制双边量额": "false",
        "是否控制平仓量额": "false",
        "下午开盘平仓开始时间": "13:00:00",
        "下午开盘平仓截止时间": "13:01:14",
        "是否忽略深交所停盘检查": "false",
        "平多阈值重置Tick数目": "50",
        "初始平多阈值重置Tick数目": "100",
        "是否打印因子值": "false",
        "因子值打印开始时间": "09:30:00",
        "因子值打印结束时间": "15:00:00",
        "openLongCoef": "1.0003",
        "closeLongCoef": "0.9997",
        "isConservativeMode": "true",
        "临停清仓激进系数": "0.999",
        "临停清仓保守系数": "0.995",
        "计算买入价格方法": "max",
        "计算卖出价格方法": "max",
        "计算买入数量方法": "sum",
        "计算卖出数量方法": "sum",
        "买入投票基准": "1",
        "卖出投票基准": "1",
    }

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    with open("/data/user/666888/WuKong/CBMap/CBMap_{}.json".format(last_trading_day), "r") as f:
        cbMap = json.load(f)

    portfolio_orders = pd.read_excel(portfolio_path + portfolioName)
    portfolio_codes = portfolio_orders.iloc[:, 0].tolist()
    portfolio_quantities = portfolio_orders.iloc[:, 3].tolist()

    counter999 = 0
    counter999List = []
    for code, quantity in zip(portfolio_codes, portfolio_quantities):
        json_param_tmp = deepcopy(json_param)

        json_param_tmp["历史数据日期"] = last_trading_day[:4] + "-" + last_trading_day[4:6] + "-" + last_trading_day[6:]

        if code in cbMap:
            json_param_tmp["对应股票代码"] = cbMap[code][0]
        else:
            json_param_tmp["对应股票代码"] = ""
            print("No ZG for {}".format(code))

        try:
            with py.open("WuKongZHXDTriggers/20200501-20200630_20200701/{}.json".format(code), "rb") as f:
                data = f.read()
                triggerRatioDict = json.loads(data)

            json_param_tmp["信号参数列表"] = [
            {
                "信号组合名称": "1-2-5",
                "longTriggerRatio": str(triggerRatioDict["8min"]["longTriggerRatio"] - 0.5),
                "shortTriggerRatio": str(triggerRatioDict["8min"]["shortTriggerRatio"] + 0.5),
                "longCloseRatio": str(triggerRatioDict["8min"]["longCloseRatio"]),
                "shortCloseRatio": str(triggerRatioDict["8min"]["shortCloseRatio"]),
            },
#            {
#                "信号组合名称": "2-5",
#                "longTriggerRatio": str(triggerRatioDict["7min"]["longTriggerRatio"] - 0.5),
#                "shortTriggerRatio": str(triggerRatioDict["7min"]["shortTriggerRatio"] + 0.5),
#                "longCloseRatio": str(triggerRatioDict["7min"]["longCloseRatio"]),
#                "shortCloseRatio": str(triggerRatioDict["7min"]["shortCloseRatio"]),
#            },
#            {
#                "信号组合名称": "1-5",
#                "longTriggerRatio": str(triggerRatioDict["6min"]["longTriggerRatio"] - 0.5),
#                "shortTriggerRatio": str(triggerRatioDict["6min"]["shortTriggerRatio"] + 0.5),
#                "longCloseRatio": str(triggerRatioDict["6min"]["longCloseRatio"]),
#                "shortCloseRatio": str(triggerRatioDict["6min"]["shortCloseRatio"]),
#            },
#            {
#                "信号组合名称": "1-2",
#                "longTriggerRatio": str(triggerRatioDict["3min"]["longTriggerRatio"] - 0.5),
#                "shortTriggerRatio": str(triggerRatioDict["3min"]["shortTriggerRatio"] + 0.5),
#                "longCloseRatio": str(triggerRatioDict["3min"]["longCloseRatio"]),
#                "shortCloseRatio": str(triggerRatioDict["3min"]["shortCloseRatio"]),
#            },
#            {
#                "信号组合名称": "5",
#                "longTriggerRatio": str(triggerRatioDict["5min"]["longTriggerRatio"]),
#                "shortTriggerRatio": str(triggerRatioDict["5min"]["shortTriggerRatio"]),
#                "longCloseRatio": str(triggerRatioDict["5min"]["longCloseRatio"]),
#                "shortCloseRatio": str(triggerRatioDict["5min"]["shortCloseRatio"]),
#            },
#            {
#                "信号组合名称": "2",
#                "longTriggerRatio": str(triggerRatioDict["2min"]["longTriggerRatio"]),
#                "shortTriggerRatio": str(triggerRatioDict["2min"]["shortTriggerRatio"]),
#                "longCloseRatio": str(triggerRatioDict["2min"]["longCloseRatio"]),
#                "shortCloseRatio": str(triggerRatioDict["2min"]["shortCloseRatio"]),
#            },
#            {
#                "信号组合名称": "1",
#                "longTriggerRatio": str(triggerRatioDict["1min"]["longTriggerRatio"]),
#                "shortTriggerRatio": str(triggerRatioDict["1min"]["shortTriggerRatio"]),
#                "longCloseRatio": str(triggerRatioDict["1min"]["longCloseRatio"]),
#                "shortCloseRatio": str(triggerRatioDict["1min"]["shortCloseRatio"]),
#            },
        ]

            with open(output_path + code + ".json", "w", encoding="utf-8") as f:
                json.dump(json_param_tmp, f, ensure_ascii=False)
        except:
            print("No triggers for {}".format(code))

    with zipfile.ZipFile(zipPath, "w") as f:
        for file in os.listdir(output_path):
            f.write("{}/{}".format(output_path, file), "/{}/{}".format(output_path.split("/")[-2], file))

    print(counter999, counter999List)


if __name__ == "__main__":
    main()
