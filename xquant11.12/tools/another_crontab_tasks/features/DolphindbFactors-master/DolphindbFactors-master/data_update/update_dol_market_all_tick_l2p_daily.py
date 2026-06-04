import json
import pandas as pd
import os
import dolphindb as ddb
import ray
import time
from xquant.factordata import FactorData
import calendar
fa = FactorData()
import os
import os
from ftplib import FTP
from git import Repo


def get_env():
    # 判断运行程序的系统
    if os.environ.get("ENV_VERSION"):
        sysFlag = "xquant"
    elif os.environ.get("DSWMAP_envTag"):
        sysFlag = "tquant"
    elif os.environ.get('BIG_DATA_PREPATH', False) and not os.environ.get('ENV_VERSION', False):
        sysFlag = "big_data"
    else:
        sysFlag = "outside"
        os.environ['outside_env'] = 'uat'

    # 判断系统的运行环境是生产还是测试
    if sysFlag == "xquant":
        envFlag = os.environ.get("ENV_VERSION")
    elif sysFlag == "tquant":
        envFlag = os.environ.get("DSWMAP_envTag")
    elif sysFlag == "outside":
        envFlag = os.environ.get("outside_env")

    if envFlag.lower() == "prd":
        env = "prd"
    elif envFlag.lower() == "uat":
        env = "uat"
    else:
        raise Exception('当前只有prd/uat环境有数据')
    return env

def connect_ddb():
    env = get_env()
    s = ddb.session()
    if env == 'uat':
        s.connect("168.61.13.40", 8848, 'admin', '123456')
    elif env == 'prd':
#        sites = ["168.17.249.171:8902", "168.17.249.172:8902", "168.17.249.173:8902"]
        host,port,userid,password = "localhost",30239,"admin","123456"
        s.connect(host=host, port=port, userid=userid, password=password)
     #        s.connect(host="168.17.249.171", port=8902, userid="admin", password="123456")
    return s



