import numpy as np
import pandas as pd
import os
import tqdm
from xquant.factordata import FactorData
import datetime
fa = FactorData()
from TradingDate import getNDaysOff



today = datetime.datetime.now().strftime("%Y%m%d")
today = '20230912'
endDate = str(getNDaysOff(int(today), 1))

print(endDate)
dateList1 = fa.tradingday('20210901', '20211231')
dateList2 = fa.tradingday('20220101', '20220717')
dateList3 = fa.tradingday('20220718', '20221115')
dateList4 = fa.tradingday('20221116', '20230106')
dateList5 = fa.tradingday('20230109', endDate)
dateList6 = fa.tradingday('20230109', '20230308')
dateList7 = fa.tradingday('20230309', "20230730")
dateList8 = fa.tradingday("20230730", endDate)
paths1 = [f'/data/user/011668/MarginSelect/AlbestDaily/bt-{date}/margin-ExecutorAlbestSPIntra-ray_algo_20210201_20210324/'
             for date in dateList1
    ]
paths2 = [f'/data/user/011668/MarginSelect/AlbestDaily/bt-{date}/margin-ExecutorAlbestSPIntra-ray_albest_20211101_20211116/'
             for date in dateList2
    ]
paths3 = [f'/data/user/011668/MarginSelect/AlbestDaily/bt-{date}/margin-ExecutorAlbestSPIntra-ray_albest_20211101_20211116_order/'
             for date in dateList2
    ]
paths4 = [f'/data/user/011668/MarginSelect/AlbestDaily/bt-{date}/margin-ExecutorAlbestSPIntra-ray_barwa_20220201_20220414/'
             for date in dateList3
    ]
paths5 = [f'/data/user/011668/MarginSelect/AlbestDaily/bt-{date}/margin-ExecutorAlbestSPIntra-ray_barwa_20220201_20220414_order/'
             for date in dateList3
    ]
    
paths6 = [f'/data/user/011668/MarginSelect/AlbestDaily/bt-{date}/margin-ExecutorAlbestSPIntra-ray_barwa_20220601_20220727/'
             for date in dateList4
    ]   
    
paths7 = [f'/data/user/011668/MarginSelect/AlbestDaily/bt-{date}/margin-ExecutorAlbestSPIntra-ray_barwa_20220601_20220727_order/'
             for date in dateList4
    ]
    
paths8 = [f'/data/user/011668/MarginSelect/AlbestDaily/bt-{date}/margin-ExecutorAlbestSPIntra-ray_barwa_20220601_20220727&barwa_20221001_20221218_lgb_sh/'
             for date in dateList5
    ]   
    
paths9 = [f'/data/user/011668/MarginSelect/AlbestDaily/bt-{date}/margin-ExecutorAlbestSPIntra-ray_barwa_20220601_20220727_order&barwa_20221001_20221218_lgb_sz/'
             for date in dateList6
    ]
    
paths10 = [f'/data/user/011668/MarginSelect/AlbestDaily/bt-{date}/margin-ExecutorAlbestSPIntra-ray_barwa_20221001_20221215_order&barwa_20221001_20221218_lgb_sz/'
             for date in dateList7
    ]
paths11 = [f'/data/user/011668/MarginSelect/AlbestDaily/bt-{date}/margin-ExecutorAlbestSPIntra-Albest20221001Order036Signals_1&LGB_Ev20220601Sample_036/'
             for date in dateList8
    ]
