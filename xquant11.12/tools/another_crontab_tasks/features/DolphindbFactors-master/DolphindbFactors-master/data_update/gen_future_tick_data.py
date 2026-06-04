import dolphindb as ddb
import ray
import uuid
import pandas as pd
import re
import time
import os
import pyarrow as pa
import calendar
from xquant.marketdata import MarketData
from xquant.factordata import FactorData
from xquant.futuredata import FutureData
import calendar
import datetime
import sys
import settings
from ftplib import FTP

md = MarketData()
fd = FactorData()
futured = FutureData()

def create_connect():
    s = ddb.session()
    s.connect("168.17.249.172", 8902, 'admin', '123456')
    return s
    
def download_from_ftp(remotepath, localpath):
    ftp_68 = FTP()  # ????
    ftp_68.set_debuglevel(2)  # ??????2???????
    ftp_68.connect("168.8.2.68", 21)  # ???ftp sever???
    ftp_68.login("ftphzh", "ftphzh2602")  # ?????????
    ftp_68.cwd("/016869/dolphin_server/")
    bufsize = 1024                # ???????
    fp = open(localpath, 'wb')     # ???????????
    ftp_68.retrbinary('RETR ' + remotepath, fp.write, bufsize)# ???????????????
    ftp_68.set_debuglevel(0)         # ????
    fp.close()                    # ????

def update_newest_server():
    download_from_ftp("start.sh", "/home/appadmin/start.sh")
    os.system("cd /home/appadmin/server/ && sh start.sh")
    time.sleep(3)
    return


def get_future_tick_from_xquant(security_id, date):
    start_time = date + " 000000000"
    end_time = date + " 235959999"
    df = futured.get_future_data(security_id, start_time, end_time, "TICK")
    df = df[['MDDate', 'MDTime', 'MDStreamID', 'SecurityType', 'SecuritySubType', 'SecurityID', 'SecurityIDSource', 'Symbol', 'MDLevel', 'MDChannel', 'TradingPhaseCode', 'SwitchStatus', 'TradingDate', 'PreOpenInterest', 'PreClosePx', 'PreSettlePrice', 'OpenPx', 'HighPx', 'LowPx', 'LastPx', 'TotalVolumeTrade', 'TotalValueTrade', 'OpenInterest', 'ClosePx', 'SettlePrice', 'MaxPx', 'MinPx', 'PreDelta', 'CurrDelta', 'Buy1Price', 'Buy1OrderQty', 'Buy1NumOrders', 'Buy1NoOrders', 'Buy1OrderDetail', 'Sell1Price', 'Sell1OrderQty', 'Sell1NumOrders', 'Sell1NoOrders', 'Sell1OrderDetail', 'Buy2Price', 'Buy2OrderQty', 'Buy2NumOrders', 'Sell2Price', 'Sell2OrderQty', 'Sell2NumOrders', 'Buy3Price', 'Buy3OrderQty', 'Buy3NumOrders', 'Sell3Price', 'Sell3OrderQty', 'Sell3NumOrders', 'Buy4Price', 'Buy4OrderQty', 'Buy4NumOrders', 'Sell4Price', 'Sell4OrderQty', 'Sell4NumOrders', 'Buy5Price', 'Buy5OrderQty', 'Buy5NumOrders', 'Sell5Price', 'Sell5OrderQty', 'Sell5NumOrders', 'MDRecordType', 'HTSCSecurityID', 'ReceiveDateTime', 'MDValidType', 'ChannelNo']]
    df = df[((df['MDTime']>='093000000') & (df['MDTime']<='113000000'))|((df['MDTime']>='130000000') & (df['MDTime']<='150000000'))]
    return df


