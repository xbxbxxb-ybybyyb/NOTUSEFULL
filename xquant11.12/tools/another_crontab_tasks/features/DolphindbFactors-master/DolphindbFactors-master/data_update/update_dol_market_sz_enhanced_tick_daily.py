import dolphindb as ddb
import ray
import uuid
import pandas as pd
import re
import os
import pyarrow as pa
import calendar
from xquant.funddata import FundData
from xquant.marketdata import MarketData
from xquant.factordata import FactorData
import datetime
import sys
import settings
from ftplib import FTP

md = MarketData()
fd = FactorData()
os.environ['JAVA_HOME'] = "/usr/java/latest/"
os.environ['JAVA_TOOL_OPTIONS'] = '-Xss1280K'
os.environ['ARROW_LIBHDFS_DIR'] = "/opt/cloudera/parcels/CDH/lib/impala/lib/"
os.environ['HADOOP_HOME'] = "/opt/cloudera/parcels/CDH/lib/hadoop"
os.environ['HADOOP_CONF_DIR'] = "/opt/cloudera/parcels/CDH/lib/hadoop/etc/hadoop"
os.environ['YARN_CONF_DIR'] = "/opt/cloudera/parcels/CDH/lib/hadoop/etc/hadoop"
basedir = os.path.abspath(os.path.join(os.path.abspath(__file__), '../..'))
sys.path.append(basedir)

def create_connect():
    s = ddb.session()
    s.connect("localhost", 8848, 'admin', '123456')
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
    os.system("cd /home/appadmin/ && sh start.sh")
    time.sleep(3)
    return

def get_stock_list():
    s = ddb.session()
    s.connect("168.17.250.49", 8902, 'admin', '123456')
    dbname="dfs://CustomData/sz_stock_tick_enhanced"
    tbname = "sz_stock_tick_enhanced"
    stocks = s.run(f"""
    dbname = '{dbname}'
    tbname = `{tbname}
    stocks = exec distinct(M_HTSCSecurityID) from loadTable(dbname, tbname)
    stocks
    """)
    stocks = list(stocks)
    return stocks


 
def upload_tick3s_data(s, data,cover=False):
    #df = pd.read_parquet(path)
    #dfs = pa.hdfs.connect()
    #df = dfs.read_parquet(path).to_pandas()
    df = data
    # 从hadoop下载的数据有这3个字段，用xquant接口取出来的数据没有下面3个字段，先补0
    df['ChannelNo'] = df['ChannelNo'].fillna(0).astype(int)
    print('read parquet ok')
 
    df['ChannelNo'] = df['ChannelNo'].fillna(0).astype(int)
    s.upload({'tick_df':df})
    print('tick upload ok')
 
 
def upload_transaction(s, data, cover=False):
    #df = pd.read_parquet(path)
    #dfs = pa.hdfs.connect()
    #df = dfs.read_parquet(path).to_pandas()
    df = data
#    df['ChannelNo'] = 0
#    df['ApplSeqNum'] = 0
 
    need_cols = ['HTSCSecurityID', 'MDDate', 'MDTime', 'TradeIndex', 'TradeType', 'TradePrice', 'TradeQty', 'TradeBSFlag', 'TradeBuyNo', 'TradeSellNo', 'ApplSeqNum', 'ChannelNo', 'ReceiveDateTime', 'TradeMoney']
    df = df[need_cols]
    df['ChannelNo'] = df['ChannelNo'].fillna(0).astype(int)
    s.upload({'transaction_df':df})


 