paths = [
    '/data/user/011668/MarginSelect/AlbestDaily/bt-20171001-20171231/margin-ExecutorAlbestSPIntra-Albest20170701/',
    '/data/user/011668/MarginSelect/AlbestDaily/bt-20180101-20180430/margin-ExecutorAlbestSPIntra-Albest20170701/',
    '/data/user/011668/MarginSelect/AlbestDaily/bt-20180501-20180831/margin-ExecutorAlbestSPIntra-Albest20170701/',
    '/data/user/011668/MarginSelect/AlbestDaily/bt-20180901-20181231/margin-ExecutorAlbestSPIntra-Albest20170701/',
    '/data/user/011668/MarginSelect/AlbestDaily/bt-20190101-20190331/margin-ExecutorAlbestSPIntra-Albest20170701/',
    '/data/user/011668/MarginSelect/AlbestDaily/bt-20190401-20191130/margin-ExecutorAlbestSPIntra-Albest20170701/',
    '/data/user/011668/MarginSelect/AlbestDaily/bt-20191201-20191231/margin-ExecutorAlbestSPIntra-SeparateModelSignals/',
    '/data/user/011668/MarginSelect/AlbestDaily/bt-20200101-20200531/margin-ExecutorAlbestSPIntra-SeparateModelSignals/',
    '/data/user/011668/MarginSelect/AlbestDaily/bt-20200601-20200930/margin-ExecutorAlbestSPIntra-SeparateModelSignals/',
    '/data/user/011668/MarginSelect/AlbestDaily/bt-20201001-20201231/margin-ExecutorAlbestSPIntra-big_algo_20200801_0923/',
    '/data/user/011668/MarginSelect/AlbestDaily/bt-20210101-20210331/margin-ExecutorAlbestSPIntra-algo_20201101_20201123/',
    '/data/user/011668/MarginSelect/AlbestDaily/bt-20210401-20210831/margin-ExecutorAlbestSPIntra-ray_algo_20210201_20210324/',
]
paths += paths1 + paths2 + paths3 + paths4 + paths5 + paths6 + paths7 + paths8 + paths9 + paths10 +paths11


date_map = {
    "Albest20170701": ("20171001", "20191130"), 
    "SeparateModelSignals": ("20191201", "20200930"),
    "big_algo_20200801_0923": ("20201001", "20201231"),
    "algo_20201101_20201123": ("20210101", "20210331"),
    "ray_algo_20210201_20210324": ("20210401", "20211231"),
    "ray_albest_20211101_20211116": ("20220101", "20220717"), 
    "ray_albest_20211101_20211116_order": ("20220101", "20220717"), 
    "ray_barwa_20220201_20220414": ("20220718", '20221115'), 
    "ray_barwa_20220201_20220414_order": ("20220718", '20221115'),
    "ray_barwa_20220601_20220727": ("20221116", '20230106'), 
    "ray_barwa_20220601_20220727_order": ("20221116", '20230106'),
    "ray_barwa_20220601_20220727&barwa_20221001_20221218_lgb_sh": ("20230109", endDate), 
    "ray_barwa_20220601_20220727_order&barwa_20221001_20221218_lgb_sz": ("20230109", '20230308'),
    "ray_barwa_20221001_20221215_order&barwa_20221001_20221218_lgb_sz": ("20230309", "20230730"),
    "Albest20221001Order036Signals_1&LGB_Ev20220601Sample_036": ("20230731", endDate)
}

longHoldSecond = []
longCumAmount = []
longOrderAmount = []
longAfterCostProfit = []
longReturnRate = []
shortHoldSecond = []
shortCumAmount = []
shortOrderAmount = []
shortAfterCostProfit = []
shortReturnRate = []
totalHoldSecond = []
totalCumAmount = []
totalOrderAmount = []
totalAfterCostProfit = []
totalReturnRate = []
tradeSize = []
winRatio = []
lossRatio = []
winLoseRatio = []
singleMaxLoss = []
cancelRatio = []

