import pandas as pd
import os
import time
import json
from AutoMiningFrame.DataCaculation.entry.FactorCalcBatch import calc_factors_by_config,calc_per_factor_by_file
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from xquant.factordata import FactorData
import json
import dolphindb as ddb
fd = FactorData()
import sys

def calc_and_save_factors(config_path, file_path, start_date, end_date, target_securities, non_factor_path, return_mode='show', study_scenario='stock', data_type='enhanced_tick'):
    calc_data_type = data_type
    save_data_type = data_type
    
    if data_type == 'enhanced_tick_norm':
        calc_data_type = 'enhanced_tick'
        save_data_type = 'enhanced_tick_norm'    
    fp = FactorProvider()
    sh_config_path = "factor_config_l2p_se.json"
    se_config_path = "factor_config_l2p_se.json"
    sh_config_file = os.path.join(config_path, sh_config_path)
    se_config_file = os.path.join(config_path, se_config_path)
    
    sh_stocks = [i for i in target_securities if i.endswith(".SH")]
    se_stocks = [i for i in target_securities if i.endswith(".SZ")]
    if len(sh_stocks)>0:
        sh_res = calc_factors_by_config(sh_config_file, file_path, start_date, end_date, sh_stocks, return_mode=return_mode, non_factor_path=non_factor_path, study_scenario=study_scenario, data_type=calc_data_type)
        #print(sh_res.head())
        for stock in sh_stocks:
            sh_res_temp = sh_res[sh_res['M_HTSCSecurityID']==stock]
            if sh_res_temp.shape[0]>0:
                fp.save_public_data_to_dfs(sh_res_temp, factor_type='factor', data_type=save_data_type)

    if len(se_stocks)>0:
        se_res = calc_factors_by_config(se_config_file, file_path, start_date, end_date, se_stocks, return_mode=return_mode, non_factor_path=non_factor_path, study_scenario=study_scenario, data_type=calc_data_type)
        #print(se_res.head())
        for stock in se_stocks:
            se_res_temp = se_res[se_res['M_HTSCSecurityID']==stock]
            if se_res_temp.shape[0]>0:
                fp.save_public_data_to_dfs(se_res_temp, factor_type='factor', data_type=save_data_type)
    return

def gen_configs(config_path,file_path,factor_list=None):
    a = open(os.path.join(config_path,"factor_config_l2p_se.json"),'w')
    res_dict = {}
    for root,dir,files in os.walk(file_path):
        for file in files:
            if factor_list:
                if file[:-4] not in factor_list:
                    continue
            contents = open(os.path.join(root,file),"r").read()
            #if "NumBidOrders" in contents or "NumOfferOrders" in contents or "TotalBuyNumber" in contents or "TotalSellNumber" in contents or "MaxDuration" in contents or "Withdraw" in contents :
           #     continue
            if "FactorBookDeapBalPlusMavgRatio" in contents or "FactorLYWDistinceZScore" in contents or "M_BuyCount" in contents or "M_SellCount" in contents or "M_NumOfferOrders" in contents or "M_NumBidOrders" in contents or "M_Withdraw" in contents or "TotalBidNumber" in contents or "TotalOfferNumber" in contents or "BidTradeMaxDuration" in contents or "OfferTradeMaxDuration" in contents or "M_NumTrades" in contents:
                continue
            if file.startswith("FactorT") and file[7].isupper():
                continue
            if file.endswith(".dos"):
                res_dict[file[:-4]] = [{}]
    a.write(json.dumps(res_dict))

    b = open(os.path.join(config_path, "factor_config_l2p_sh.json"),'w')
    res_dict = {}
    for root,dir,files in os.walk(file_path):
        for file in files:
            if factor_list:
                if file[:-4] not in factor_list:
                    continue
            contents = open(os.path.join(root,file),"r").read()
            
            if "DiffPx" in contents:
                continue
            if file.startswith("FactorT") and file[7].isupper():
                continue
            contents = open(os.path.join(root,file),"r").read()
            if file.endswith(".dos"):
                res_dict[file[:-4]] = [{}]
    b.write(json.dumps(res_dict))
    return


