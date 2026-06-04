from DataAPI import DataToolkit as dtk
import pandas as pd


def main(portfolio, sDate, eDate, initialAmount, resultPath):
    sDate = int(sDate)
    eDate = int(eDate)
    
    portfolioPath = "/data/user/666888/AlgoModelCmp/portfolios/{}.xlsx".format(portfolio)
    resultPath = ("/data/user/666888/AlgoModelCmp/results/{}-{}/".format(sDate, eDate) + resultPath)

    pdf = pd.read_excel(portfolioPath)
    mind = dtk.get_panel_daily_pv_df(pdf.iloc[:, 0].tolist(), sDate, eDate, "close")
    vol = (pdf.set_index("stock")["weight"] * initialAmount / 10000).astype("int") * 100
    dd = mind.multiply(vol, axis=1)
    dd = dd.sum(axis=1)

    rdf = pd.read_excel(resultPath + "/result_daily.xls")
    rdf["总市值"] = dd.tolist()
    rdf["市值收益率"] = (rdf["总盈利"] / rdf["总市值"] * 1000).round(2)
    rdf.to_excel(resultPath + "/result_daily_modified.xlsx")