for path in tqdm.tqdm(paths):
    name = path.split('/')[-2].split('-')[-1]
    for key, value in date_map.items():
        start_date = value[0]
        end_date = value[1]
        if key == name:
            break
    start_date2 = start_date[:4]+'-'+start_date[4:6]+'-'+start_date[6:8]
    end_date2 = end_date[:4]+'-'+end_date[4:6]+'-'+end_date[6:8]
    
    tmp = pd.read_pickle(path + 'CombineData/trades.pickle')
    tmp['holdSecond'] = tmp['endTime'].apply(lambda x: datetime.datetime.strptime(f"{x}", "%H:%M:%S").timestamp()) - tmp['startTime'].apply(lambda x: datetime.datetime.strptime(f"{x}", "%H:%M:%S").timestamp())
    tmp['holdSecond'] = tmp['holdSecond'].apply(lambda x:int(x))

    long_tmp = tmp[tmp['direction'] == 'long ']
    long_tmp = long_tmp.groupby(['date','code'])['holdSecond','cumAmount','orderAmount','afterCostProfit','returnRate'].mean()
    long_tmp = long_tmp.rename(columns={"holdSecond": "longHoldSecond", "cumAmount": "longCumAmount", 'orderAmount':'longOrderAmount',
                                       'afterCostProfit':'longAfterCostProfit', 'returnRate':'longReturnRate'})

    short_tmp = tmp[tmp['direction'] == 'short']
    short_tmp = short_tmp.groupby(['date','code'])['holdSecond','cumAmount','orderAmount','afterCostProfit','returnRate'].mean()
    short_tmp = short_tmp.rename(columns={"holdSecond": "shortHoldSecond", "cumAmount": "shortCumAmount", 'orderAmount':'shortOrderAmount',
                                       'afterCostProfit':'shortAfterCostProfit', 'returnRate':'shortReturnRate'})

    total_tmp = tmp.groupby(['date','code'])['holdSecond','cumAmount','orderAmount','afterCostProfit','returnRate'].mean()
    total_tmp = total_tmp.rename(columns={"holdSecond": "totalHoldSecond", "cumAmount": "totalCumAmount", 'orderAmount':'totalOrderAmount',
                                       'afterCostProfit':'totalAfterCostProfit', 'returnRate':'totalReturnRate'})

    longHoldSecond.append(long_tmp['longHoldSecond'].loc[start_date:end_date])
    longCumAmount.append(long_tmp['longCumAmount'].loc[start_date:end_date])
    longOrderAmount.append(long_tmp['longOrderAmount'].loc[start_date:end_date])
    longAfterCostProfit.append(long_tmp['longAfterCostProfit'].loc[start_date:end_date])
    longReturnRate.append(long_tmp['longReturnRate'].loc[start_date:end_date])
    shortHoldSecond.append(short_tmp['shortHoldSecond'].loc[start_date:end_date])
    shortCumAmount.append(short_tmp['shortCumAmount'].loc[start_date:end_date])
    shortOrderAmount.append(short_tmp['shortOrderAmount'].loc[start_date:end_date])
    shortAfterCostProfit.append(short_tmp['shortAfterCostProfit'].loc[start_date:end_date])
    shortReturnRate.append(short_tmp['shortReturnRate'].loc[start_date:end_date])
    totalHoldSecond.append(total_tmp['totalHoldSecond'].loc[start_date:end_date])
    totalCumAmount.append(total_tmp['totalCumAmount'].loc[start_date:end_date])
    totalOrderAmount.append(total_tmp['totalOrderAmount'].loc[start_date:end_date])
    totalAfterCostProfit.append(total_tmp['totalAfterCostProfit'].loc[start_date:end_date])
    totalReturnRate.append(total_tmp['totalReturnRate'].loc[start_date:end_date])

    tmp = pd.read_pickle(path + 'CombineData/daily.pickle')
    tmp = tmp.rename(columns={'日期': 'date'})
    tmp = tmp.groupby(['date','code'])[['交易总市值','获利收益率','亏损收益率','盈亏比','最大单笔亏损','撤单比']].mean()
    tmp = tmp.rename(columns={"交易总市值": "tradeSize", "获利收益率": "winRatio", '亏损收益率':'lossRatio',
                                       '盈亏比':'winLoseRatio', '最大单笔亏损':'singleMaxLoss', '撤单比':'cancelRatio'})

    tradeSize.append(tmp['tradeSize'].loc[start_date2:end_date2])
    winRatio.append(tmp['winRatio'].loc[start_date2:end_date2])
    lossRatio.append(tmp['lossRatio'].loc[start_date2:end_date2])
    winLoseRatio.append(tmp['winLoseRatio'].loc[start_date2:end_date2])
    singleMaxLoss.append(tmp['singleMaxLoss'].loc[start_date2:end_date2])
    cancelRatio.append(tmp['cancelRatio'].loc[start_date2:end_date2])