def get_stock_list():
    s = ddb.session()
    s.connect("168.17.249.172", 8902, 'admin', '123456')
    dbname="dfs://CustomData/sz_stock_tick_l2p_persec"
    tbname = "sz_stock_tick_l2p_persec"
    se_stocks = s.run(f"""
    dbname = '{dbname}'
    tbname = `{tbname}
    stocks = exec distinct(M_HTSCSecurityID) from loadTable(dbname, tbname)
    stocks
    """)
    se_stocks = list(se_stocks)

    dbname="dfs://CustomData/sh_stock_tick_l2p_persec"
    tbname = "sh_stock_tick_l2p_persec"
    sh_stocks = s.run(f"""
    dbname = '{dbname}'
    tbname = `{tbname}
    stocks = exec distinct(M_HTSCSecurityID) from loadTable(dbname, tbname)
    stocks
    """)
    sh_stocks = list(sh_stocks)
    stocks = se_stocks+sh_stocks
    return stocks


def main(start_date, end_date, target_securities,factor_list=None):
    
    file_path = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-2]), "factors/norm_factors/new_factors")
    non_factor_path = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-2]), "factors/norm_factors/new_non_factors")
    config_path = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-2]), "data_update")
    gen_configs(config_path, file_path,factor_list)    
    calc_and_save_factors(config_path, file_path, start_date, end_date, target_securities, non_factor_path, return_mode='show', study_scenario='stock', data_type='tick_l2p')
    return

