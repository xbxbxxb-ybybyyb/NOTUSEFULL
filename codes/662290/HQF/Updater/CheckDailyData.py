import time
import os
import sys
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../"))
from AlgoConfig_Apple_48 import save_path,start_date,end_date
import DataAPI.DataToolkit as Dtk
from xquant.factordata import FactorData
import pandas as pd
from xquant.xqutils.helper import link
xqf = FactorData()
lm = link.LinkMessage()



today = end_date

pre_day = Dtk.get_n_days_off(today,-2)[0]

sl = Dtk.get_complete_stock_list(pre_day)
valid_sl = xqf.stock_filter(sl,str(today),'SUSPEND')['stock'].to_list()


factor_names = ['factorAccAmountBuy',
                'factorAccAmountSell',
                'factorBuyOrderAmt',
                'factorBuyOrderVol',
                'factorSellOrderAmt',
                'factorSellOrderVol',
                'factorActiveBuyOrderAmt',
                'factorActiveBuyOrderVol',
                'factorPassiveBuyOrderAmt',
                'factorPassiveBuyOrderVol',
                'factorActiveSellOrderAmt',
                'factorActiveSellOrderVol',
                'factorPassiveSellOrderAmt',
                'factorPassiveSellOrderVol',
                'factorBuyOrderCanceledAmt',
                'factorBuyOrderCanceledVol',
                'factorSellOrderCanceledAmt',
                'factorSellOrderCanceledVol',
                'factorTradeNum',
                'factorBuyTradeNum',
                'factorBuyTradeAmt',
                'factorBuyTradeVol',
                'factorSellTradeNum',
                'factorSellTradeAmt',
                'factorSellTradeVol']

coverage_list = []

for factor in factor_names:
    path = '{}/{}/{}_{}.pkl'.format(save_path,factor[6:],today,factor[6:])
    missing_log = []
    if not os.path.exists(path):
        missing_log.append(factor)
    if missing_log.__len__() > 0:
        lm.sendMessage('{} missing'.format(missing_log))
        raise Exception('{} missing'.format(missing_log))
    valid_num = pd.read_pickle(path).dropna(axis=1,how='all').shape[-1]
    coverage_ratio = valid_num/valid_sl.__len__()
    coverage_list.append(coverage_ratio)

coverage = pd.Series(coverage_list,index=factor_names)

if coverage.min() < 0.95:
    lm.sendMessage('Coverage too low : {}'.format(coverage.min()))
    raise Exception('Coverage too low : {}'.format(coverage.min()))
else:
    print('min coverage = {}'.format(coverage.min()))

with open('/data/user/015618/HQF_Update_Log/{}/{}_HFF.part1'.format(today,today),'wb') as f:
    pass
lm.sendMessage('HQF_daily_data on {} quanlified'.format(today))