longHoldSecond = pd.concat(longHoldSecond).sort_index().unstack()
longCumAmount = pd.concat(longCumAmount).sort_index().unstack()
longOrderAmount = pd.concat(longOrderAmount).sort_index().unstack()
longAfterCostProfit = pd.concat(longAfterCostProfit).sort_index().unstack()
longReturnRate = pd.concat(longReturnRate).sort_index().unstack()
shortHoldSecond = pd.concat(shortHoldSecond).sort_index().unstack()
shortCumAmount = pd.concat(shortCumAmount).sort_index().unstack()
shortOrderAmount = pd.concat(shortOrderAmount).sort_index().unstack()
shortAfterCostProfit = pd.concat(shortAfterCostProfit).sort_index().unstack()
shortReturnRate = pd.concat(shortReturnRate).sort_index().unstack()
totalHoldSecond = pd.concat(totalHoldSecond).sort_index().unstack()
totalCumAmount = pd.concat(totalCumAmount).sort_index().unstack()
totalOrderAmount = pd.concat(totalOrderAmount).sort_index().unstack()
totalAfterCostProfit = pd.concat(totalAfterCostProfit).sort_index().unstack()
totalReturnRate = pd.concat(totalReturnRate).sort_index().unstack()
tradeSize = pd.concat(tradeSize).sort_index().unstack()
winRatio = pd.concat(winRatio).sort_index().unstack()
lossRatio = pd.concat(lossRatio).sort_index().unstack()
winLoseRatio = pd.concat(winLoseRatio).sort_index().unstack()
singleMaxLoss = pd.concat(singleMaxLoss).sort_index().unstack()
cancelRatio = pd.concat(cancelRatio).sort_index().unstack()


tradeSize.index = [''.join(i.split('-')) for i in tradeSize.index.tolist()]
winRatio.index = [''.join(i.split('-')) for i in winRatio.index.tolist()]
lossRatio.index = [''.join(i.split('-')) for i in lossRatio.index.tolist()]
winLoseRatio.index = [''.join(i.split('-')) for i in winLoseRatio.index.tolist()]
singleMaxLoss.index = [''.join(i.split('-')) for i in singleMaxLoss.index.tolist()]
cancelRatio.index = [''.join(i.split('-')) for i in cancelRatio.index.tolist()]


longHoldSecond.index.name = 'mddate'
longHoldSecond.columns.name = 'stock'

longCumAmount.index.name = 'mddate'
longCumAmount.columns.name = 'stock'

longOrderAmount.index.name = 'mddate'
longOrderAmount.columns.name = 'stock'

longAfterCostProfit.index.name = 'mddate'
longAfterCostProfit.columns.name = 'stock'

longReturnRate.index.name = 'mddate'
longReturnRate.columns.name = 'stock'

shortHoldSecond.index.name = 'mddate'
shortHoldSecond.columns.name = 'stock'

shortCumAmount.index.name = 'mddate'
shortCumAmount.columns.name = 'stock'

shortOrderAmount.index.name = 'mddate'
shortOrderAmount.columns.name = 'stock'

shortAfterCostProfit.index.name = 'mddate'
shortAfterCostProfit.columns.name = 'stock'

shortReturnRate.index.name = 'mddate'
shortReturnRate.columns.name = 'stock'

totalHoldSecond.index.name = 'mddate'
totalHoldSecond.columns.name = 'stock'

totalCumAmount.index.name = 'mddate'
totalCumAmount.columns.name = 'stock'

totalOrderAmount.index.name = 'mddate'
totalOrderAmount.columns.name = 'stock'

totalAfterCostProfit.index.name = 'mddate'
totalAfterCostProfit.columns.name = 'stock'

totalReturnRate.index.name = 'mddate'
totalReturnRate.columns.name = 'stock'

tradeSize.index.name = 'mddate'
tradeSize.columns.name = 'stock'

winRatio.index.name = 'mddate'
winRatio.columns.name = 'stock'

lossRatio.index.name = 'mddate'
lossRatio.columns.name = 'stock'

winLoseRatio.index.name = 'mddate'
winLoseRatio.columns.name = 'stock'

singleMaxLoss.index.name = 'mddate'
singleMaxLoss.columns.name = 'stock'

cancelRatio.index.name = 'mddate'
cancelRatio.columns.name = 'stock'


