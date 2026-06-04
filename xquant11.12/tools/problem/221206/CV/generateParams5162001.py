import os
import shutil
import json
import pandas as pd
from copy import deepcopy
from CV.generateTimetableAndTargetQtyInterval import generateTimetableAndTargetQtyInterval
from CV.generateGeneralTrigger import generateGeneralTrigger


def main():
    portfolio = "5162001"

    next_trading_day = "20191223"
    last_trading_day = "20191220"
    start_date = "20191007"
    end_date = "20191220"
    period = 20

    portfolio_path = "/data/user/666888/Apollo/portfolios/{}/morning/".format(next_trading_day)
    output_path = "/data/user/666888/Apollo/parameters/Apollo_{}/{}/".format(next_trading_day, portfolio)
    param_path = "/data/user/666888/Apollo/cv_results/results/{}-{}_{}/{}/".format(
        start_date, end_date, next_trading_day, portfolio
    )

    json_param = {
        "因子计算上午开始时间": "09:30:15",
        "因子计算上午结束时间": "11:30:00",
        "因子计算下午开始时间": "13:00:15",
        "因子计算下午结束时间": "14:56:59",
        "允许开仓起始时间": "09:30:00",
        "允许开仓结束时间": "14:57:00",
        "有效tick上午开始时间": "09:30:00",
        "有效tick上午结束时间": "11:29:59",
        "有效tick下午开始时间": "13:00:00",
        "有效tick下午结束时间": "14:56:59",
        "策略开始时间": "09:30:00",
        "策略结束时间": "14:56:59",
        "信号有效上午开始时间": "09:31:15",
        "信号有效上午结束时间": "11:29:59",
        "信号有效下午开始时间": "13:01:15",
        "信号有效下午结束时间": "14:56:59",
        "闭市区间上午开始时间": "11:29:00",
        "闭市区间上午结束时间": "11:30:00",
        "闭市区间下午开始时间": "14:55:00",
        "闭市区间下午结束时间": "14:57:00",
        "区间结束时间长度": "15",
        "区间结束激进下单时间长度": "15",
        "aggressivePriceMulti": "0.0002",
        "priceMulti": "0.0004",
        "priceLimitMulti": "0.001",
        "marketClosePriceMulti": "0.012",
        "最大需更新Tick数量": "3",
        "是否强制加载历史数据": "true",
        "模型目录": "resources/StrategyModel/apple",
        "是否使用通用模型": "true",
        "FrozenConfig": "0x0a, 0x07, 0x0a, 0x03, 0x43, 0x50, 0x55, 0x10, 0x06",
        "单笔最大委托金额": "1800000",
        "单笔最大报单量": "1000000",
        "涨跌停最大委托金额": "1800000",
        "下单价格最大偏离度": "0.012",
        "最大可接受系统延迟秒数": "20",
        "提前闭市区间下午开始时间": "14:30:00",
        "priceCutOff": "25",
        "ChaosNum": "20",
        "上午截止时间1": "11:25:00",
        "上午截止时间2": "11:28:00",
        "上午截止时间3": "11:29:00",
        "下午截止时间": "14:52:00",
        "下单模块名": "CsfNew",
        "是否使用RemoveSelfOrder": "true",
        "marketCloseVolumeUpperLimit": "0.3",
        "marketVolumeProportionTrigger": "0.03",
        "unfinishedQtyUpperLimit": "0.75",
        "remainRatioTrigger": "0.9",
        "remainRatioTrigger2": "0.5"
    }

    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        shutil.rmtree(output_path)
        os.makedirs(output_path)

    portfolio_orders = pd.read_excel(portfolio_path + "Apollo_" + portfolio + "_" + next_trading_day + ".xlsx")
    portfolio_codes = portfolio_orders.iloc[:, 0].tolist()
    portfolio_quantities = (portfolio_orders.iloc[:, 3] - portfolio_orders.iloc[:, 4]).tolist()

    try:
        portfolio_customized_triggers = pd.read_excel(param_path + "/TotalSummary.xlsx", index_col=0)
    except FileNotFoundError:
        portfolio_customized_triggers = None

    for code, quantity in zip(portfolio_codes, portfolio_quantities):
        try:
            longAggressiveRatio = portfolio_customized_triggers.loc[code, "longAggressiveRatio"]
            longPassiveRatio = portfolio_customized_triggers.loc[code, "longPassiveRatio"]
            shortAggressiveRatio = portfolio_customized_triggers.loc[code, "shortAggressiveRatio"]
            shortPassiveRatio = portfolio_customized_triggers.loc[code, "shortPassiveRatio"]
        except (AttributeError, KeyError):
            print("No customized triggers for {}, try to use general triggers instead".format(code))

            if quantity == 0:
                print("Zero quantity for {}".format(code))
                continue

            triggerRatioDict = generateGeneralTrigger(code, end_date)

            longAggressiveRatio = triggerRatioDict["longAggressiveRatio"]
            longPassiveRatio = triggerRatioDict["longPassiveRatio"]
            shortAggressiveRatio = triggerRatioDict["shortAggressiveRatio"]
            shortPassiveRatio = triggerRatioDict["shortPassiveRatio"]

        json_param_tmp = deepcopy(json_param)
        json_param_tmp["历史数据日期"] = last_trading_day[:4] + "-" + last_trading_day[4:6] + "-" + last_trading_day[6:]
        json_param_tmp["longAggressiveRatio"] = str(longAggressiveRatio)
        json_param_tmp["longPassiveRatio"] = str(longPassiveRatio)
        json_param_tmp["shortAggressiveRatio"] = str(shortAggressiveRatio)
        json_param_tmp["shortPassiveRatio"] = str(shortPassiveRatio)
        json_param_tmp["目标持仓"] = generateTimetableAndTargetQtyInterval(code, quantity, int(next_trading_day), period)

        with open(output_path + code + ".json", "w", encoding="utf-8") as f:
            json.dump(json_param_tmp, f, ensure_ascii=False)

    print(len(portfolio_codes))


if __name__ == "__main__":
    main()
