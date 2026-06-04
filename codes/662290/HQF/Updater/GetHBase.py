import os
import sys
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../"))
from xquant.compute.aimr import AIMR
import numpy as np
import pandas as pd
import datetime as dt
import time
import pickle
import DataAPI.DataToolkit as Dtk
from xquant.factordata import FactorData
from AlgoConfig_Apple_48 import start_date,end_date,save_path
xqf = FactorData()

start_idx, end_idx, pid = AIMR.getParam().split('-')
start_idx = int(start_idx)
end_idx = int(end_idx)
print('starting sub tasks    pid=' + pid)


library_name = 'HQF'

trading_days = Dtk.get_trading_day(start_date, end_date)
trading_mins = ['0925',
                '0930', '0931', '0932', '0933', '0934', '0935', '0936', '0937',
                '0938', '0939', '0940', '0941', '0942', '0943', '0944', '0945',
                '0946', '0947', '0948', '0949', '0950', '0951', '0952', '0953',
                '0954', '0955', '0956', '0957', '0958', '0959', '1000', '1001',
                '1002', '1003', '1004', '1005', '1006', '1007', '1008', '1009',
                '1010', '1011', '1012', '1013', '1014', '1015', '1016', '1017',
                '1018', '1019', '1020', '1021', '1022', '1023', '1024', '1025',
                '1026', '1027', '1028', '1029', '1030', '1031', '1032', '1033',
                '1034', '1035', '1036', '1037', '1038', '1039', '1040', '1041',
                '1042', '1043', '1044', '1045', '1046', '1047', '1048', '1049',
                '1050', '1051', '1052', '1053', '1054', '1055', '1056', '1057',
                '1058', '1059', '1100', '1101', '1102', '1103', '1104', '1105',
                '1106', '1107', '1108', '1109', '1110', '1111', '1112', '1113',
                '1114', '1115', '1116', '1117', '1118', '1119', '1120', '1121',
                '1122', '1123', '1124', '1125', '1126', '1127', '1128', '1129',
                '1300', '1301', '1302', '1303', '1304', '1305', '1306', '1307',
                '1308', '1309', '1310', '1311', '1312', '1313', '1314', '1315',
                '1316', '1317', '1318', '1319', '1320', '1321', '1322', '1323',
                '1324', '1325', '1326', '1327', '1328', '1329', '1330', '1331',
                '1332', '1333', '1334', '1335', '1336', '1337', '1338', '1339',
                '1340', '1341', '1342', '1343', '1344', '1345', '1346', '1347',
                '1348', '1349', '1350', '1351', '1352', '1353', '1354', '1355',
                '1356', '1357', '1358', '1359', '1400', '1401', '1402', '1403',
                '1404', '1405', '1406', '1407', '1408', '1409', '1410', '1411',
                '1412', '1413', '1414', '1415', '1416', '1417', '1418', '1419',
                '1420', '1421', '1422', '1423', '1424', '1425', '1426', '1427',
                '1428', '1429', '1430', '1431', '1432', '1433', '1434', '1435',
                '1436', '1437', '1438', '1439', '1440', '1441', '1442', '1443',
                '1444', '1445', '1446', '1447', '1448', '1449', '1450', '1451',
                '1452', '1453', '1454', '1455', '1456',
                '1457', '1458', '1459', '1500']
factor_names = [
    "factorAccAmountBuy",
    "factorAccAmountSell",
    "factorBuyOrderAmt",
    "factorBuyOrderVol",
    "factorSellOrderAmt",
    "factorSellOrderVol",
    "factorActiveBuyOrderAmt",
    "factorActiveBuyOrderVol",
    "factorPassiveBuyOrderAmt",
    "factorPassiveBuyOrderVol",
    "factorActiveSellOrderAmt",
    "factorActiveSellOrderVol",
    "factorPassiveSellOrderAmt",
    "factorPassiveSellOrderVol",
    "factorBuyOrderCanceledAmt",
    "factorBuyOrderCanceledVol",
    "factorSellOrderCanceledAmt",
    "factorSellOrderCanceledVol",
    "factorTradeNum",
    "factorBuyTradeNum",
    "factorBuyTradeAmt",
    "factorBuyTradeVol",
    "factorSellTradeNum",
    "factorSellTradeAmt",
    "factorSellTradeVol"
]



factor_names = factor_names[start_idx:end_idx]


if not os.path.exists(save_path):
    os.mkdir(save_path)

for f, factor in enumerate(factor_names):
    if not os.path.exists(save_path + factor[6:] + '/'):
        os.mkdir(save_path + factor[6:] + '/')
    for d, day in enumerate(trading_days):
        pre_day = Dtk.get_n_days_off(day,-2)[0]
        if os.path.exists(save_path + factor[6:] + '/' + str(day) + '_' + factor[6:] + '.pkl'):
            pass
        data_stockwise = []
        stock_have_data = []
        t1 = time.time()
        stock_list = Dtk.get_complete_stock_list(pre_day)
        stock_list_filter = xqf.stock_filter(stock_list, str(day), filterType='SUSPEND')['stock'].to_list()
        for s, stock_code in enumerate(stock_list_filter):
            try:
                t3 = time.time()
                output = xqf.get_factor_value(library_name, stock_code, str(day), ['timestamp', factor])
                cost = time.time() - t3
                if cost>0.5:
                    print('cost {} seconds 2 get data of {}'.format(round(cost,2),stock_code))
            except AttributeError:
                print(str(day) + '  ' + stock_code + '  ' + factor)
            else:
                timestamp = output['timestamp']
                factor_data = output[factor]
                time_index = pd.to_datetime([dt.datetime.fromtimestamp(item) for item in timestamp])
                factor_data.index = time_index
                factor_data_1min = factor_data.resample('1min').sum()
                data_stockwise.append(factor_data_1min)
                stock_have_data.append(stock_code)
        output_daily = pd.concat(data_stockwise, axis=1)
        output_daily.columns = stock_have_data
        complete_index = pd.MultiIndex.from_product([[str(day)], trading_mins])
        complete_index = [complete_index[i][0] + complete_index[i][1] for i in range(complete_index.__len__())]
        complete_index = [int(item) for item in complete_index]
        complete_index_datetime = pd.to_datetime(Dtk.convert_date_or_time_int_to_datetime(complete_index))
        output_daily = output_daily.reindex(index=complete_index_datetime)
        output_daily.iloc[[0, 238, 239, 240, 241], :] = np.nan
        output_daily[np.isnan(output_daily)] = 0
        output_daily_sum = output_daily.sum(axis=0)
        output_daily.loc[:,output_daily_sum == 0] = np.nan
        output_daily = output_daily.reindex(columns=stock_list)
        t2 = time.time()
        print(str(day) + ' cost' + str(t2-t1) + ' s' + '  pid=' +pid)
        with open(save_path + factor[6:] + '/' + str(day) + '_' + factor[6:] + '.pkl', 'wb') as f:
            pickle.dump(output_daily, f)

print('ending sub tasks    pid=' + pid)