data_length = len(fa.tradingday('20171001', endDate))
assert longHoldSecond.shape[0] == data_length, print('longHoldSecond has problem.')
assert longCumAmount.shape[0] == data_length, print('longCumAmount has problem.')
assert longOrderAmount.shape[0] == data_length, print('longOrderAmount has problem.')
assert longAfterCostProfit.shape[0] == data_length, print('longAfterCostProfit has problem.')
assert longReturnRate.shape[0] == data_length, print('longReturnRate has problem.')
assert shortHoldSecond.shape[0] == data_length, print('shortHoldSecond has problem.')
assert shortCumAmount.shape[0] == data_length, print('shortCumAmount has problem.')
assert shortOrderAmount.shape[0] == data_length, print('shortOrderAmount has problem.')
assert shortAfterCostProfit.shape[0] == data_length, print('shortAfterCostProfit has problem.')
assert shortReturnRate.shape[0] == data_length, print('shortReturnRate has problem.')
assert totalHoldSecond.shape[0] == data_length, print('totalHoldSecond has problem.')
assert totalCumAmount.shape[0] == data_length, print('totalCumAmount has problem.')
assert totalOrderAmount.shape[0] == data_length, print('totalOrderAmount has problem.')
assert totalAfterCostProfit.shape[0] == data_length, print('totalAfterCostProfit has problem.')
assert totalReturnRate.shape[0] == data_length, print('totalReturnRate has problem.')
assert tradeSize.shape[0] == data_length, print('tradeSize has problem.')
assert winRatio.shape[0] == data_length, print('winRatio has problem.')
assert lossRatio.shape[0] == data_length, print('lossRatio has problem.')
assert winLoseRatio.shape[0] == data_length, print('winLoseRatio has problem.')
assert singleMaxLoss.shape[0] == data_length, print('singleMaxLoss has problem.')
assert cancelRatio.shape[0] == data_length, print('cancelRatio has problem.')


longHoldSecond = longHoldSecond.sort_index()
longCumAmount = longCumAmount.sort_index()
longOrderAmount = longOrderAmount.sort_index()
longAfterCostProfit = longAfterCostProfit.sort_index()
longReturnRate = longReturnRate.sort_index()
shortHoldSecond = shortHoldSecond.sort_index()
shortCumAmount = shortCumAmount.sort_index()
shortOrderAmount = shortOrderAmount.sort_index()
shortAfterCostProfit = shortAfterCostProfit.sort_index()
shortReturnRate = shortReturnRate.sort_index()
totalHoldSecond = totalHoldSecond.sort_index()
totalCumAmount = totalCumAmount.sort_index()
totalOrderAmount = totalOrderAmount.sort_index()
totalAfterCostProfit = totalAfterCostProfit.sort_index()
totalReturnRate = totalReturnRate.sort_index()
tradeSize = tradeSize.sort_index()
winRatio = winRatio.sort_index()
lossRatio = lossRatio.sort_index()
winLoseRatio = winLoseRatio.sort_index()
singleMaxLoss = singleMaxLoss.sort_index()
cancelRatio = cancelRatio.sort_index()


data_name = '/data/user/018106/RQXG/data/'

longHoldSecond.to_pickle(f'{data_name}longHoldSecond.pkl')
longCumAmount.to_pickle(f'{data_name}longCumAmount.pkl')
longOrderAmount.to_pickle(f'{data_name}longOrderAmount.pkl')
longAfterCostProfit.to_pickle(f'{data_name}longAfterCostProfit.pkl')
longReturnRate.to_pickle(f'{data_name}longReturnRate.pkl')
shortHoldSecond.to_pickle(f'{data_name}shortHoldSecond.pkl')
shortCumAmount.to_pickle(f'{data_name}shortCumAmount.pkl')
shortOrderAmount.to_pickle(f'{data_name}shortOrderAmount.pkl')
shortAfterCostProfit.to_pickle(f'{data_name}shortAfterCostProfit.pkl')
shortReturnRate.to_pickle(f'{data_name}shortReturnRate.pkl')
totalHoldSecond.to_pickle(f'{data_name}totalHoldSecond.pkl')
totalCumAmount.to_pickle(f'{data_name}totalCumAmount.pkl')
totalOrderAmount.to_pickle(f'{data_name}totalOrderAmount.pkl')
totalAfterCostProfit.to_pickle(f'{data_name}totalAfterCostProfit.pkl')
totalReturnRate.to_pickle(f'{data_name}totalReturnRate.pkl')
tradeSize.to_pickle(f'{data_name}tradeSize.pkl')
winRatio.to_pickle(f'{data_name}winRatio.pkl')
lossRatio.to_pickle(f'{data_name}lossRatio.pkl')
winLoseRatio.to_pickle(f'{data_name}winLoseRatio.pkl')
singleMaxLoss.to_pickle(f'{data_name}singleMaxLoss.pkl')
cancelRatio.to_pickle(f'{data_name}cancelRatio.pkl')