def main(start_date, end_date, stock, security_type='stock'):
    s = create_connect() 
    dol_start_date = start_date[:4]+ "."+start_date[4:6]+"."+start_date[6:]
    dol_end_date = end_date[:4] + "." + end_date[4:6] + "."+end_date[6:]   
    s.run("""
        def dropAllEngines(){
            if(getStreamEngineStat().rows() > 0){
                engineTypes = getStreamEngineStat().keys()
                for(engineType in engineTypes){
                        engineNames = getStreamEngineStat()[engineType].name
                        for(name in engineNames){
                                print("Drop Stream Engine: " + name)
                                try{
                                        dropStreamEngine(name)
                                }
                                catch(ex){
                                        print(ex)
                                }
                        }
                }
        }
        print("All engines have been dropped !")
        }
        //dropAllEngines()
        """)
 
    date_list = fd.tradingday(start_date, end_date)
    year_month=start_date[:6]
    if security_type == 'stock':
        os.system(
         f"hdfs dfs -get /htdata/mdc/MDCProvider/XSHE_Stock_Snapshot_Level2_Month/month={year_month}/XSHE_Stock_Snapshot_Level2_{stock}_{year_month}.parquet".format(stock=stock,year_month=year_month))
        try:
            tick_data = pd.read_parquet(f"XSHE_Stock_Snapshot_Level2_{stock}_{year_month}.parquet".format(stock=stock,year_month=year_month))
        except:
            tick_data = pd.DataFrame()
        os.system(f"rm -rf XSHE_Stock_Snapshot_Level2_{stock}_{year_month}.parquet".format(stock=stock,year_month=year_month))
    else:
        os.system(
         f"hdfs dfs -get /htdata/mdc/MDCProvider/XSHE_Fund_Snapshot_Level2_Month/month={year_month}/XSHE_Fund_Snapshot_Level2_{stock}_{year_month}.parquet".format(stock=stock,year_month=year_month))
        try:
            tick_data = pd.read_parquet(f"XSHE_Fund_Snapshot_Level2_{stock}_{year_month}.parquet".format(stock=stock,year_month=year_month))
            tick_data_columns = tick_data.columns.to_list()
            tick_data['AfterHoursTotalVolumeTrade']=0
            tick_data['AfterHoursTotalValueTrade']=0
            tick_data['AfterHoursNumTrades']=0
            tick_data = tick_data[['MDDate', 'MDTime', 'SecurityType', 'SecuritySubType', 'SecurityID', 'SecurityIDSource', 'Symbol', 'TradingPhaseCode', 'PreClosePx', 'NumTrades', 'TotalVolumeTrade', 'TotalValueTrade', 'LastPx', 'OpenPx', 'ClosePx', 'HighPx', 'LowPx', 'DiffPx1', 'DiffPx2', 'MaxPx', 'MinPx', 'TotalBidQty', 'TotalOfferQty', 'WeightedAvgBidPx', 'WeightedAvgOfferPx', 'AfterHoursNumTrades', 'AfterHoursTotalVolumeTrade', 'AfterHoursTotalValueTrade', 'Buy1Price', 'Buy1OrderQty', 'Buy1NumOrders', 'Buy1NoOrders', 'Buy1OrderDetail', 'Sell1Price', 'Sell1OrderQty', 'Sell1NumOrders', 'Sell1NoOrders', 'Sell1OrderDetail', 'Buy2Price', 'Buy2OrderQty', 'Buy2NumOrders', 'Sell2Price', 'Sell2OrderQty', 'Sell2NumOrders', 'Buy3Price', 'Buy3OrderQty', 'Buy3NumOrders', 'Sell3Price', 'Sell3OrderQty', 'Sell3NumOrders', 'Buy4Price', 'Buy4OrderQty', 'Buy4NumOrders', 'Sell4Price', 'Sell4OrderQty', 'Sell4NumOrders', 'Buy5Price', 'Buy5OrderQty', 'Buy5NumOrders', 'Sell5Price', 'Sell5OrderQty', 'Sell5NumOrders', 'Buy6Price', 'Buy6OrderQty', 'Buy6NumOrders', 'Sell6Price', 'Sell6OrderQty', 'Sell6NumOrders', 'Buy7Price', 'Buy7OrderQty', 'Buy7NumOrders', 'Sell7Price', 'Sell7OrderQty', 'Sell7NumOrders', 'Buy8Price', 'Buy8OrderQty', 'Buy8NumOrders', 'Sell8Price', 'Sell8OrderQty', 'Sell8NumOrders', 'Buy9Price', 'Buy9OrderQty', 'Buy9NumOrders', 'Sell9Price', 'Sell9OrderQty', 'Sell9NumOrders', 'Buy10Price', 'Buy10OrderQty', 'Buy10NumOrders', 'Sell10Price', 'Sell10OrderQty', 'Sell10NumOrders', 'HTSCSecurityID', 'ReceiveDateTime', 'ChannelNo']]
        except:
            tick_data = pd.DataFrame()
        os.system(f"rm -rf XSHE_Fund_Snapshot_Level2_{stock}_{year_month}.parquet".format(stock=stock,year_month=year_month))

    if tick_data.empty:
        return
    tick_data = tick_data[tick_data['MDDate'].isin(date_list)]
    if security_type == 'stock':
        transaction_data = md.get_data_by_date("Transaction",stock,start_date)
    else:
        fnd = FundData()
        transaction_data = fnd.get_fund_data(stock,start_date+" 093000000",start_date+" 150000000","TRANSACTION") 
    transaction_data = transaction_data[transaction_data['MDDate'].isin(date_list)]
    if not tick_data.empty and not transaction_data.empty:
        upload_tick3s_data(s=s, data=tick_data, cover=True)
