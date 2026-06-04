import xquant.thirdpartydata.quant as xq
for i in range(50):
    t = xq.tradingDay(20160816,20160820)
print(t)


stocks = xq.hset(xq.PlateType.MARKET, 20190701, xq.MarketType.ALLA)
#print(stocks[0])
result = xq.hfactor(stocks[0] , xq.Factors.growth_cagr_netprofit, [20190930, -3])
#result = xq.hfactor(stocks[0][0] , xq.Factors.open, [20190701])
print(result[0])
