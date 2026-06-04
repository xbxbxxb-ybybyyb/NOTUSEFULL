from xquant.factordata import FactorData

s = FactorData()
stock_1 = s.hset("INDEX", '20221230', "HS300")["stock"].to_list()
stock_2 = s.hset("INDEX", '20221230', "ZZ500")["stock"].to_list()
stock_3 = s.hset("INDEX", '20221230', "ZZ1000")["stock"].to_list()
stock_1 = stock_1 + stock_2 + stock_3
stockList_SH = sorted([each for each in stock_1 if each.endswith("SH")])
import json
with open('/data/user/018106/TrendFactor/FactorList/AlbestFactorList/ray_albest_20220201_20220414_new.json', 'rb') as output:
    Albest = json.load(output)
#    path = '/data/user/018106/TrendFactor/FactorList/Barwa/ray_barwa_20220201_20220414.txt'
#    factor_path = open(path,'r')
#    factor_data = factor_path.readlines()
#    barwa = eval(factor_data[0])
#读因子
path = '/data/user/018106/TrendFactor/FactorList/EverestStockList/everest_use_factors.txt'
factor_path = open(path,'r')
factor_data = factor_path.readlines()
Everest = eval(factor_data[0])
import pickle
with open('/data/user/017023/share/CB_Sample/zg_lyh_115_20230320.pkl', 'rb') as output:
    CB = pickle.load(output)
with open('/data/user/018106/TrendFactor/FactorList/EverestStockList/everest_use_factors_new.pickle','rb') as output:
    Everest_new = pickle.load(output)
factorList = list((set(Albest).union(set(Everest))).union(set(CB)).union(set(Everest_new)))
stock = '600007.SH'
data_1 = s.get_factor_value('Factor_Zeus_Plus_20230725', stock, '20230728', factorList)
data_2 = s.get_factor_value('Factor_Zeus_Plus', stock, '20230728', factorList)
factor_name = []
for stock in stockList_SH:
    try:
        data_1 = s.get_factor_value('Factor_Zeus_Plus_20230725',stock,'20230728',factorList)
        data_2 = s.get_factor_value('Factor_Zeus_Plus',stock,'20230728',factorList)
        # print(stock,(data_1 - data_2).max().loc[(data_1 - data_2).max() != 0].index)
        factor_name +=(data_1 - data_2).max().loc[(data_1 - data_2).max() != 0].index.tolist()
        if 'factorMdf20BidAmtPerTradeZScore' in factor_name:
            print(stock)
    except:
        pass
print(factor_name)
print(set(factor_name))