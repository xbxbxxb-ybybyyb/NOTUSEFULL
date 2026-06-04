import os
import json
import zipfile
import shutil
import pandas as pd
from copy import deepcopy
from ftplib import FTP
from xquant.factordata import FactorData
fa = FactorData()


def main():
    next_trading_day = "20201103"
    last_trading_day = "20201102"
    cv_path = ("/data/user/666888/WuKong/sources/"
               "20200824-20201030_{}/cv-20200824-20201030_{}-WuKong-maxTurnoverPerOrder-maxExposure_big_cb_stock_20200701_20200413_prod_lag0/"
               .format(next_trading_day, next_trading_day))

    portfolioName = "WuKong_{}.xlsx".format(next_trading_day)
    paramName = "WuKong_{}.zip".format(next_trading_day)

    portfolio_path = "/data/user/666888/WuKong/portfolios/"
    output_path = "/data/user/666888/WuKong/parameters/WuKong_{}/".format(next_trading_day)
    zipPath = "/data/user/666888/WuKong/parameters/{}".format(paramName)

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
        "上午截止时间1": "11:25:00",
        "上午截止时间2": "11:28:00",
        "上午截止时间3": "11:29:00",
        "下午截止时间": "14:52:00",
        "ChaosNum": "20",
        "止损参数": "-10",
        "最大价格偏离度": "0.012",
        "最大单笔委托金额": "100000",
        "最大单边总金额暴露": "200000",
        "最大单边总张数暴露": "50000",
        "风控成交量统计范围秒数": "180",
        "成交量占比上限": "0.2",
        "最大需更新Tick数量": "3",
        "是否强制加载历史数据": "true",
        "模型目录": "resources/WuKongModel/big_cb_stock_20200701_20200413/",
        "是否使用通用模型": "true",
        "是否使用RemoveSelfOrder": "true",
        "FrozenConfig": "0x0a, 0x07, 0x0a, 0x03, 0x43, 0x50, 0x55, 0x10, 0x06",
        "最大可接受系统延迟秒数": "20",
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
        "初始平多阈值重置Tick数目": "20",
        "是否打印因子值": "false",
        "因子值打印开始时间": "09:30:00",
        "因子值打印结束时间": "15:00:00",
        "openLongCoef": "1.0004",
        "closeLongCoef": "0.9995",
        "isConservativeMode": "true",
        "临停清仓激进系数": "0.999",
        "临停清仓保守系数": "0.995",
        "开仓过滤tick数目": "60",
        "价格回撤幅度": "-0.01",
        "多次开仓价格系数": "1.01",
        "初次开仓价格系数": "1.01",
        "平仓价格系数": "0.98",
        "止损平仓价格系数": "0.98",
    }

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    if not os.path.exists("/data/user/666888/WuKong/portfolios/WuKongCBFilterPool_{}.xlsx".format(next_trading_day)):
        shutil.copy(
            "/data/user/015629/ConvertibleBond/CbondPoolManagement/DailyPortfolio/{}/WuKongCBFilterPool_{}.xlsx"
                .format(next_trading_day, next_trading_day),
            "/data/user/666888/WuKong/portfolios/WuKongCBFilterPool_{}.xlsx".format(next_trading_day)
        )

    filterPool = pd.read_excel(
        "/data/user/666888/WuKong/portfolios/WuKongCBFilterPool_{}.xlsx".format(next_trading_day)
    )
    monitorPool = filterPool["Monitor"].tolist()
    yjlPool = filterPool["HighPremiumRatio"].tolist()

#    with open("/data/user/011668/bt_params/params/{}.json".format(next_trading_day), "r") as f:
#        risk_params = json.load(f)
#    maxTurnoverPerOrder = risk_params["maxTurnoverPerOrder"]
#    maxExposure = risk_params["maxExposure"]

    with open("/data/user/666888/WuKong/CBMap/CBMap_{}.json".format(last_trading_day), "r") as f:
        cbMap = json.load(f)

    portfolio_orders = pd.read_excel(portfolio_path + portfolioName)
    portfolio_codes = portfolio_orders.iloc[:, 0].tolist()
    portfolio_quantities = portfolio_orders.iloc[:, 3].tolist()

    counter999 = 0
    counter999List = []
    for code, quantity in zip(portfolio_codes, portfolio_quantities):