#             上传逐笔成交
        upload_transaction(s=s, data=transaction_data, cover=True)
            # 上传逐笔委托
    else:
        return
    script_repair = """
    //修正60整秒时间
    //参数t是double类型的时间，如20221226101560000，输出是timestamp类型，如2022.12.26T10:16:00.000
    def OneInSixty(t){
        stringT = t$long$string
        if (stringT.strlen()==0) return NULL
        if (stringT[12:14]=="60") {
            stringT = stringT[0:12] + "00" + stringT[14:17]
            OneInSixtyTime = temporalAdd(temporalParse(stringT, `yyyyMMddHHmmssSSS),1,'m')
            }
        else OneInSixtyTime = temporalParse(stringT, `yyyyMMddHHmmssSSS)
        return OneInSixtyTime
    }
    """
    s.run(script_repair)
    s.run(f"""
        tick_df
        transaction_df
        stock= `{stock}
        date_list = {dol_start_date}..{dol_end_date} 
        cover=true
        exchangeHouse='sz'
        if (exchangeHouse == 'sh'){{
        dbName = 'dfs://CustomData/sh_stock_tick_enhanced'
        tbName =  `sh_stock_tick_enhanced
        }}
    else if (exchangeHouse == 'sz'){{
        dbName = 'dfs://CustomData/sz_stock_tick_enhanced'
        tbName =  `sz_stock_tick_enhanced
        }}
        def create_connection(){{
            remote_conn=xdb('168.17.250.48', 8902, 'admin', '123456')
            return remote_conn
        }}
        
        def check(dbName, tbName, stock, date, cover){{
            cnt = exec count(*) from loadTable(dbName, tbName) where M_HTSCSecurityID in stock, M_MDDate=date
            if (cnt >0){{
                if (!cover)  throw "已存在融合数据，若要覆盖，设置cover=true"
                else delete from loadTable(dbName, tbName) where M_HTSCSecurityID in stock, M_MDDate=date
                }}
            }}
        def check_remote(dbName, tbName, stock, date, cover){{
            remote_connect = create_connection()
            remoteRun(remote_connect, check, dbName, tbName, stock, date, cover)
            }}

        def append_local(dbName, tbName, result){{
            pt = loadTable(dbName, tbName)
            pt.append!(result)
            }}

        def append_remote(dbName, tbName, result){{
            remote_connect = create_connection()
            remoteRun(remote_connect, append_local, dbName, tbName, result)
            }}
            
        tick_df.replaceColumn!(`MDDate, temporalParse(tick_df.MDDate, `yyyyMMdd))
        tick_df.replaceColumn!(`MDTime, temporalParse(string(tick_df.MDTime),"HHmmssSSS"))
          
        transaction_df.replaceColumn!(`MDDate, temporalParse(transaction_df.MDDate, `yyyyMMdd))
        transaction_df.replaceColumn!(`MDTime, temporalParse(string(transaction_df.MDTime),"HHmmssSSS"))
        transaction_df.replaceColumn!(`ApplSeqNum, long(transaction_df.ApplSeqNum))
        transaction_df.replaceColumn!(`ChannelNo, long(transaction_df.ChannelNo))
        for(date in date_list){{
            try{{
            //校验库中是否已有当天数据
            //加载调整tick
            tickData = select * from tick_df where MDDate==date
            tradeData = select * from transaction_df where MDDate == date
            if (tickData.size()==0 or tradeData.size()==0){{continue}}
            tickData = select * from tickData where MDTime between 09:30:00.000 : 11:30:00.000 or MDTime between 13:00:00.000 : 14:57:00.000 order by ReceiveDateTime
            tickData.replaceColumn!(`ReceiveDateTime, each(OneInSixty, tickData.ReceiveDateTime))
            tickData.replaceColumn!(`TotalValueTrade, floor(tickData.TotalValueTrade))
            tickData.replaceColumn!(`HTSCSecurityID, symbol(tickData.HTSCSecurityID))
            //加载调整trade
            tradeData = select * from tradeData where MDTime between 09:30:00.000 : 11:30:00.000 or MDTime between 13:00:00.000 : 15:00:00.000 order by ReceiveDateTime,TradeIndex
            tradeData.replaceColumn!(`ReceiveDateTime, each(OneInSixty, tradeData.ReceiveDateTime))
            tradeData.replaceColumn!(`HTSCSecurityID, symbol(tradeData.HTSCSecurityID))
            tmpData = select * from tradeData context by HTSCSecurityID limit -1
            tmpData.replaceColumn!(`ReceiveDateTime, take(concatDateTime(date, 15:01:00.000), tmpData.size()))
            tradeData.append!(tmpData)
            sch_trade = tradeData.schema().colDefs
            update sch_trade set name = `TradeMDTime where name = `MDTime
            tradeData.rename!(sch_trade.name)
            //windowJoin引擎参数
            sch_tickData = tickData.schema().colDefs
            delete from sch_tickData where name in `ReceiveDateTime`MDDate`HTSCSecurityID`ChannelNo
            needTradeColumns = `TradeIndex`TradeBuyNo`TradeSellNo`TradeType`TradeBSFlag`TradePrice`TradeQty`TradeMoney`ApplSeqNum`TradeMDTime
            sch_tradeData = select * from tradeData.schema().colDefs where name in needTradeColumns
            newType = []
            for (x in sch_tradeData.typeString) newType.append!(x+'[]')
            sch_tradeData.replaceColumn!(`typeString, string(newType))
            sch_tickTrade = sch_tickData.append!(sch_tradeData)
            metrics = sqlCol(sch_tickTrade.name) join
            sqlColAlias(<sum(iif(TradeBSFlag == 1 && TradeType==0, TradeQty, 0))>, `BuyQty) join
            sqlColAlias(<sum(iif(TradeBSFlag == 1 && TradeType==0, TradePrice*TradeQty, 0))>, `BuyMoney) join
            sqlColAlias(<count(iif(TradeBSFlag != 1 or TradeType != 0, NULL, TradeType))>, `BuyCount) join
            sqlColAlias(<sum(iif(TradeBSFlag == 2 && TradeType==0, TradeQty, 0))>, `SellQty) join
            sqlColAlias(<sum(iif(TradeBSFlag == 2 && TradeType==0, TradePrice*TradeQty, 0))>, `SellMoney) join
            sqlColAlias(<count(iif(TradeBSFlag != 2 or TradeType != 0, NULL, TradeType))>, `SellCount)

            if (exchangeHouse=='sh'){{
                nullFill = (2022.10.28T09:30:00.146,2022.10.28,`688599.SH,09:30:00.000,0,'','',0,'','',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'',0,0,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,[[]],[[]],[[]],[[]],[[]],[[]],[[]],[[]],[[]],[[]],0,0,0,0,0,0)
                }}
            else if (exchangeHouse=='sz'){{
                nullFill = (2022.10.28T09:30:00.146,2022.10.28,`688599.SH,09:30:00.000,0,'','',0,'','',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'',0,0,0,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,[[]],[[]],[[]],[[]],[[]],[[]],[[]],[[]],[[]],[[]],0,0,0,0,0,0)
            }}
            tickTradeTable = table(1:0, `ReceiveDateTime`MDDate`HTSCSecurityID join sch_tickTrade.name join `BuyQty`BuyMoney`BuyCount`SellQty`SellMoney`SellCount, ['TIMESTAMP','DATE','SYMBOL'] join sch_tickTrade.typeString join ['DOUBLE','DOUBLE','INT','DOUBLE','DOUBLE','INT'])
            engineName = "stockEnhanceTick_" + temporalFormat(date, `yyyyMMdd) + '_' + temporalFormat(now(), `yyyyMMddHHmmssSSS)
            //创建windowJoin引擎、注入数据
            try{{dropStreamEngine(engineName)}} catch(ex){{ print ex }}
            wjEngine=createWindowJoinEngine(name=engineName, leftTable=tickData, rightTable=tradeData, outputTable=tickTradeTable,  window=0:0, metrics=metrics, matchingColumn=`MDDate`HTSCSecurityID, timeColumn=`ReceiveDateTime, useSystemTime=false, nullFill=nullFill)
            appendForJoin(getStreamEngine(engineName), true, tickData)
            appendForJoin(getStreamEngine(engineName), false, tradeData)
            timer{{
            //判断引擎算完
            tCheck = now()
            do{{
                if(tickTradeTable.size() >= tickData.size()) break
                print('预期数据量：' + string(tickData.size()) + '，当前数据量：' + string(tickTradeTable.size()))
                sleep(5000)
                if (now() > tCheck + 30*1000) throw "计算耗时超30s"
                }}
            while(true)
            }}
            //tick十合一
            needTickTradeColumns = tickTradeTable.schema().colDefs
            delete from needTickTradeColumns where name like "Buy%Price" or name like "Buy%OrderQty" or name like "Buy%NumOrders" or name like "Sell%Price" or name like "Sell%OrderQty" or name like "Sell%NumOrders"
            needTickTradeColumns = sqlCol(needTickTradeColumns.name) join
            sqlColAlias(<fixedLengthArrayVector(Buy1Price,Buy2Price,Buy3Price,Buy4Price,Buy5Price,Buy6Price,Buy7Price,Buy8Price,Buy9Price,Buy10Price)>, `BuyPrice) join
            sqlColAlias(<fixedLengthArrayVector(Buy1OrderQty,Buy2OrderQty,Buy3OrderQty,Buy4OrderQty,Buy5OrderQty,Buy6OrderQty,Buy7OrderQty,Buy8OrderQty,Buy9OrderQty,Buy10OrderQty)>, `BuyOrderQty) join
            sqlColAlias(<fixedLengthArrayVector(Buy1NumOrders,Buy2NumOrders,Buy3NumOrders,Buy4NumOrders,Buy5NumOrders,Buy6NumOrders,Buy7NumOrders,Buy8NumOrders,Buy9NumOrders,Buy10NumOrders)>, `BuyNumOrders) join
            sqlColAlias(<fixedLengthArrayVector(Sell1Price,Sell2Price,Sell3Price,Sell4Price,Sell5Price,Sell6Price,Sell7Price,Sell8Price,Sell9Price,Sell10Price)>, `SellPrice) join
            sqlColAlias(<fixedLengthArrayVector(Sell1OrderQty,Sell2OrderQty,Sell3OrderQty,Sell4OrderQty,Sell5OrderQty,Sell6OrderQty,Sell7OrderQty,Sell8OrderQty,Sell9OrderQty,Sell10OrderQty)>, `SellOrderQty) join
            sqlColAlias(<fixedLengthArrayVector(Sell1NumOrders,Sell2NumOrders,Sell3NumOrders,Sell4NumOrders,Sell5NumOrders,Sell6NumOrders,Sell7NumOrders,Sell8NumOrders,Sell9NumOrders,Sell10NumOrders)>, `SellNumOrders)
            needTickTradeColumns_right = sqlCol(['ReceiveDateTime','MDDate','HTSCSecurityID','MDTime','SecurityType','SecuritySubType','SecurityID','SecurityIDSource','Symbol','TradingPhaseCode','PreClosePx','NumTrades','TotalVolumeTrade','TotalValueTrade','LastPx','OpenPx','ClosePx','HighPx','LowPx','DiffPx1','DiffPx2','MaxPx','MinPx','TotalBidQty','TotalOfferQty','WeightedAvgBidPx','WeightedAvgOfferPx','AfterHoursNumTrades','AfterHoursTotalVolumeTrade','AfterHoursTotalValueTrade','Buy1NoOrders','Buy1OrderDetail','Sell1NoOrders','Sell1OrderDetail','TradeMDTime','TradeIndex','TradeBuyNo','TradeSellNo','TradeType','TradeBSFlag','TradePrice','TradeQty','TradeMoney','ApplSeqNum','BuyQty','BuyMoney','BuyCount','SellQty','SellMoney','SellCount','BuyPrice','BuyOrderQty','BuyNumOrders','SellPrice','SellOrderQty','SellNumOrders'])
            result = sql(select=needTickTradeColumns, from=tickTradeTable, groupBy=<HTSCSecurityID>, groupFlag=0, csort=<ReceiveDateTime>).eval()
            result = sql(select=needTickTradeColumns_right, from=result).eval()
            check_remote(dbName, tbName, stock, date, cover=true)
            append_remote(dbName, tbName, result)
            try{{dropStreamEngine(engineName)}} catch(ex){{ print ex }}
            }}catch(ex){{ print ex }}      
        }}
        """)
    return
 
