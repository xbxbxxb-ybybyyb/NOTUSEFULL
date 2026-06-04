from xquant.factordata import FactorData

s = FactorData()
stock = s.hset("MARKET",20181231,"ALLA")
df = s.get_factor_value("Basic_factor",stock=stock,tdate='20181231',factor_names=["apturn","apturndays","maintenance","netturndays","non_currentassetsturn","operatecapitalturn","yoycf","yoydebt","yoyprofit","yoy_assets","yoy_cash","yoy_fixedassets"])
print(df.head())
df.to_csv("factor1231.csv")