@ray.remote
def calc_tick_persec(security_id, parse_date, interval=1000):
    """
    合并逐笔成交、逐笔委托数据
    :param date: string类型，格式如'20220101'
    :return:
    """
    from xquant.factordata import FactorData
    fd = FactorData()
    from xquant.marketdata import MarketData
    md = MarketData()
    month_trans_data = md.get_data_by_date("Transaction", security_id, parse_date)
    month_order_data = md.get_data_by_date("Order", security_id, parse_date)

    print(security_id, parse_date)
    dol_parse_date = parse_date[:4] + "." + parse_date[4:6] + "." + parse_date[6:]
    s = connect_ddb()
    exchange_house = "XSHG" if security_id.endswith("SH") else "XSHE"
    transaction_data = month_trans_data[month_trans_data['MDDate']==parse_date]
    order_data = month_order_data[month_order_data['MDDate']==parse_date]
    if transaction_data.empty or order_data.empty:
        return

    s.upload({'trade_data': transaction_data})
    s.upload({'order_data': order_data})
    dol_parse_date = parse_date[:4]+"."+parse_date[4:6]+"."+parse_date[6:] 
    merge_script = f'''
        trade_data = select HTSCSecurityID, MDDate, MDTime, 1 as SourceType, TradeType as Type, TradePrice as Price, TradeQty as Qty, 
                            TradeBSFlag as BSFlag, TradeBuyNo as BuyNo, TradeSellNo as SellNo, ApplSeqNum, ChannelNo, 
                            ReceiveDateTime from trade_data    
        if('{exchange_house}'=='XSHG'){{
            order_data = select HTSCSecurityID, MDDate, MDTime, 0 as SourceType, OrderType as Type, OrderPrice as Price, OrderQty as Qty, 
                                OrderBSFlag as BSFlag, OrderNO as BuyNo, OrderNO as SellNo, ApplSeqNum, ChannelNo, 
                                ReceiveDateTime from order_data
            fake_stock = "600000.SH"
        }}
        else{{
            order_data = select HTSCSecurityID, MDDate, MDTime, 0 as SourceType, OrderType as Type, OrderPrice as Price, OrderQty as Qty, OrderBSFlag as BSFlag, OrderIndex as BuyNo, OrderIndex as SellNo, ApplSeqNum, ChannelNo, ReceiveDateTime from order_data
            fake_stock = "000000.SZ"
        }}
        trade_data.replaceColumn!(`MDTime, temporalParse(string(trade_data.MDTime),"HHmmssSSS"))
        order_data.replaceColumn!(`MDTime, temporalParse(string(order_data.MDTime),"HHmmssSSS"))

        trade_data.replaceColumn!(`ReceiveDateTime, temporalParse(string(trade_data.ReceiveDateTime), 'yyyyMMddHHmmssSSS'))
        order_data.replaceColumn!(`ReceiveDateTime, temporalParse(string(order_data.ReceiveDateTime),'yyyyMMddHHmmssSSS'))


        trade_data.replaceColumn!(`MDDate, temporalParse(trade_data.MDDate, `yyyyMMdd))
        order_data.replaceColumn!(`MDDate, temporalParse(order_data.MDDate, `yyyyMMdd))

        trade_data.append!(order_data)

        fake_data = table(09:30:00..11:29:59 join 13:00:00..15:00:00 as MDTime)
        fake_data.replaceColumn!(`MDTime, time(time(fake_data.MDTime)+time("00:00:00.001")))
        fake_data['HTSCSecurityID'] = fake_stock
        fake_data['MDDate'] = {dol_parse_date}
        fake_data['ApplSeqNum'] = 1
        fake_data['ReceiveDateTime'] = now()
        fake_data['ChannelNo'] = trade_data['ChannelNo'][0] 

        fake_data = select HTSCSecurityID as SecurityID, MDDate, MDTime, 1 as SourceType, 0 as Type,
                           0 as Price, 0 as Qty, 0 as BSFlag, 0 as BuyNo, 0 as SellNo, 
                           ApplSeqNum, ChannelNo as ChannelNo, ReceiveDateTime as ReceiveDateTime from fake_data

        trade_data = trade_data.append!(fake_data)
        trade_data = select * from trade_data where MDTime<15:00:00 order by MDTime, ApplSeqNum
        update trade_data set ApplSeqNum = rowNo(ApplSeqNum)+1
        update trade_data set Price = Price*10000
        merge_data = trade_data
        trade_data = NULL
        order_data = NULL
    '''
    s.run(merge_script)
    calc_script = f'''
    suffix = string(1..10)
    day = {dol_parse_date}
    name = `HTSCSecurityID`MDDate`MDTime`SourceType`Type`Price`Qty`BSFlag`BuyNo`SellNo`ApplSeqNum`ChannelNo`ReceiveDateTime
    type = `SYMBOL`DATE`TIME`INT`INT`LONG`LONG`INT`LONG`LONG`LONG`INT`TIMESTAMP
    dummyOrderStream = table(1:0, name, type)

    engineName = 'engine'+temporalFormat(day, `yyyyMMdd)

    colNames = `MDTime`HTSCSecurityID`MDDate`PreClosePx`TotalVolumeTrade`TotalValueTrade`LastPx`OpenPx`HighPx`LowPx`TotalBidQty`TotalOfferQty`WeightedAvgBidPx`WeightedAvgOfferPx join ("BuyPrice" + string(1..10)) join ("BuyOrderQty" + string(1..10)) join ("SellPrice" + string(1..10)) join ("SellOrderQty" + string(1..10)) join ("BuyNumOrders" + string(1..10)) join ("SellNumOrders" + string(1..10)) join `TradingPhaseCode`UpdateTime1`MaxPx`MinPx`BuyQty`SellQty`BuyMoney`SellMoney`UpdateTime2`TradePriceList`TradeQtyList`TradeTypeList`TradeBSFlagList`TradeMDTimeList`TradeBuyNoList`TradeSellNoList
    colTypes =`TIME`SYMBOL`DATE`DOUBLE`LONG`DOUBLE`DOUBLE`DOUBLE`DOUBLE`DOUBLE`LONG`LONG`DOUBLE`DOUBLE join take("DOUBLE", 10) join take("LONG", 10) join take("DOUBLE", 10) join take("LONG", 10) join take("INT", 10) join take("INT", 10) join `INT`TIMESTAMP`DOUBLE`DOUBLE`LONG`LONG`DOUBLE`DOUBLE`NANOTIMESTAMP join ["DOUBLE[]", "DOUBLE[]", "INT[]", "INT[]","TIME[]", "DOUBLE[]", "DOUBLE[]"]
    outTable = table(1000000:0, colNames, colTypes)

    inputColMap_ = dict(`codeColumn`timeColumn`typeColumn`priceColumn`qtyColumn`buyOrderColumn`sellOrderColumn`sideColumn`msgTypeColumn`seqColumn`receiveTime, 
                        `HTSCSecurityID`MDTime`Type`Price`Qty`BuyNo`SellNo`BSFlag`SourceType`ApplSeqNum`ReceiveDateTime)

    prevClose = dict(`688888.SH,[1.5] )  //?????????preClosePrice?????????????OrderBookSnapshotEngine???
    try{{dropStreamEngine(engineName)}} catch(ex){{ print ex }}
    engine = createOrderBookSnapshotEngine(name=engineName, exchange="{exchange_house}", orderbookDepth=10, intervalInMilli = {interval}, date=day, 
                                           startTime=09:30:01.000, prevClose=prevClose, dummyTable=dummyOrderStream, outputTable=outTable, inputColMap=inputColMap_,
                                           includeTradeDetail=true, triggerType="mutual", priceNullFill=0)

    engine.append!(merge_data)
    '''
    s.run(calc_script)

    calc_script = f'''

        if('{exchange_house}'=='XSHG'){{
        dbName_target = "dfs://CustomData/sh_stock_tick_l2p_persec"
        tbName_target = `sh_stock_tick_l2p_persec
}}
        else{{
        dbName_target = "dfs://CustomData/sz_stock_tick_l2p_persec"
        tbName_target = `sz_stock_tick_l2p_persec


}}
        res_data_join = select MDTime as M_MDTime,
                          HTSCSecurityID as M_HTSCSecurityID,
                          MDDate as M_MDDate,
                          PreClosePx as M_PreClosePx,
                          TotalVolumeTrade as M_TotalVolumeTrade, 
                          TotalValueTrade as M_TotalValueTrade,
                          LastPx as M_LastPx,
                          OpenPx as M_OpenPx,
                          HighPx as M_HighPx,
                          LowPx as M_LowPx,
                          TotalBidQty as M_TotalBidQty, 
                          TotalOfferQty as M_TotalOfferQty,
                          WeightedAvgBidPx as M_WeightedAvgBidPx,
                          WeightedAvgOfferPx as M_WeightedAvgOfferPx,
                          TradingPhaseCode as M_TradingPhaseCode,
                          UpdateTime1 as M_UpdateTime1,
                          MaxPx as M_MaxPx,
                          MinPx as M_MinPx,
                          BuyQty as M_BuyQty,
                          SellQty as M_SellQty,
                          BuyMoney as M_BuyMoney,
                          SellMoney as M_SellMoney,
                          UpdateTime2 as M_UpdateTime2,
                          TradePriceList as M_TradePrice,
                          TradeQtyList as M_TradeQty,
                          TradeBSFlagList as M_TradeBSFlag,
                          TradeMDTimeList as M_TradeMDTime,
                          TradeBuyNoList as M_TradeBuyNo,
                          TradeSellNoList as M_TradeSellNo,
                          fixedLengthArrayVector(BuyPrice1,BuyPrice2,BuyPrice3,BuyPrice4,BuyPrice5,BuyPrice6,BuyPrice7,BuyPrice8,BuyPrice9,BuyPrice10) as M_BuyPrice,
                          fixedLengthArrayVector(BuyOrderQty1,BuyOrderQty2,BuyOrderQty3,BuyOrderQty4,BuyOrderQty5,BuyOrderQty6,BuyOrderQty7,BuyOrderQty8,BuyOrderQty9,BuyOrderQty10) as M_BuyOrderQty,
                          fixedLengthArrayVector(SellPrice1,SellPrice2,SellPrice3,SellPrice4,SellPrice5,SellPrice6,SellPrice7,SellPrice8,SellPrice9,SellPrice10) as M_SellPrice,
                          fixedLengthArrayVector(SellOrderQty1,SellOrderQty2,SellOrderQty3,SellOrderQty4,SellOrderQty5,SellOrderQty6,SellOrderQty7,SellOrderQty8,SellOrderQty9,SellOrderQty10) as M_SellOrderQty,
                          fixedLengthArrayVector(BuyNumOrders1,BuyNumOrders2,BuyNumOrders3,BuyNumOrders4,BuyNumOrders5,BuyNumOrders6,BuyNumOrders7,BuyNumOrders8,BuyNumOrders9,BuyNumOrders10) as M_BuyNumOrders,
                          fixedLengthArrayVector(SellNumOrders1,SellNumOrders2,SellNumOrders3,SellNumOrders4,SellNumOrders5,SellNumOrders6,SellNumOrders7,SellNumOrders8,SellNumOrders9,SellNumOrders10) as M_SellNumOrders

                from outTable
                where HTSCSecurityID == '{security_id}'
                res_data_join = select * from res_data_join where M_MDTime in 09:30:01.000..11:30:00.000 or M_MDTime in 13:00:01.000..14:57:00.000
    '''
    s.run(calc_script)

    save_script = f"""

        if('{exchange_house}'=='XSHG'){{
        dbName_target = "dfs://CustomData/sh_stock_tick_l2p_persec"
        tbName_target = `sh_stock_tick_l2p_persec
        }}
        else{{
        dbName_target = "dfs://CustomData/sz_stock_tick_l2p_persec"
        tbName_target = `sz_stock_tick_l2p_persec
        }}

        remote_conn = xdb("168.17.249.172",8902,"admin","123456")
        def save_data_to_dfs(res_data,symbol,dol_parse_date,dbName_target,tbName_target){{
            // 删除本次新增数据
            cnt = select count(*) from loadTable(dbName_target, tbName_target) where M_HTSCSecurityID==symbol and M_MDDate==dol_parse_date
            if(cnt[0,0]>0){{
                print "delete data"            
                delete from loadTable(dbName_target, tbName_target) where M_HTSCSecurityID==symbol and M_MDDate==dol_parse_date
                }}
            //写入新增数据
            loadTable(dbName_target, tbName_target).append!(res_data)
        }}
        remoteRun(remote_conn,save_data_to_dfs,res_data_join,'{security_id}',{dol_parse_date},dbName_target,tbName_target)
        // drop engine
        dropStreamEngine(engineName)

    """
    s.run(save_script)
    return