if __name__ == '__main__':
    import time
    #update_newest_server()
    #cur_date = datetime.datetime.now().strftime("%Y%m%d")
    #parse_date = fd.tradingday(cur_date,-1)[0]
    #parse_date = '20240125'
    #start_date, end_date = parse_date, parse_date 
    #stock_list = get_stock_list()
    #stock_list = [i for i in stock_list if i.endswith(".SZ")]
    stock_list = []
    print(len(stock_list))
    #start_month = start_date[:6]
    #end_month = end_date[:6]
    #all_months = [str(i)+str(j).zfill(2) for i in range(2010,2030) for j in range(1,13)]
    #need_calc_months = all_months[all_months.index(start_month):all_months.index(end_month)+1]
    #start = time.time()   
    #for stock in stock_list:
        #need_calc_months = all_months[all_months.index(start_month):all_months.index(end_month)+1]
        #for month in need_calc_months:
        #    start_date = month+"01"
        #    end_date = month+str(calendar.monthrange(int(month[:4]), int(month[4:]))[1])
    #    main(start_date, end_date, stock)

#    lm.sendMessage('016869','【科创板做市】{}-{}增强tick更新完成'.format(start_date, end_date))
#    print('016869','【科创板做市】增强tick更新完成')
    #print(time.time()-start)
    start_date = "20210101"
    end_date = "20240219"
    tradingday = fd.tradingday(start_date, end_date)
    for date in tradingday:
        main(start_date=date, end_date=date, stock='180401.SZ', security_type='fund') 
                                                                                        

