import dolphindb as ddb
import uuid
import pandas as pd
import re
import os
import time
import json
from collections import defaultdict
from utils.setenv import get_env
from AutoMiningFrame.configs.local_connect import parse_connect

env = get_env()

if env == 'prd':
    from xquant.factordata import FactorData


def calc_factors_date(config_path, file_path, start_date, end_date, target_securities, return_mode):
    s = ddb.session()
    host, port, userid, password = parse_connect()
    s.connect(host=host, port=port, userid=userid, password=password)
    u = uuid.uuid1()
    u = 'u' + str(u).replace('-', '')
    # TODO: check date
    start_date = start_date[:4] + "." + start_date[4:6] + "." + start_date[6:]
    end_date = end_date[:4] + "." + end_date[4:6] + "." + end_date[6:]

    factors_and_args_list = []
    resFactorList = []
    custom_factor_dict = defaultdict(list)
    config_path = os.path.join(config_path, 'factor_config.json')
    factor_config = json.load(open(config_path))
    factor_list = [i for i in factor_config]
    for factor_name in factor_list:
        # 加载配置文件参数
        custom_params = factor_config[factor_name]
        # 因子文件路径
        total_path = os.path.join(file_path, factor_name) + ".dos"
        total_path = total_path.replace('\\', '\\\\')
        total_path = os.path.join("/app/nsw_test",total_path)
        # 获取因子的计算逻辑
        s.run("file_parse = file('{}')".format(total_path))
        temp = s.run("file_parse.readLines()")
        script_factor = "\n".join(i for i in temp)
        script_factor = re.search(r'@.*', script_factor, re.DOTALL).group()
        script_factor_cus = script_factor
        for custom_param_dict in custom_params:
            pattern = re.compile(r"[(](.*?)[)][{]", re.S)
            res = re.findall(pattern, script_factor)[0]
            res_copy = res
            for k, v in custom_param_dict.items():
                # if k not in res:
                #    raise Exception("自定义参数没有: {}".format(k))
                target_param = [i for i in res.split(",") if k in i][0]
                res = res.replace(target_param, " "+ k + "=" + str(v))
            script_factor_cus = script_factor.replace(res_copy, res)
            script_factor_cus = script_factor_cus.replace(factor_name, factor_name+"_"+"_".join([k+str(v) for k, v in custom_param_dict.items()]))
            custom_factor_dict[factor_name].append(script_factor_cus)

    for factor_name, script_factor_list in custom_factor_dict.items():
        for script_factor in script_factor_list:
            # 提取因子名和参数
            sear = re.search(r'def (.*?){.*?return (.*?)}', script_factor, re.DOTALL)
            factors_and_args_list.append(sear.group(1))
            # 提取结果因子名
            resFactor = sear.group(2)
            resFactor = re.sub(r'\s', '', resFactor).split(',')
            for res in resFactor:
                if not res.startswith(factor_name):
                    raise Exception(
                        'return因子名需以函数名为前缀，如{res} --> {factor_name}_{res}'.format(factor_name=factor_name, res=res))
            resFactorList.append(resFactor)
            try:
                s.run(script_factor)
            except Exception as e:
                raise Exception('自定义因子语法有误：{}'.format(e))
            print('{} - parse factor ok'.format(factor_name))
    # factors_and_args = factors_and_args[:-1]
    # factors_and_args = factors_and_args.replace('mutable', '')
    factors_and_args = ",".join(i.replace('mutable', '') for i in factors_and_args_list)
    start = time.time()
    if return_mode == 'show':
        tempList = []
        for i in resFactorList:
            tempList += i
        script_defineStreamTable = """
            use  DolphinFrame::PythonFactorCalcStream_3s
            //tick流表
            names = `MDDate`MDTime`SecurityType`SecuritySubType`SecurityID`SecurityIDSource`Symbol`TradingPhaseCode`PreClosePx`NumTrades`TotalVolumeTrade`TotalValueTrade`LastPx`OpenPx`ClosePx`HighPx`LowPx`DiffPx1`DiffPx2`MaxPx`MinPx`TotalBidQty`TotalOfferQty`WeightedAvgBidPx`WeightedAvgOfferPx`AfterHoursNumTrades`AfterHoursTotalVolumeTrade`AfterHoursTotalValueTrade`Buy1Price`Buy1OrderQty`Buy1NumOrders`Buy1NoOrders`Buy1OrderDetail`Sell1Price`Sell1OrderQty`Sell1NumOrders`Sell1NoOrders`Sell1OrderDetail`Buy2Price`Buy2OrderQty`Buy2NumOrders`Sell2Price`Sell2OrderQty`Sell2NumOrders`Buy3Price`Buy3OrderQty`Buy3NumOrders`Sell3Price`Sell3OrderQty`Sell3NumOrders`Buy4Price`Buy4OrderQty`Buy4NumOrders`Sell4Price`Sell4OrderQty`Sell4NumOrders`Buy5Price`Buy5OrderQty`Buy5NumOrders`Sell5Price`Sell5OrderQty`Sell5NumOrders`Buy6Price`Buy6OrderQty`Buy6NumOrders`Sell6Price`Sell6OrderQty`Sell6NumOrders`Buy7Price`Buy7OrderQty`Buy7NumOrders`Sell7Price`Sell7OrderQty`Sell7NumOrders`Buy8Price`Buy8OrderQty`Buy8NumOrders`Sell8Price`Sell8OrderQty`Sell8NumOrders`Buy9Price`Buy9OrderQty`Buy9NumOrders`Sell9Price`Sell9OrderQty`Sell9NumOrders`Buy10Price`Buy10OrderQty`Buy10NumOrders`Sell10Price`Sell10OrderQty`Sell10NumOrders`HTSCSecurityID`ReceiveDateTime`ChannelNo
             types = ['DATE','TIME','INT','STRING','STRING','INT','STRING','STRING','DOUBLE','LONG','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','STRING','DOUBLE','DOUBLE','DOUBLE','DOUBLE','STRING','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','DOUBLE','STRING','LONG','LONG']
            Sch_tick_data = table(names as name, types as typeString)
            share streamTable(1:0, Sch_tick_data.name, Sch_tick_data.typeString) as StockStream{u}

            //trade流表---分区
            try{{ undef(`orderTradeStream, SHARED) }} catch(ex){{ print(ex) }}
            dbTime = database(, RANGE, 00:00:00.000 + 0..(24*60*60/30-1)*30000)         //30s
            colNames = `HTSCSecurityID`MDDate`MDTime`TradeIndex`TradeType`TradePrice`TradeQty`TradeBSFlag`TradeBuyNo`TradeSellNo`ApplSeqNum`ChannelNo`ReceiveDateTime`TradeMoney
            colTypes = [STRING, DATE, TIME, LONG, LONG, DOUBLE, DOUBLE, LONG, LONG, LONG, LONG, LONG, LONG, DOUBLE]
            orderTradeTemp_Sch = table(1:0, colNames, colTypes)
            orderTradeTemp = dbTime.createPartitionedTable(orderTradeTemp_Sch, `orderTradeTemp, `MDTime)
            share orderTradeTemp as orderTradeStream{u}

            //生成带有LastTime的tick表结构
            Sch_tickGetLastTime = table(`LastTime as name, `TIME as typeString)
            Sch_tickGetLastTime.append!(Sch_tick_data)
            delete from Sch_tickGetLastTime where name like "Buy%Price" or name like "Buy%OrderQty" or name like "Buy%NumOrders" or name like "Sell%Price" or name like "Sell%OrderQty" or name like "Sell%NumOrders" or name=`HTSCSecurityID
            insert into Sch_tickGetLastTime  values(`BuyPrice`BuyOrderQty`BuyNumOrders`SellPrice`SellOrderQty`SellNumOrders, take("DOUBLE[]", 6))

            //响应式状态引擎获取LastTime，新tick表名为tickGetLastTime
            share streamTable(1:0, `HTSCSecurityID join Sch_tickGetLastTime.name join `TS_StockStream, [`SYMBOL] join Sch_tickGetLastTime.typeString join ['TIMESTAMP']) as tickGetLastTime{u}

            //因子结果表
            share streamTable(100:0, `HTSCSecurityID`timestamp join {factorsReturn} join `TS_StockStream`TS_tickGetLastTime_ahead`TS_tickGetLastTime_middle`TS_tickGetLastTime_behind`ReceiveDateTime, [SYMBOL, TIMESTAMP] join take(DOUBLE, {factorsReturn}.size()) join [TIMESTAMP, TIMESTAMP, TIMESTAMP, TIMESTAMP, TIMESTAMP]) as rseEngineOutput{u}

            //过渡表 -> 解决向引擎并发写数导致服务奔溃
            names = tickGetLastTime{u}.schema().colDefs.name join `TS_tickGetLastTime_ahead`TS_tickGetLastTime_middle`BuyQty`BuyMoney`BuyCount`SellQty`SellMoney`SellCount  join `TS_tickGetLastTime_behind
            M_names = array(STRING, 0)
            for (nam in names){{
                M_names.append!('M_' + nam)
                }}
            types = tickGetLastTime{u}.schema().colDefs.typeInt join [TIMESTAMP, TIMESTAMP, DOUBLE, DOUBLE, INT, DOUBLE, DOUBLE, INT, TIMESTAMP]
            share streamTable(1:0, M_names , types) as transTable{u}
            """.format(u=u, factorsReturn=tempList)
        s.run(script_defineStreamTable)
        metrics = "<[concatDateTime(M_MDDate, M_MDTime),  " + factors_and_args + ",M_TS_StockStream, M_TS_tickGetLastTime_ahead, \
                M_TS_tickGetLastTime_middle, M_TS_tickGetLastTime_behind, temporalParse(string(M_ReceiveDateTime), 'yyyyMMddHHmmssSSS')]>"
        target_securities = str(target_securities).replace('None', 'NULL')
        script_callFunc = '''
                    calc_factors_and_return_3s_master({metrics}, {startDate}, {endDate}, {marketType}, {symbolGroups}, {cntPerEngine},  StockStream{u},  \
                    orderTradeStream{u},  tickGetLastTime{u},  rseEngineOutput{u},  transTable{u}, `{u})
                    '''.format(metrics=metrics, startDate=start_date,
                               endDate=end_date, cntPerEngine=1,
                               marketType="['tick','trade']", symbolGroups=target_securities, u=u)

        print('calc_factors_and_return_3s_master 定义完成，正在计算...')
        res = s.run(script_callFunc)
        end = time.time()
        print(end-start)
        return res

    elif return_mode == 'write':
        print('TODO')

    s.close()



if __name__ == "__main__":

    target_securities = [('688599.SH', None)]
    factor_list = ['rseF']

    if env == 'uat':
        t1 = time.time()
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'factors')
        config_path = '/'.join(os.path.abspath(__file__).split('/')[:-2] + ['config'])

        res = calc_factors_date(config_path=config_path, file_path=file_path, start_date='20220630',
                                end_date='20220630', target_securities=target_securities, return_mode='show')
        print(res)
        t2 = time.time()
        print("耗时：", t2 - t1)


    if env == 'prd':
        file_path = '/'.join(os.path.abspath(__file__).split('/')[:-2] + ['factors'])
        config_path = '/'.join(os.path.abspath(__file__).split('/')[:-2] + ['config'])
        res = calc_factors_date(config_path=config_path, file_path=file_path, start_date='20211101',
                                end_date='20211102', target_securities=target_securities, return_mode='show')
        print(res)
