from xquant.factordata import FactorData

s = FactorData()


df  = s.hset('MARKET', '20241121', 'ALLA_HIS')
stocks = df['stock'].tolist()
print(stocks[:10])
print(len(stocks))
stock_bj = [i for i in stocks if i.endswith('.BJ')]
print(stock_bj[:10])
print(len(stock_bj))