def calc_tick_persec_his_date(dt_list, securities_list, num_cpus):
    fd = FactorData()
    finish = []
    if not ray.is_initialized():
        ray.init(num_cpus=num_cpus,_system_config={"object_spilling_config": json.dumps( {"type": "filesystem", "params": {"directory_path": "/data/user/999999"}})})
    for security_id in securities_list:
        start_time = time.time()

        #ray.init(num_cpus=num_cpus)

        ray.get([calc_tick_persec.remote(security_id=security_id, parse_date=parse_date)
                  for parse_date in dt_list])
        #ray.shutdown()
        finish.append(security_id)
        print("[Tick L2P] ============= cur security_id cost: {} ================".format(time.time()-start_time))
        time.sleep(3)
        print(finish, len(finish))
    #ray.shutdown()
    return

def get_stock_list():
    s = ddb.session()
    s.connect("168.17.249.172",8902,"admin","123456")
    dbname = "dfs://PublicData/platformdata/EnhancedTickL2P"
    tbname = "online_factor_data"
    stocks = s.run(f"""
    dbname = "{dbname}"
    tbname = `{tbname}
    stocks = exec distinct(M_HTSCSecurityID) from loadTable(dbname, tbname)
    stocks
    """)
    return stocks

if __name__ == "__main__":
    stocks_list = []
    from xquant.factordata import FactorData
    fd = FactorData()
    dt_list = fd.tradingday("20220101","20240222")
    num_cpus = 20
    import sys
    securities_list = [sys.argv[1]]
    calc_tick_persec_his_date(dt_list, securities_list, num_cpus)
