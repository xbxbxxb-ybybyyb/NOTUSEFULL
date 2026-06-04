import os
import pandas as pd


def analyzeLongShortProfits(resultPathList):
    resList = []
    for resultPath in resultPathList:
        for file in os.listdir(resultPath):
            if file[-6:] != "SH.xls" and file[-6:] != "SZ.xls":
                continue

            orderSheet = pd.read_excel("{}/{}".format(resultPath, file), sheet_name="orders")
            for date, dailyData in orderSheet.groupby("date"):
                mask1 = dailyData["direction"] != "short"
                mask2 = dailyData["endTime"] <= "12:00:00"

                longProfitAM = dailyData[mask1 & mask2]["afterCostProfit"].sum()
                shortProfitAM = dailyData[~mask1 & mask2]["afterCostProfit"].sum()
                longProfitPM = dailyData[mask1 & ~mask2]["afterCostProfit"].sum()
                shortProfitPM = dailyData[~mask1 & ~mask2]["afterCostProfit"].sum()

                longAmountAM = dailyData[mask1 & mask2]["cumAmount"].sum()
                shortAmountAM = dailyData[~mask1 & mask2]["cumAmount"].sum()
                longAmountPM = dailyData[mask1 & ~mask2]["cumAmount"].sum()
                shortAmountPM = dailyData[~mask1 & ~mask2]["cumAmount"].sum()

                resList.append(
                    [date, longProfitAM, longAmountAM, shortProfitAM, shortAmountAM, longProfitPM, longAmountPM,
                     shortProfitPM, shortAmountPM, ]
                )

    resColumns = ["Date", "LongProfitAM", "LongAmountAM", "ShortProfitAM", "ShortAmountAM", "LongProfitPM",
                  "LongAmountPM", "ShortProfitPM", "ShortAmountPM", ]
    resDF = pd.DataFrame(resList, columns=resColumns).groupby("Date").sum()

    resDF["LongReturnAM"] = resDF["LongProfitAM"] / resDF["LongAmountAM"]
    resDF["ShortReturnAM"] = resDF["ShortProfitAM"] / resDF["ShortAmountAM"]
    resDF["LongReturnPM"] = resDF["LongProfitPM"] / resDF["LongAmountPM"]
    resDF["ShortReturnPM"] = resDF["ShortProfitPM"] / resDF["ShortAmountPM"]

    resDF = resDF.fillna(0)
    resDF = resDF.sort_values("Date")

    return resDF
