path = "/app/data/666888/BT_Results/results/"
import os
import pandas as pd
print(list(os.listdir(path)))

date_list = []
for date in os.listdir(path):
    if len(date)==8:
        date_list.append(date)
print(date_list)
date_list.sort()

if True:
    summary = pd.DataFrame(index=date_list, columns=["research", "production", "h300", "z500"])
    for date in date_list:
        for file in os.listdir(path+date):
            try:
                if "research" in file:
                    # print(file)
                    research = pd.read_excel(os.path.join(path, date, file, "TotalSummary.xls"))
                    # print(research.afterCostProfit.sum())
                    # print(research.initAmount.sum())
                    print(research.afterCostProfit.sum()/research.initAmount.sum()*250)
                    summary.loc[date, "research"] = research.afterCostProfit.sum()
                if "production" in file:
                    production = pd.read_excel(os.path.join(path, date, file, "TotalSummary.xls"))
                    summary.loc[date, "production"] = production.afterCostProfit.sum()
                    
                if "h300" in file:
                    production = pd.read_excel(os.path.join(path, date, file, "TotalSummary.xls"))
                    summary.loc[date, "h300"] = production.afterCostProfit.sum()      
                if "z500" in file:
                    production = pd.read_excel(os.path.join(path, date, file, "TotalSummary.xls"))
                    summary.loc[date, "z500"] = production.afterCostProfit.sum()         
            except Exception as e:
                pass  
    summary.to_csv("/app/data/666888/Logging/money.csv") 


summary = pd.DataFrame(index=date_list, columns=["research", "production", "h300", "z500"])
a,b,c,d = 1,1,1,1

if True:
    for date in date_list:
        for file in os.listdir(path+date):
            try:
                if "research" in file:
                    # print(file)
                    research = pd.read_excel(os.path.join(path, date, file, "TotalSummary.xls"))
                    # print(research.afterCostProfit.sum())
                    # print(research.initAmount.sum())
                    a = (research.afterCostProfit.sum()/research.initAmount.sum()+1)*a
                    summary.loc[date, "research"] = a
                if "production" in file:
                    production = pd.read_excel(os.path.join(path, date, file, "TotalSummary.xls"))
                    b = (research.afterCostProfit.sum()/research.initAmount.sum()+1)*b
                    summary.loc[date, "production"] = b
                    
                if "h300" in file:
                    production = pd.read_excel(os.path.join(path, date, file, "TotalSummary.xls"))
                    c = (research.afterCostProfit.sum()/research.initAmount.sum()+1)*c
                    summary.loc[date, "h300"] = c
                    
                if "z500" in file:
                    production = pd.read_excel(os.path.join(path, date, file, "TotalSummary.xls"))
                    d = (research.afterCostProfit.sum()/research.initAmount.sum()+1)*d
                    summary.loc[date, "z500"] = d    
            except Exception as e:
                pass 
    summary.to_csv("/app/data/666888/Logging/pnl.csv") 
    print(summary)





