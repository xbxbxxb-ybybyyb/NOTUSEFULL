from xquant.factordata import FactorData
s = FactorData()
import pickle

with open('/data/user/018106/TrendFactor/factor_pass/final_0907.pickle', 'rb') as output:
    factorListAll = pickle.load(output)
factorList = factorListAll['oldNotOrder'] + factorListAll['oldOrder'] + factorListAll['SPNotOrder'] + factorListAll[
    'SPOrder']

with open('/data/user/018106/TrendFactor/StockList/FactorCalculateTest/StockChoose.pickle', 'rb') as output:
    stockList = list(pickle.load(output))
for i in factorList:
    print(i)
    factorLYH = s.get_factor_value('Factor_Zeus_2022',stockList[0],'20220602',[i])
factorLST = s.get_factor_value('Factor_Zeus_Plus',stockList[0],'20220601',factorList)