#        if code == "123012.SZ":
#            continue
        json_param_tmp = deepcopy(json_param)

        if code in yjlPool:
            json_param_tmp["成交量占比上限"] = "0.15"
        elif code in monitorPool:
            json_param_tmp["成交量占比上限"] = "0.1"

        if False:
#        if code in maxTurnoverPerOrder:
#            maxTurnoverPerOrderTmp = int(maxTurnoverPerOrder[code])
#            maxExposureTmp = int(maxExposure[code])
            maxTurnoverPerOrderTmp = 100000
            maxExposureTmp = 200000
            json_param_tmp["最大单笔委托金额"] = str(maxTurnoverPerOrderTmp)
            json_param_tmp["最大单边总金额暴露"] = str(maxExposureTmp)
        else:
            maxTurnoverPerOrderTmp = 100000
            maxExposureTmp = 200000
            json_param_tmp["最大单笔委托金额"] = str(maxTurnoverPerOrderTmp)
            json_param_tmp["最大单边总金额暴露"] = str(maxExposureTmp)
            print(code, "no risk params")

        json_param_tmp["历史数据日期"] = last_trading_day[:4] + "-" + last_trading_day[4:6] + "-" + last_trading_day[6:]

        if code in cbMap:
            json_param_tmp["对应股票代码"] = cbMap[code][0]
        else:
            json_param_tmp["对应股票代码"] = ""
            print("No ZG for {}".format(code))

        try:
            with open("{}/{}/triggerRatio.json".format(cv_path
                                                       .replace("maxTurnoverPerOrder", str(maxTurnoverPerOrderTmp // 10000))
                                                       .replace("maxExposure", str(maxExposureTmp // 10000)), code), "r") as f:
                triggerRatioDict = json.load(f)

            longTriggerRatio = triggerRatioDict["longTriggerRatio"]
            longCloseRatio = triggerRatioDict["longCloseRatio"]
            shortTriggerRatio = triggerRatioDict["shortTriggerRatio"]
            shortCloseRatio = triggerRatioDict["shortCloseRatio"]

            if longTriggerRatio > 99:
                counter999 += 1
                counter999List.append(code)

            json_param_tmp["longTriggerRatio"] = str(longTriggerRatio)
            json_param_tmp["longCloseRatio"] = str(longCloseRatio)
            json_param_tmp["shortTriggerRatio"] = str(shortTriggerRatio)
            json_param_tmp["shortCloseRatio"] = str(shortCloseRatio)

            with open(output_path + code + ".json", "w", encoding="utf-8") as f:
                json.dump(json_param_tmp, f, ensure_ascii=False)
        except:
            print("No triggers for {}".format(code))

    with zipfile.ZipFile(zipPath, "w") as f:
        for file in os.listdir(output_path):
            f.write("{}/{}".format(output_path, file), "/{}/{}".format(output_path.split("/")[-2], file))

    ftp = FTP()
    ftp.set_debuglevel(0)
    ftp.connect(host="168.8.2.68", port=21)
    ftp.login("xquant", "Xquant-32")

    path1 = "/XQuant/011477/{}/".format(next_trading_day)
    try:
        ftp.cwd(path1)
    except:
        ftp.mkd(path1)
    path2 = "{}/WuKong_{}/".format(path1, next_trading_day)
    try:
        ftp.cwd(path2)
    except:
        ftp.mkd(path2)

    with open(portfolio_path + portfolioName, "rb") as f:
        ftp.storbinary('STOR {0}'.format(path2 + portfolioName), f)

    with open(zipPath, "rb") as f:
        ftp.storbinary('STOR {0}'.format(path2 + paramName), f)

    ftp.quit()
    print(counter999, counter999List)


if __name__ == "__main__":
    main()
