import json
import datetime as dt
from xquant.factordata import FactorData
from System.getCBSet import cbond_set


def main(date):
    fd = FactorData()

    ca = fd.get_factor_value("WIND_CBondAmount")
    ca = ca.loc[:, ["S_INFO_WINDCODE", "S_INFO_ENDDATE", "B_INFO_OUTSTANDINGBALANCE"]]
    ca = ca.astype({"S_INFO_WINDCODE": "str", "S_INFO_ENDDATE": "int", "B_INFO_OUTSTANDINGBALANCE": "float"})
    ca = ca.loc[ca["S_INFO_ENDDATE"] <= int(date), :]
    ca = ca.sort_values(["S_INFO_WINDCODE", "S_INFO_ENDDATE"])

    amountDict = {}
    for stock, amountDF in ca.groupby("S_INFO_WINDCODE"):
        amountDict[stock] = amountDF["B_INFO_OUTSTANDINGBALANCE"].iloc[-1]

    resDict = {}
    bondList = cbond_set(date)
    for stock in bondList:
        if stock not in amountDict:
            print("No record for {}".format(stock))

        resDict[stock] = amountDict[stock]

    import pandas as pd

    pd.Series(resDict).T.to_excel("/data/user/666888/yue.xlsx")


if __name__ == '__main__':
    date = dt.datetime.now().strftime("%Y%m%d")
    date = 20200415
    main(date)