def upload_future_data_to_dol(security_id, date):
    s = create_connect()
    dbname = "dfs://MarketData/cf_future_tick"
    tbname = "cf_future_tick"
    df = get_future_tick_from_xquant(security_id, date)
    security_name_list = [security_id]
    #date_list = fd.tradingday(start_date, end_date)
    #mdmonth_list = sorted(set([i[:6] for i in date_list]))
    #for month in mdmonth_list:
    
    #df_list = []
    #security_name_list = list(future_dict.values())
    #for name,security_id in future_dict.items():
    #    df_temp = get_future_tick_from_xquant(security_id, date)
    #    df_temp['HTSCSecurityID'] = name  
    #    df_list.append(df_temp)
    #df = pd.concat(df_list)
          
    if df.shape[0]==0:
        return
    dol_date = date[:4]+"."+date[4:6]+"."+date[6:]
    s.upload({"future_tick":df})
    s.run(f"""
    future_tick.replaceColumn!(`MDDate, temporalParse(future_tick.MDDate, `yyyyMMdd))
    future_tick.replaceColumn!(`MDTime, temporalParse(future_tick.MDTime,"HHmmssSSS"))
    future_tick = select 
                    MDDate as M_MDDate,
                    MDTime as M_MDTime,
                    MDStreamID as M_MDStreamID,
                    SecurityType as M_SecurityType,
                    SecuritySubType as M_SecuritySubType,
                    SecurityID as M_SecurityID,
                    SecurityIDSource as M_SecurityIDSource,
                    Symbol as M_Symbol,
                    MDLevel as M_MDLevel,
                    MDChannel as M_MDChannel,
                    TradingPhaseCode as M_TradingPhaseCode,
                    SwitchStatus as M_SwitchStatus,
                    TradingDate as M_TradingDate,
                    PreOpenInterest as M_PreOpenInterest,
                    PreClosePx as M_PreClosePx,
                    PreSettlePrice as M_PreSettlePrice,
                    OpenPx as M_OpenPx,
                    HighPx as M_HighPx,
                    LowPx as M_LowPx,
                    LastPx as M_LastPx,
                    TotalVolumeTrade as M_TotalVolumeTrade,
                    TotalValueTrade as M_TotalValueTrade,
                    OpenInterest as M_OpenInterest,
                    ClosePx as M_ClosePx,
                    SettlePrice as M_SettlePrice,
                    MaxPx as M_MaxPx,
                    MinPx as M_MinPx,
                    PreDelta as M_PreDelta,
                    CurrDelta as M_CurrDelta,
                    Buy1NoOrders as M_Buy1NoOrders,
                    Buy1OrderDetail as M_Buy1OrderDetail,
                    Sell1NoOrders as M_Sell1NoOrders,
                    Sell1OrderDetail as M_Sell1OrderDetail,
                    fixedLengthArrayVector(Buy1Price,Buy2Price,Buy3Price,Buy4Price,Buy5Price) as M_BuyPrice,
                    fixedLengthArrayVector(Buy1OrderQty,Buy2OrderQty,Buy3OrderQty,Buy4OrderQty,Buy5OrderQty) as M_BuyOrderQty,
                    fixedLengthArrayVector(Sell1Price,Sell2Price,Sell3Price,Sell4Price,Sell5Price) as M_SellPrice,
                    fixedLengthArrayVector(Sell1OrderQty,Sell2OrderQty,Sell3OrderQty,Sell4OrderQty,Sell5OrderQty) as M_SellOrderQty,
                    fixedLengthArrayVector(Buy1NumOrders,Buy2NumOrders,Buy3NumOrders,Buy4NumOrders,Buy5NumOrders) as M_BuyNumOrders,
                    fixedLengthArrayVector(Sell1NumOrders,Sell2NumOrders,Sell3NumOrders,Sell4NumOrders,Sell5NumOrders) as M_SellNumOrders,
                    MDRecordType as M_MDRecordType,
                    HTSCSecurityID as M_HTSCSecurityID,
                    ReceiveDateTime as M_ReceiveDateTime,
                    MDValidType as M_MDValidType,
                    ChannelNo as M_ChannelNo
                from future_tick
    dbName = "{dbname}"
    tbName = `{tbname}
    pt = loadTable(dbName, tbName)
    delete from pt where M_MDDate=={dol_date},M_HTSCSecurityID in {security_name_list}
    sleep(300)
    pt = loadTable(dbName, tbName)
    pt.append!(future_tick)
    
    """)
    print("[CF FUTURE TICK]{} {} finish!!".format(security_id, date))
    
    return

def get_cf_future_listing_date(typer):
    import pandas as pd
    from xquant.futuredata import FutureData
    fd = FutureData()
    instrument_list = [typer+str(i)+str(j).zfill(2)+".CF" for i in range(21,25) for j in range(1,13)]
    df_list = []
    for ins in instrument_list:
        df = fd.get_instrument_info(ins)
        df_list.append(df[['windcode','listdate','delistdate']])
    res = pd.concat(df_list, axis=0)

    return list(res.values)


def main(start_date, end_date, future):
    from xquant.futuredata import FutureData
    fud = FutureData()
#    for security_id, start_date, end_date in get_cf_future_listing_date(future):
#        if security_id.split(".")[0][-4:]<='2403':
#            continue
#        date_list = fd.tradingday(start_date, end_date)
#        cur_date = datetime.datetime.now().strftime("%Y%m%d")
#        real_start_date = date_list[0]
#        real_end_date = date_list[-1]
#        if real_start_date>cur_date:
#            continue
#        elif real_end_date>cur_date:
#            real_end_date = cur_date
#        print(security_id, real_start_date,real_end_date)
#        real_date_list = fd.tradingday(real_start_date, real_end_date)
#        if len(real_date_list)>0:
#            for date in date_list:
#                print(security_id, date)
#                upload_future_data_to_dol(security_id, date)

    date_list = fd.tradingday(start_date, end_date)
    for date in date_list:
        print(f"=================={date}=============")
        security_id = future+"00.CF" 
        print(security_id)
        upload_future_data_to_dol(security_id, date)
    return

if __name__ == "__main__":
    #update_newest_server()
    fd = FactorData()
    start_date = "20240101"
    end_date = "20240312"
    future = "IF"
    main(start_date, end_date,future)