if __name__ == "__main__":
    import time
    #factor_list = ['FactorNSWMountValleyWeightMidPx', 'FactorNSWOrderNumRatioTrend', 'FactorNSWOrderWeightRatioTrend', 'FactorNSWOrderWeightRatioCount', 'FactorNSWOrderBuyWeightRatioTrend', 'FactorNSWBuySellOrderDeltaAmountRatio', 'FactorNSWBuyWeightPriceSkew', 'FactorNSWSellOrderQtySkew', 'FactorNSWOrderNumRatio', 'FactorNSWSellOrderExRet', 'FactorNSWBuyOrderExRet', 'FactorNSWActiveSmallBuyAmtStrength', 'FactorNSWSellAmtPreTradeMA', 'FactorNSWBuyAmtPreTradeMA', 'FactorNSWBuyOrderPriceRetCorr']
    factor_list = None
    from xquant.factordata import FactorData
    fd = FactorData()
    #target_securities = sorted(get_stock_list())
    securities_list = ['688169.SH', '688188.SH', '688301.SH', '688072.SH', '688120.SH', '688052.SH', '688390.SH', '600563.SH', '603688.SH', '688114.SH', '603882.SH', '603160.SH', '603338.SH', '603658.SH', '603596.SH', '688234.SH', '600486.SH', '688099.SH', '688220.SH', '603379.SH', '603589.SH', '600129.SH', '603939.SH', '688122.SH', '688521.SH', '603606.SH', '688002.SH', '603816.SH', '600566.SH', '600038.SH', '600298.SH', '600511.SH', '688180.SH', '600536.SH', '689009.SH', '600161.SH', '603712.SH', '603927.SH', '600529.SH', '600885.SH', '603156.SH', '603000.SH', '600118.SH', '603233.SH', '600060.SH', '605358.SH', '601966.SH', '600079.SH', '600482.SH', '600985.SH', '600546.SH', '603456.SH', '600160.SH', '600862.SH', '600895.SH', '688728.SH', '600096.SH', '600141.SH', '600066.SH', '603858.SH', '601168.SH', '600131.SH', '600549.SH', '600535.SH', '600699.SH', '600498.SH', '600258.SH', '600765.SH', '600859.SH', '601717.SH', '601666.SH', '600373.SH', '688772.SH', '600801.SH', '601231.SH', '603225.SH', '601058.SH', '600418.SH', '600521.SH', '603885.SH', '601233.SH', '600988.SH', '688567.SH', '600380.SH', '600416.SH', '600499.SH', '600970.SH', '600884.SH', '600739.SH', '600348.SH', '601696.SH', '600873.SH', '600848.SH', '601456.SH', '600580.SH', '600153.SH', '600867.SH', '600004.SH', '300394.SZ', '300866.SZ', '300724.SZ', '300502.SZ', '300474.SZ', '000423.SZ', '002028.SZ', '300487.SZ', '002756.SZ', '002409.SZ', '300676.SZ', '300037.SZ', '300558.SZ', '300114.SZ', '002432.SZ', '002025.SZ', '300373.SZ', '300418.SZ', '000513.SZ', '301236.SZ', '002223.SZ', '002557.SZ', '300073.SZ', '002738.SZ', '002595.SZ', '002353.SZ', '000988.SZ', '002294.SZ', '300395.SZ', '000831.SZ', '002281.SZ', '300699.SZ', '300604.SZ', '002430.SZ', '002368.SZ', '002138.SZ', '002831.SZ', '002422.SZ', '300212.SZ', '002463.SZ', '002508.SZ', '002262.SZ', '300601.SZ', '000893.SZ', '002472.SZ', '002568.SZ', '002439.SZ', '000400.SZ', '002156.SZ', '300677.SZ', '002444.SZ', '300390.SZ', '002240.SZ', '300595.SZ', '300529.SZ', '002268.SZ', '300285.SZ', '300001.SZ', '300136.SZ', '300244.SZ', '000933.SZ', '000997.SZ', '002008.SZ', '300146.SZ', '002572.SZ', '002128.SZ', '000738.SZ', '300748.SZ', '002299.SZ', '300118.SZ', '000623.SZ', '002372.SZ', '000975.SZ', '002080.SZ', '300003.SZ', '002384.SZ', '002507.SZ', '002625.SZ', '000998.SZ', '000021.SZ', '300207.SZ', '002056.SZ', '002078.SZ', '000960.SZ', '300012.SZ', '002407.SZ', '000519.SZ', '300568.SZ', '000009.SZ', '002155.SZ', '002739.SZ', '000636.SZ', '002517.SZ', '000878.SZ', '002152.SZ', '002624.SZ', '002465.SZ', '002273.SZ', '002497.SZ', '300024.SZ', '002558.SZ', '300144.SZ', '000830.SZ']
    kc50 = fd.hset("INDEX","20240208","000688.SH")['stock'].values.tolist()
    target_securities = sorted(list(set(securities_list)-set(kc50)-set(['000009.SZ','000021.SZ','000400.SZ','000423.SZ','000513.SZ','000519.SZ','000623.SZ','000636.SZ','000738.SZ','000830.SZ','000831.SZ','000878.SZ','000893.SZ','000933.SZ','000960.SZ','000975.SZ','000988.SZ','000997.SZ','000998.SZ','002008.SZ','002025.SZ','002028.SZ','002056.SZ','002078.SZ','002080.SZ','002128.SZ','002138.SZ','002152.SZ','002155.SZ','002156.SZ','002223.SZ','002240.SZ','002262.SZ','002268.SZ','002273.SZ','002281.SZ','002294.SZ','002299.SZ','002353.SZ','002368.SZ','002372.SZ','002384.SZ','002407.SZ','002409.SZ','002422.SZ','002430.SZ','002432.SZ','002439.SZ','002444.SZ','002463.SZ','002465.SZ','002472.SZ','002497.SZ','002507.SZ','002508.SZ','002517.SZ','002557.SZ','002558.SZ','002568.SZ','002572.SZ','002595.SZ','002624.SZ','002625.SZ','002738.SZ','002739.SZ','002756.SZ','002831.SZ','300001.SZ','300003.SZ','300012.SZ','300024.SZ','300037.SZ','300073.SZ','300114.SZ','300118.SZ','300136.SZ','300144.SZ','300146.SZ','300207.SZ','300212.SZ','300244.SZ','300285.SZ','300373.SZ','300390.SZ','300394.SZ','300395.SZ','300418.SZ','300474.SZ','300487.SZ','300502.SZ','300529.SZ','300558.SZ','300568.SZ','300595.SZ','300601.SZ','300604.SZ','300676.SZ','300677.SZ','300699.SZ','300724.SZ','300748.SZ','300866.SZ','301236.SZ','600536.SH','603688.SH','689009.SH']))) 
    print(len(target_securities))
    start_month_list = sorted([str(i)+"0101" for i in range(2022,2025)]+[str(i)+"0701" for i in range(2022,2025)])
    end_month_list = sorted([str(i)+"0630" for i in range(2022,2025)]+[str(i)+"1231" for i in range(2022,2025)])
    month_list = sorted(list(set(zip(start_month_list,end_month_list))))
    for stock in target_securities:
        print(stock, target_securities.index(stock)/len(target_securities))
        for start_date,end_date in month_list:
            try:
                st = time.time()
                main(start_date, end_date, [stock],factor_list)
                print("[FactorCalcBatch] time total cost:{}".format(time.time()-st))
            except:
                #raise Exception()
                print("{} {} {} 无数据".format(stock,start_date,end_date))
