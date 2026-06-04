import os
import json
import datetime as dt
from xquant.factordata import FactorData


def main(date):
    fd = FactorData()

    cbDF = fd.get_factor_value(
        "WIND_CCBondIssuance",
        factors=["S_INFO_WINDCODE", "IS_CONVERTIBLE_BONDS", "S_INFO_COMPCODE"],
        S_INFO_WINDCODE="like'%.S%'",
        IS_CONVERTIBLE_BONDS="1"
    ).dropna().drop_duplicates()
    cbSeries = cbDF.set_index("S_INFO_WINDCODE")["S_INFO_COMPCODE"]

    sDF = fd.get_factor_value(
        "WIND_AShareDescription",
        factors=["S_INFO_WINDCODE", "S_INFO_COMPCODE", "S_INFO_LISTDATE"],
    ).dropna().drop_duplicates()
    sDF = sDF.set_index("S_INFO_COMPCODE")
    sCounts = sDF["S_INFO_WINDCODE"].index.value_counts()

    zzzg = {}
    for cbCode in cbSeries.index:
        cbCompCode = cbSeries.loc[cbCode]
        if cbCompCode in sDF.index:
            if sCounts.loc[cbCompCode] > 1:
                zzzg[cbCode] = sDF.loc[cbCompCode].sort_values(
                    "S_INFO_LISTDATE",
                    ascending=False
                )["S_INFO_WINDCODE"].tolist()
            else:
                zzzg[cbCode] = [sDF.loc[cbCompCode, "S_INFO_WINDCODE"]]

    if not os.path.exists("/data/user/666888/WuKong/CBMap/"):
        os.makedirs("/data/user/666888/WuKong/CBMap/")

    with open("/data/user/666888/WuKong/CBMap/CBMap_{}.json".format(date), "w") as f:
        json.dump(zzzg, f)


if __name__ == "__main__":
    date = dt.datetime.now().strftime("%Y%m%d")
    # date = "20200403"

    main(date)
