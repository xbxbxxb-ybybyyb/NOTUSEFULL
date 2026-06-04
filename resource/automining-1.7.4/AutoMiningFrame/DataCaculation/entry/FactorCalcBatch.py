import dolphindb as ddb
import uuid
import pandas as pd
import re
import os
import sys
import datetime as dt
from decimal import *
basedir = os.path.abspath(os.path.join(os.path.abspath(__file__), '../..'))
sys.path.append(basedir)
import time
import json
from collections import defaultdict
from AutoMiningFrame.DataCaculation.utils.ray_creator import set_ray_options
from AutoMiningFrame.DataCaculation.utils.setenv import get_env
from AutoMiningFrame.configs.local_connect import parse_connect
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
import ray
from xquant.factordata import FactorData
from xquant.marketdata import MarketData
fd = FactorData()
md = MarketData()
env = get_env()


def check_factor_batch_stream(config_path, file_path, non_factor_path=None, study_scenario='stock',
                              data_type='enhanced_tick', user_id=None, path_result=None):
    """

    :param config_path:
    :param file_path:
    :param non_factor_path:
    :param study_scenario:
    :param data_type:
    :param user_id:
    :param path_result:
    :return:
    """
    # 跑批结果
    start_date = '20230505'
    end_date = '20230505'
    target_securities = ['688599.SH']
    return_mode = 'show'
    return_res_name = False
    batchFactor = calc_factors_by_config(config_path, file_path, start_date, end_date, target_securities, return_mode,
                                         non_factor_path=non_factor_path, return_res_name=return_res_name,
                                         study_scenario=study_scenario,
                                         data_type=data_type, user_id=user_id)

    # 流式结果
    factor_module_name = file_path.split("/")[-2]
    nonfactor_module_name = non_factor_path.split("/")[-2]
    nonfactor_dos_name = [i[:-4] for i in os.listdir(non_factor_path) if i.endswith(".dos")]
    factor_names = list(json.loads(open(config_path).read()).keys())
    if os.path.exists("/home/appadmin/server/modules/Factors"):
        print("/home/appadmin/server/modules/Factors 目录已存在，正在删除")
        os.system("rm -r /home/appadmin/server/modules/Factors")
    if os.path.exists("/home/appadmin/server/modules/NoneFactor"):
        print("/home/appadmin/server/modules/NoneFactor 目录已存在，正在删除")
        os.system("rm -r /home/appadmin/server/modules/NoneFactor")
    os.system("cp -r {} /home/appadmin/server/modules/Factors".format(file_path))
    os.system("cp -r {} /home/appadmin/server/modules/NoneFactor".format(non_factor_path))

    dol_start_date = start_date[:4] + "." + start_date[4:6] + "." + start_date[6:]
    dol_end_date = end_date[:4] + "." + end_date[4:6] + "." + end_date[6:]
    s = ddb.session()
    host, port, userid, password = parse_connect()
    s.connect(host=host, port=port, userid=userid, password=password)
    scripts = f"""
    undef all
    go
    Path_noneFactor = "{non_factor_path}"
    Path_Factors =  "{file_path}"
    factorNamesConfig={factor_names}
    use ta
    use DolphinFrame::DataManager    
    /**==============noneFactor=================*/
    noneFactorNames = exec filename from files(Path_noneFactor) where filename != ".gitkeep"
    if (noneFactorNames.size() != 0){{
	for(noneFac in {nonfactor_dos_name}){{runScript("use NoneFactor::" + noneFac)}}
    }}
    /**==============Òò×ÓÏà¹Ø²ÎÊý=================*/
    factorNames = factorNamesConfig
    for (fac in factorNames) runScript("use Factors::" + fac)
    
    def regexFactorNameOfDefAndReturn(Path_Factors, factorName){{
        pathFactor = Path_Factors + factorName + ".dos"
        factorTxt = file(pathFactor)
        lines = factorTxt.readLines()
        factorTxt.close()
        txt = ""
        for (line in lines){{
            txt += line
            }}
        a = txt.regexFind("def")
        b = txt.regexFind("\\\\{{")
        factorDef = txt[(a+4):b]
        c = txt.regexFind("return")
        d = txt.regexFind("\\\\}}", c)
        factorReturn = txt[(c+7):d]
        return factorDef, factorReturn
        }}
    
    factorsDef = []
    factorsReturn = []
    for (factorName in factorNames){{
        D, R = regexFactorNameOfDefAndReturn(Path_Factors, factorName)
        factorsDef.append!(D)
        if(R.like("%,%")){{
            RList = R.split(",")
            for (r in RList) factorsReturn.append!(regexReplace(r,'\\\\s',''))
            }}
        else{{
            factorsReturn.append!(regexReplace(R,'\\\\s',''))
            }}
        }}
    
    factorsDefConcat = ""
    for (x in factorsDef) factorsDefConcat += x + ","
    factorsDefConcat = factorsDefConcat[:factorsDefConcat.strlen()-1]
    script = "metrics = <[concatDateTime(M_MDDate, M_MDTime), " + factorsDefConcat + "]>"
    runScript(script)
    go
    /**=============»Ø·Å¼ÆËãÒò×Ó===============*/
    enhancedTickData = getMarketData_Remote(stock={target_securities}, startTime={dol_start_date}, endTime={dol_end_date}, 
                                            tableName=`sh_stock_tick_enhanced)
    
    names = `M_ReceiveDateTime`M_MDDate`M_HTSCSecurityID`M_MDTime`M_SecurityType`M_SecuritySubType`M_SecurityID`M_SecurityIDSource`M_Symbol`M_TradingPhaseCode`M_PreClosePx`M_NumTrades`M_TotalVolumeTrade`M_TotalValueTrade`M_LastPx`M_OpenPx`M_ClosePx`M_HighPx`M_LowPx`M_DiffPx1`M_DiffPx2`M_MaxPx`M_MinPx`M_TotalBidQty`M_TotalOfferQty`M_WeightedAvgBidPx`M_WeightedAvgOfferPx`M_AfterHoursNumTrades`M_AfterHoursTotalVolumeTrade`M_AfterHoursTotalValueTrade`M_Buy1NoOrders`M_Buy1OrderDetail`M_Sell1NoOrders`M_Sell1OrderDetail`M_TradeMDTime`M_TradeIndex`M_TradeType`M_TradePrice`M_TradeQty`M_TradeBSFlag`M_TradeBuyNo`M_TradeSellNo`M_ApplSeqNum`M_TradeMoney`M_BuyQty`M_BuyMoney`M_BuyCount`M_SellQty`M_SellMoney`M_SellCount`M_BuyPrice`M_BuyOrderQty`M_BuyNumOrders`M_SellPrice`M_SellOrderQty`M_SellNumOrders
    types = ["TIMESTAMP","DATE","SYMBOL","TIME","INT","STRING","STRING","INT","STRING","STRING","DOUBLE","LONG","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","DOUBLE","STRING","DOUBLE","STRING","TIME[]","LONG[]","LONG[]","DOUBLE[]","DOUBLE[]","LONG[]","LONG[]","LONG[]","LONG[]","DOUBLE[]","DOUBLE","DOUBLE","INT","DOUBLE","DOUBLE","INT","DOUBLE[]","DOUBLE[]","DOUBLE[]","DOUBLE[]","DOUBLE[]","DOUBLE[]"]
    sch = table(names as name, types as type)
        
    rseEngineOutput = table(500000:0, `HTSCSecurityID`timestamp join factorsReturn, [SYMBOL, TIMESTAMP] join take(DOUBLE, factorsReturn.size()))
    try{{dropStreamEngine("rseEngine")}} catch(ex){{ print(ex) }}
    rse = createReactiveStateEngine(name = "rseEngine", metrics = metrics, dummyTable = enhancedTickData, outputTable = rseEngineOutput, keyColumn=`M_HTSCSecurityID, keepOrder =true)
    
    replay(enhancedTickData, rse, dateColumn=`M_MDDate, timeColumn=`M_MDTime, replayRate=100000, absoluteRate=false)  
    
    // 返回因子结果
    rseEngineOutput
"""
    
    replayFactor = s.run(scripts)

    # 因子比对
    precision = 4
    #batchFactor['timestamp'] = batchFactor['timestamp'].apply(lambda x: dt.datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
    #replayFactor['timestamp'] = replayFactor['timestamp'].apply(lambda x: dt.datetime.strptime(x, '%Y.%m.%dT%H:%M:%S.000'))

    tmp = set(replayFactor.columns.to_list()) - set(batchFactor.columns.to_list())
    if len(tmp - {'HTSCSecurityID'}) > 0:
        print(f"回放有，跑批没有的因子 : {tmp - {'HTSCSecurityID'}}")
        print('-' * 100)
    tmp = set(batchFactor.columns.to_list()) - set(replayFactor.columns.to_list())
    if len(tmp - {'R_HTSCSecurityID', 'M_HTSCSecurityID'}) > 0:
        print(f"跑批有，回放没有的因子 : {tmp - {'R_HTSCSecurityID', 'M_HTSCSecurityID'}}")
        print('-' * 100)
    factors = sorted(
        list(set(batchFactor.columns.to_list()).intersection(set(replayFactor.columns.to_list())) - {"timestamp"}))

    merge_df = pd.merge(batchFactor, replayFactor, left_on=['timestamp', 'M_HTSCSecurityID'],
                        right_on=['timestamp', 'HTSCSecurityID'],
                        how='outer', suffixes=("_batch", "_replay"))
    columns_batch = [x + '_batch' for x in factors]
    columns_replay = [x + '_replay' for x in factors]
    extra = merge_df[merge_df[columns_batch].isna().all(1)]
    if len(extra) > 0:
        print(f"replay 比 batch 存在多的数据，如下：")
        # print(extra)
        print('-' * 50)
        merge_df.drop(extra.index, inplace=True)
    missing = merge_df[merge_df[columns_replay].isna().all(1)]
    if len(missing) > 0:
        print(f"replay 比 batch 存在缺少数据，如下：")
        # print(missing)
        print('-' * 50)
        merge_df.drop(missing.index, inplace=True)

    print(f"剔除多余和缺少的数据后，逐列对比...")
    columns_zip = list(zip(columns_batch, columns_replay))
    corr_all = pd.DataFrame()
    wrong_all = pd.DataFrame()
    for x, y in columns_zip:
        df_zip = merge_df[['timestamp', 'M_HTSCSecurityID', x, y]]
        # print(df_zip)
        # 2022.03.07T09:30:00.000
        df_zip['date'] = df_zip['timestamp'].apply(
            lambda x: x.strftime("%Y-%m-%d %H:%M:%S").split(" ")[0].replace("-", ""))
        corr_1 = df_zip.groupby('date')[[x, y]].corr()
        corr_1 = corr_1[corr_1.index.get_level_values(1) == y][[x]]
        corr_1 = corr_1.mean().values[0]
        del df_zip['date']
        corr_all = corr_all.append(pd.DataFrame([[x.replace("_batch", ""), corr_1]], columns=['factor', 'corr']))

        # 保留4位小数校验
        df_zip_1 = df_zip.copy()
        df_zip_1.loc[:, x] = df_zip_1.loc[:, x].apply(
                lambda x: Decimal(x).quantize(Decimal('0.' + '0' * precision)))
        df_zip_1.loc[:, y] = df_zip_1.loc[:, y].apply(
                lambda x: Decimal(x).quantize(Decimal('0.' + '0' * precision)))
        df_zip_1.loc[:, 'comp'] = df_zip_1.loc[:, x] == df_zip_1.loc[:, y]
        df_zip_1 = df_zip_1[df_zip_1['comp'] == False]
        # 增加第五位小数校验，解决四舍五入问题，如0.1500与0.1499保留1位小数
        df_zip_2 = df_zip.loc[df_zip_1.index]
        df_zip_2.loc[:, x] = df_zip_2.loc[:, x].apply(
                lambda x: Decimal(x).quantize(Decimal('0.' + '0' * (precision + 1))))
        df_zip_2.loc[:, y] = df_zip_2.loc[:, y].apply(
                lambda x: Decimal(x).quantize(Decimal('0.' + '0' * (precision + 1))))
        df_zip_2.loc[:, 'comp'] = df_zip_2.loc[:, x] == df_zip_2.loc[:, y]
        wrong_col = df_zip_2[df_zip_2['comp'] == False].copy()
        wrong_col[[x, y]] = wrong_col[[x, y]].astype(float)
        #else:
        #    wrong_col = df_zip[df_zip[x] != df_zip[y]]
        #    wrong_col.loc[:, 'comp'] = False
        wrong_col = wrong_col[~wrong_col[[x, y]].isna().all(1)]
        if len(wrong_col) > 0:
            del wrong_col["comp"]
            wrong_col.columns = ["timestamp", "M_HTSCSecurityID", "batch", "replay"]
            wrong_col.insert(0, "factor", x.replace("_batch", ""))
            wrong_all = wrong_all.append(wrong_col)

    return wrong_all, corr_all


def calc_entry_per_factor_per_year(config_path, file_path, start_date, end_date, target_securities, return_mode,
                                   non_factor_path=None, return_res_name=False, study_scenario='stock',
                                   data_type='enhanced_tick', user_id=None):
    s = ddb.session()
    host, port, userid, password = parse_connect()
    s.connect(host=host, port=port, userid=userid, password=password)
    s.run("use ta")
    # s.run("use mytt")

    if non_factor_path:
        list_dir = os.listdir(non_factor_path)
        for non_factor in list_dir:
            if non_factor.endswith(".dos"):
                total_path = os.path.join(non_factor_path, non_factor)
                s.run("file_parse = file('{}')".format(total_path))
                temp = s.run("file_parse.readLines()")
                script_factor = "\n".join(i for i in temp)
                if "@state" in script_factor:
                    script_factor = re.search(r'@.*', script_factor, re.DOTALL).group()
                else:
                    script_factor = re.search(r'def.*', script_factor, re.DOTALL).group()
                s.run(script_factor)

    # TODO: check date
    start_date = start_date[:4] + "." + start_date[4:6] + "." + start_date[6:]
    end_date = end_date[:4] + "." + end_date[4:6] + "." + end_date[6:]
    factors_and_args_list = []
    resFactorList = []
    custom_factor_dict = defaultdict(list)
    factor_config = json.load(open(config_path))
    factor_list = [i for i in factor_config]
    for factor_name in factor_list:
        # 加载配置文件参数
        custom_params = factor_config[factor_name]
        # 因子文件路径
        total_path = os.path.join(file_path, factor_name) + ".dos"
        # 获取因子的计算逻辑

        s.run("file_parse = file('{}')".format(total_path))
        temp = s.run("file_parse.readLines()")
        script_factor = "\n".join(i for i in temp)
        script_factor = re.search(r'@.*', script_factor, re.DOTALL).group()
        for custom_param_dict in custom_params:
            pattern = re.compile(r"[(](.*?)[)][\s{0,}{]", re.S)
            res = re.findall(pattern, script_factor)[0]
            res_copy = res
            for k, v in custom_param_dict.items():
                if k not in res:
                    raise Exception("自定义参数没有: {}".format(k))
                target_param = [i for i in res.split(",") if i.strip().startswith(k) and "=" in i][0]
                res = res.replace(target_param, " " + k + "=" + str(v))
            script_factor_cus = script_factor.replace(res_copy, res)
            if custom_param_dict:
                script_factor_cus = script_factor_cus.replace(factor_name, factor_name + "_" + "_".join(
                    [k + str(v) for k, v in custom_param_dict.items()]))
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
            #print('[FactorCalcBatch] {} - parse factor ok'.format(factor_name))
    start = time.time()

    # 根据标的后缀 判断是上交所还是深交所标的
    if isinstance(target_securities, list):
        exchange_house = target_securities[0].split(".")[1].lower()
    elif isinstance(target_securities, str):
        exchange_house = target_securities.split(".")[1].lower()
    data_type_transfer = {'enhanced_tick': 'tick_enhanced', 'trade': 'trade', 'tick_l2p': 'tick_l2p_persec',
                          'tick': 'tick', 'index_enhanced': 'tick_index', 'l3_flying': 'l3_flying'}
    table_name = exchange_house + "_" + study_scenario + "_" + data_type_transfer[data_type]

    # target_securities = str(target_securities).replace('None', 'NULL')
    temp_str_list = []
    rseList = []
    for i in range(len(factors_and_args_list)):
        temp_str = factors_and_args_list[i] + " as " + "".join("`" + res for res in resFactorList[i])
        rseList += [res for res in resFactorList[i]]
        temp_str_list.append(temp_str)
    metrics = ",".join(temp_str_list)

    # step1: 加载模块
    s.run("""
        use  DolphinFrame::FactorCalcBatch_3s
        use  DolphinFrame::DataManager    
    """)

    # step2: 加载依赖数据
    print('[FactorCalcBatch] 开始加载依赖数据...')
    start_load = time.time()
    # step3: 计算逻辑
    if data_type == 'enhanced_tick':
        load_depend_data = '''
            data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
            data = select * from data where (M_MDTime>=09:30:00 and M_MDTime<=11:30:00) or (M_MDTime>=13:00:00 and M_MDTime<=14:56:00)
            '''.format(startDate=start_date, endDate=end_date, table_name=table_name,
                       target_securities=target_securities)
        s.run(load_depend_data)
        data_clean = '''  
            need_select = select M_MDDate, M_HTSCSecurityID from data group by M_MDDate, M_HTSCSecurityID  having count(*)>={market_data_threshold}
            data = ej(data, need_select, `M_MDDate`M_HTSCSecurityID)
            // 将内存表转为分区表
            colnames = data.schema().colDefs.name
            coltypes = data.schema().colDefs.typeInt
            t=table(1:0,colnames, coltypes)
            db=database("",VALUE,2010.01.01..2030.12.31)
            input_data=db.createPartitionedTable(t,`input_data,`M_MDDate)
            input_data.append!(data)
            data = NULL
            '''.format(metrics=metrics, market_data_threshold=1000)
        s.run(data_clean)
    elif data_type in ['trade','index_enhanced']:
        load_depend_data = '''
            data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
            data = select * from data where (MDTime>=09:30:00 and MDTime<=11:30:00) or (MDTime>=13:00:00 and MDTime<=14:56:00)
            // 将内存表转为分区表
            colnames = data.schema().colDefs.name
            coltypes = data.schema().colDefs.typeInt
            t=table(1:0,colnames, coltypes)
            db=database("",VALUE,2010.01.01..2030.12.31)
            input_data=db.createPartitionedTable(t,`input_data,`MDDate)
            input_data.append!(data)
            data = NULL
            '''.format(startDate=start_date, endDate=end_date, table_name=table_name,
                       target_securities=target_securities)
        s.run(load_depend_data)
    elif data_type == 'tick_l2p':
        load_depend_data = '''
            data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
            data = select * from data where (M_MDTime>=09:30:00 and M_MDTime<=11:30:00) or (M_MDTime>=13:00:00 and M_MDTime<=14:56:00)
            // 将内存表转为分区表
            colnames = data.schema().colDefs.name
            coltypes = data.schema().colDefs.typeInt
            t=table(1:0,colnames, coltypes)
            db=database("",VALUE,2010.01.01..2030.12.31)
            input_data=db.createPartitionedTable(t,`input_data,`M_MDDate)
            input_data.append!(data)
            data = NULL
            '''.format(startDate=start_date, endDate=end_date, table_name=table_name,
                       target_securities=target_securities)
        s.run(load_depend_data)
    elif data_type == 'tick':
        if exchange_house.lower() == 'hk':
            load_depend_data = '''
                    data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
                    data = select * from data where (M_MDTime>=09:30:00 and M_MDTime<=12:00:00) or (M_MDTime>=13:00:00 and M_MDTime<=16:00:00)
                    '''.format(startDate=start_date, endDate=end_date, table_name=table_name,
                               target_securities=target_securities)
            s.run(load_depend_data)
            data_clean = '''  
                    need_select = select M_MDDate, M_HTSCSecurityID from data group by M_MDDate, M_HTSCSecurityID  having count(*)>={market_data_threshold}
                    data = ej(data, need_select, `M_MDDate`M_HTSCSecurityID)
                    // 将内存表转为分区表
                    colnames = data.schema().colDefs.name
                    coltypes = data.schema().colDefs.typeInt
                    t=table(1:0,colnames, coltypes)
                    db=database("",VALUE,2010.01.01..2030.12.31)
                    input_data=db.createPartitionedTable(t,`input_data,`M_MDDate)
                    input_data.append!(data)
                    data = NULL
                    '''.format(metrics=metrics, market_data_threshold=1000)
            s.run(data_clean)
        if exchange_house.lower() == 'cf' or study_scenario=='index':
            load_depend_data = '''
                    data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
                    data = select * from data where (M_MDTime>=09:30:00 and M_MDTime<=11:30:00) or (M_MDTime>=13:00:00 and M_MDTime<=14:56:00)
                    '''.format(startDate=start_date, endDate=end_date, table_name=table_name,
                               target_securities=target_securities)
            s.run(load_depend_data)
            data_clean = '''  
                    need_select = select M_MDDate, M_HTSCSecurityID from data group by M_MDDate, M_HTSCSecurityID  having count(*)>={market_data_threshold}
                    data = ej(data, need_select, `M_MDDate`M_HTSCSecurityID)
                    // 将内存表转为分区表
                    colnames = data.schema().colDefs.name
                    coltypes = data.schema().colDefs.typeInt
                    t=table(1:0,colnames, coltypes)
                    db = database("", VALUE, 2020.01.01..2030.01.30)
                    input_data=db.createPartitionedTable(t,`input_data,`M_MDDate)
                    input_data.append!(data)
                    data = NULL
                    '''.format(metrics=metrics, market_data_threshold=1000)
            s.run(data_clean)
    elif data_type == 'l3_event':
        load_depend_data = '''
                   data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
                   data = select * from data where (M_MDTime>=09:30:00 and M_MDTime<=11:30:00) or (M_MDTime>=13:00:00 and M_MDTime<=14:56:00)
                   // 将内存表转为分区表
                   colnames = data.schema().colDefs.name
                   coltypes = data.schema().colDefs.typeInt
                   t=table(1:0,colnames, coltypes)
                   db=database("",VALUE,2010.01.01..2030.12.31)
                   input_data=db.createPartitionedTable(t,`input_data,`M_MDDate)
                   input_data.append!(data)
                   data = NULL
                   '''.format(startDate=start_date, endDate=end_date, table_name=table_name,
                              target_securities=target_securities)
        load_his_daily_data = '''
                  daily_data = getMarketData_Remote(stock={target_securities},startTime={startDate},endTime={endDate},tableName=`daily_stock_his_data)
                  daily_data = select factor_value from daily_data pivot by mddate, stock_name, factor_name
                  input_data = lj(input_data, daily_data)
                  daily_data = NULL
        '''
        s.run(load_depend_data)
        s.run(load_his_daily_data)

    end_load = time.time()
    print('[FactorCalcBatch] 依赖数据加载完成，cost={}'.format(end_load - start_load))

    print('[FactorCalcBatch] 开始计算因子...')
    start_calc = time.time()
    calc_func = f'''  
        calc_factors_and_save_batch_dates(input_data=input_data, metrics="{metrics}", data_type='{data_type}')
        '''
    res = s.run(calc_func)
    end_calc = time.time()
    print('[FactorCalcBatch] 因子计算完成, cost={}'.format(end_calc - start_calc))
    s.close()

    if return_mode == 'save':
        if not user_id:
            raise Exception("[FactorCalcBatch]save模式下，必须传user_id参数")
        fp = FactorProvider(userID=user_id)
        if data_type == 'tick' and study_scenario == 'future':
            data_type = 'future_tick'
        if data_type == 'tick' and study_scenario == 'index':
            data_type = 'index_tick'
        fp.save_personal_data_to_dfs(res, factor_type='factor', data_type=data_type)
    if return_res_name:
        return res, rseList
    else:
        return res


def calc_factors_by_config(config_path, file_path, start_date, end_date, target_securities, return_mode,
                           non_factor_path=None, return_res_name=False, study_scenario='stock',
                           data_type='enhanced_tick', user_id=None):
    '''
    :param study_scenario: stock or fund
    :param data_type: enhanced_tick or trade
    :param return_res_name:
    :param config_path:  配置文件路径
    :param file_path:    因子文件路径
    :param start_date:   计算开始时间
    :param end_date:      计算结束时间
    :param target_securities:  计算标的
    :param return_mode:   show: 返回因子值 save:存储因子值
    :param non_factor_path: nonFactor文件的路径
    :return: 因子结果或存储的成功与否
    '''
    fa = FactorData()
    date_list = fa.tradingday(start_date, end_date)
    # 查过200天 再拉起来ray

    if len(date_list) <= 2000:
        res = calc_entry_per_factor_per_year(config_path=config_path, file_path=file_path, start_date=start_date,
                                             end_date=end_date, target_securities=target_securities,
                                             return_mode=return_mode, non_factor_path=non_factor_path,
                                             return_res_name=return_res_name, study_scenario=study_scenario,
                                             data_type=data_type, user_id=user_id)
        if return_res_name:
            res_df = res[0]
            resfac_name_list = res[1]
        else:
            res_df = res

    else:
        set_ray_options()
        date_list_combine = []
        temp = []
        for date in date_list:
            if len(temp) < 2000:
                temp.append(date)
            else:
                date_list_combine.append(temp)
                temp = []
        date_list_combine = [[i[0], i[-1]] for i in date_list_combine]
        res = ray.get([ray.remote(calc_entry_per_factor_per_year, config_path=config_path, file_path=file_path,
                                  start_date=start_date, end_date=end_date,
                                  target_securities=target_securities,
                                  return_mode=return_mode, non_factor_path=non_factor_path,
                                  return_res_name=return_res_name,
                                  study_scenario=study_scenario, data_type=data_type, user_id=user_id)
                       for start_date, end_date in date_list_combine])
        if return_res_name:
            res_df = pd.concat([i[0] for i in res])
            resfac_name_list = res[0][1]
        else:
            res_df = pd.concat(res)

    if return_res_name:
        return res_df, resfac_name_list
    else:
        return res_df


def calc_per_factor_by_file(factor_name, file_path, start_date, end_date, target_securities, need_factorfunc=True,
                            automining_formula=None, study_scenario='stock', data_type='enhanced_tick',
                            return_mode='show', non_factor_path=None, user_id=None):
    '''
    :param data_type: enhanced_tick or trade
    :param automining_formula:
    :param factor_name: 计算因子文件名称 也是因子名
    :param file_path:   因子文件所在路径
    :param start_date:  开始时间
    :param end_date:    结束时间
    :param target_securities: 计算标的
    :param need_factorfunc:   是否需要返回因子相关信息
    :param study_scenario
    :return: 因子数据 或者 因子数据+因子表达式+因子依赖
    '''
    s = ddb.session()
    host, port, userid, password = parse_connect()
    s.connect(host=host, port=port, userid=userid, password=password)
    s.run("use ta")
    start_date = start_date[:4] + "." + start_date[4:6] + "." + start_date[6:]
    end_date = end_date[:4] + "." + end_date[4:6] + "." + end_date[6:]

    if non_factor_path:
        list_dir = os.listdir(non_factor_path)
        for non_factor in list_dir:
            if non_factor.endswith(".dos"):
                total_path = os.path.join(non_factor_path, non_factor)
                s.run("file_parse = file('{}')".format(total_path))
                temp = s.run("file_parse.readLines()")
                script_factor = "\n".join(i for i in temp)
                if "@state" in script_factor:
                    script_factor = re.search(r'@.*', script_factor, re.DOTALL).group()
                else:
                    script_factor = re.search(r'def.*', script_factor, re.DOTALL).group()
                s.run(script_factor)

    if automining_formula:
        if not os.path.exists(file_path):
            os.system(f"mkdir -p {file_path}")
        gen_factor_module(path=file_path, factor_name=factor_name, factor_expression=automining_formula)
    total_path = os.path.join(file_path, factor_name) + ".dos"
    s.run("file_parse = file('{}')".format(total_path))
    temp = s.run("file_parse.readLines()")
    script_factor = "\n".join(i for i in temp)
    script_factor = re.search(r'@.*', script_factor, re.DOTALL).group()
    # 执行函数
    s.run(script_factor)

    sear = re.search(r'def (.*?){.*?return (.*?)}', script_factor, re.DOTALL)
    # 提取函数名
    funcFactor = sear.group(1)
    # 提取结果因子名
    resFactor = sear.group(2)
    resFactor = re.sub(r'\s', '', resFactor).split(',')
    # 校验函数名
    for res in resFactor:
        if not res.startswith(factor_name):
            raise Exception(
                'return因子名需以函数名为前缀，如{res} --> {factor_name}_{res}'.format(factor_name=factor_name, res=res))
    # 拼接select 函数
    metrics = funcFactor + " as " + "".join("`" + res for res in resFactor)

    # 根据标的后缀 判断是上交所还是深交所标的
    if isinstance(target_securities, list):
        exchange_house = target_securities[0].split(".")[1].lower()
    elif isinstance(target_securities, str):
        exchange_house = target_securities.split(".")[1].lower()
    data_type_transfer = {'enhanced_tick': 'tick_enhanced', 'trade': 'trade', 'tick_l2p': 'tick_l2p_persec',
                          'tick': 'tick', 'index_enhanced': 'tick_index','l3_flying': 'l3_flying'}
    table_name = exchange_house + "_" + study_scenario + "_" + data_type_transfer[data_type]

    # step1: 加载模块
    s.run("""
        use  DolphinFrame::FactorCalcBatch_3s
        use  DolphinFrame::DataManager    
    """)

    # step2: 加载依赖数据
    print('[FactorCalcBatch] 开始加载依赖数据...')
    start_load = time.time()
    # step3: 计算逻辑
    if data_type == 'enhanced_tick':
        load_depend_data = '''
            data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
            data = select * from data where (M_MDTime>=09:30:00 and M_MDTime<=11:30:00) or (M_MDTime>=13:00:00 and M_MDTime<=14:56:00)
            '''.format(startDate=start_date, endDate=end_date, table_name=table_name,
                       target_securities=target_securities)
        s.run(load_depend_data)
        data_clean = '''  
            need_select = select M_MDDate, M_HTSCSecurityID from data group by M_MDDate, M_HTSCSecurityID  having count(*)>={market_data_threshold}
            data = ej(data, need_select, `M_MDDate`M_HTSCSecurityID)
            // 将内存表转为分区表
            colnames = data.schema().colDefs.name
            coltypes = data.schema().colDefs.typeInt
            t=table(1:0,colnames, coltypes)
            db=database("",VALUE,2010.01.01..2030.12.31)
            input_data=db.createPartitionedTable(t,`input_data,`M_MDDate)
            input_data.append!(data)
            data = NULL
            '''.format(metrics=metrics, market_data_threshold=1000)
        s.run(data_clean)
    elif data_type in ['trade', 'index_enhanced']:
        load_depend_data = '''
            data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
            data = select * from data where (MDTime>=09:30:00 and MDTime<=11:30:00) or (MDTime>=13:00:00 and MDTime<=14:56:00)
            // 将内存表转为分区表
            colnames = data.schema().colDefs.name
            coltypes = data.schema().colDefs.typeInt
            t=table(1:0,colnames, coltypes)
            db=database("",VALUE,2010.01.01..2030.12.31)
            input_data=db.createPartitionedTable(t,`input_data,`MDDate)
            input_data.append!(data)
            data = NULL
            '''.format(startDate=start_date, endDate=end_date, table_name=table_name,
                       target_securities=target_securities)
        s.run(load_depend_data)
    elif data_type == 'tick_l2p':
        load_depend_data = '''
            data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
            data = select * from data where (M_MDTime>=09:30:00 and M_MDTime<=11:30:00) or (M_MDTime>=13:00:00 and M_MDTime<=14:56:00)
            // 将内存表转为分区表
            colnames = data.schema().colDefs.name
            coltypes = data.schema().colDefs.typeInt
            t=table(1:0,colnames, coltypes)
            db=database("",VALUE,2010.01.01..2030.12.31)
            input_data=db.createPartitionedTable(t,`input_data,`M_MDDate)
            input_data.append!(data)
            data = NULL
            '''.format(startDate=start_date, endDate=end_date, table_name=table_name,
                       target_securities=target_securities)
        s.run(load_depend_data)
    elif data_type == 'tick':
        if exchange_house.lower() == 'hk':
            load_depend_data = '''
                data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
                data = select * from data where (M_MDTime>=09:30:00 and M_MDTime<=12:00:00) or (M_MDTime>=13:00:00 and M_MDTime<=16:00:00)
                '''.format(startDate=start_date, endDate=end_date, table_name=table_name,
                           target_securities=target_securities)
            s.run(load_depend_data)
            data_clean = '''  
                // 将内存表转为分区表
                colnames = data.schema().colDefs.name
                coltypes = data.schema().colDefs.typeInt
                t=table(1:0,colnames, coltypes)
                db=database("",VALUE,2010.01.01..2030.12.31)
                input_data=db.createPartitionedTable(t,`input_data,`M_MDDate)
                input_data.append!(data)
                data = NULL
                '''.format(metrics=metrics, market_data_threshold=1000)
            s.run(data_clean)
        if exchange_house.lower() == 'cf' or study_scenario=='index':
            load_depend_data = '''
                    data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
                    data = select * from data where (M_MDTime>=09:30:00 and M_MDTime<=11:30:00) or (M_MDTime>=13:00:00 and M_MDTime<=14:56:00)
                    '''.format(startDate=start_date, endDate=end_date, table_name=table_name,
                               target_securities=target_securities)
            s.run(load_depend_data)
            data_clean = '''  
                    need_select = select M_MDDate, M_HTSCSecurityID from data group by M_MDDate, M_HTSCSecurityID  having count(*)>={market_data_threshold}
                    data = ej(data, need_select, `M_MDDate`M_HTSCSecurityID)
                    // 将内存表转为分区表
                    colnames = data.schema().colDefs.name
                    coltypes = data.schema().colDefs.typeInt
                    t=table(1:0,colnames, coltypes)
                    db = database("", VALUE, 2020.01.01..2030.01.30)
                    input_data=db.createPartitionedTable(t,`input_data,`M_MDDate)
                    input_data.append!(data)
                    data = NULL
                    '''.format(metrics=metrics, market_data_threshold=1000)
            s.run(data_clean)
    elif data_type == 'l3_event':
        load_depend_data = '''
                   data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
                   data = select * from data where (M_MDTime>=09:30:00 and M_MDTime<=11:30:00) or (M_MDTime>=13:00:00 and M_MDTime<=14:56:00)
                   // 将内存表转为分区表
                   colnames = data.schema().colDefs.name
                   coltypes = data.schema().colDefs.typeInt
                   t=table(1:0,colnames, coltypes)
                   db=database("",VALUE,2010.01.01..2030.12.31)
                   input_data=db.createPartitionedTable(t,`input_data,`M_MDDate)
                   input_data.append!(data)
                   data = NULL
                   '''.format(startDate=start_date, endDate=end_date, table_name=table_name,
                              target_securities=target_securities)
        load_his_daily_data = '''
                  daily_data = getMarketData_Remote(stock={target_securities},startTime={startDate},endTime={endDate},tableName=`daily_stock_his_data)
                  daily_data = select factor_value from daily_data pivot by mddate, stock_name, factor_name
                  input_data = lj(input_data, daily_data,`M_MDDate`M_HTSCSecurityID,`mddate`stock_name)
                  daily_data = NULL
        '''
        s.run(load_depend_data)
        s.run(load_his_daily_data)

    end_load = time.time()
    print('[FactorCalcBatch] 依赖数据加载完成，cost={}'.format(end_load - start_load))

    print('[FactorCalcBatch] 开始计算因子...')
    start_calc = time.time()
    calc_func = f'''  
        calc_factors_and_save_batch_dates(input_data=input_data, metrics="{metrics}", data_type='{data_type}')
        '''
    res = s.run(calc_func)
    end_calc = time.time()
    print('[FactorCalcBatch] 因子计算完成, cost={}'.format(end_calc - start_calc))

    if return_mode == 'save':
        if not user_id:
            raise Exception("[FactorCalcBatch]save模式下，必须传user_id参数")
        fp = FactorProvider(userID=user_id)
        if data_type == 'tick' and study_scenario == 'future':
            data_type = 'future_tick'
        if data_type == 'tick' and study_scenario == 'index':
            data_type = 'index_tick'
        fp.save_personal_data_to_dfs(res, factor_type='factor', data_type=data_type)
    if need_factorfunc:
        return script_factor, funcFactor, resFactor, res
    else:
        return res


def gen_factor_module(path, factor_name, factor_expression):
    all_cols = ["M_HTSCSecurityID", "M_LastTime", "M_MDDate", "M_MDTime", "M_SecurityType", "M_SecuritySubType",
                "M_SecurityID",
                "M_SecurityIDSource", "M_Symbol", "M_TradingPhaseCode", "M_PreClosePx", "M_NumTrades",
                "M_TotalVolumeTrade",
                "M_TotalValueTrade", "M_LastPx", "M_OpenPx", "M_ClosePx", "M_HighPx", "M_LowPx", "M_DiffPx1",
                "M_DiffPx2",
                "M_MaxPx", "M_MinPx", "M_TotalBidQty", "M_TotalOfferQty", "M_WeightedAvgBidPx", "M_WeightedAvgOfferPx",
                "M_AfterHoursNumTrades", "M_AfterHoursTotalVolumeTrade", "M_AfterHoursTotalValueTrade",
                "M_Buy1NoOrders",
                "M_Buy1OrderDetail", "M_Sell1NoOrders", "M_Sell1OrderDetail", "M_ReceiveDateTime", "M_ChannelNo",
                "M_BuyPrice",
                "M_BuyOrderQty", "M_BuyNumOrders", "M_SellPrice", "M_SellOrderQty", "M_SellNumOrders", "M_BuyQty",
                "M_BuyMoney",
                "M_BuyCount", "M_SellQty", "M_SellMoney", "M_SellCount"]
    need_cols = []
    for col in all_cols:
        if col in factor_expression:
            need_cols.append(col)
    need_cols = ','.join(need_cols)
    script = f"module {factor_name} \n@state\ndef {factor_name}({need_cols}){{\n{factor_name}={factor_expression}\nreturn {factor_name}\n}}"
    path = path if path.endswith("/") else path + "/"
    path = path + factor_name + ".dos"
    if os.path.exists(path):
        raise Exception(f"文件 {path} 已存在，请修改因子文件名或路径重新执行")
    file = open(path, 'w+', )
    file.write(script)
    file.close()


def calc_factor_by_custom_data(factor_name, file_path, custom_data=None, study_scenario='stock', data_type='enhanced_tick',
                               non_factor_path=None, custom_params={}):
    '''
    :param data_type: enhanced_tick or trade
    :param automining_formula:
    :param factor_name: 计算因子文件名称 也是因子名
    :param file_path:   因子文件所在路径
    :param start_date:  开始时间
    :param end_date:    结束时间
    :param target_securities: 计算标的
    :param need_factorfunc:   是否需要返回因子相关信息
    :param study_scenario
    :return: 因子数据 或者 因子数据+因子表达式+因子依赖
    '''
    s = ddb.session()
    host, port, userid, password = parse_connect()
    s.connect(host=host, port=port, userid=userid, password=password)
    s.run("use ta")
    if 'MDDate' not in custom_data or 'MDTime' not in custom_data:
        raise Exception("custom_data 中必须包含日期列(MDDate)和时间列（MDTime）")
    custom_data = custom_data.sort_values(['MDDate', 'MDTime'])
    start_date = str(custom_data['MDDate'].iloc[0])
    end_date = str(custom_data['MDDate'].iloc[-1])

    custom_data['MDDate'] = custom_data['MDDate'].astype(str)
    custom_data['MDTime'] = custom_data['MDTime'].astype(str).apply(lambda x:x.zfill(9)) 
    start_date = start_date[:4] + "." + start_date[4:6] + "." + start_date[6:]
    end_date = end_date[:4] + "." + end_date[4:6] + "." + end_date[6:]
    target_securities = list(set(custom_data['HTSCSecurityID'].values))

    if non_factor_path:
        list_dir = os.listdir(non_factor_path)
        for non_factor in list_dir:
            if non_factor.endswith(".dos"):
                total_path = os.path.join(non_factor_path, non_factor)
                s.run("file_parse = file('{}')".format(total_path))
                temp = s.run("file_parse.readLines()")
                script_factor = "\n".join(i for i in temp)
                if "@state" in script_factor:
                    script_factor = re.search(r'@.*', script_factor, re.DOTALL).group()
                else:
                    script_factor = re.search(r'def.*', script_factor, re.DOTALL).group()
                s.run(script_factor)
    # 因子文件路径
    total_path = os.path.join(file_path, factor_name) + ".dos"

    # 获取因子的计算逻辑
    s.run("file_parse = file('{}')".format(total_path))
    temp = s.run("file_parse.readLines()")
    script_factor = "\n".join(i for i in temp)
    script_factor = re.search(r'@.*', script_factor, re.DOTALL).group()
    custom_factor_dict = defaultdict(list)
    #custom_params = custom_params[factor_name]
    for custom_param_dict in custom_params:
        pattern = re.compile(r"[(](.*?)[)][\s{0,}{]", re.S)
        res = re.findall(pattern, script_factor)[0]
        res_copy = res
        for k, v in custom_param_dict.items():
            if k not in res:
                raise Exception("自定义参数没有: {}".format(k))
            target_param = [i for i in res.split(",") if i.strip().startswith(k) and "=" in i][0]
            res = res.replace(target_param, " " + k + "=" + str(v))
        script_factor_cus = script_factor.replace(res_copy, res)
        if custom_param_dict:
            script_factor_cus = script_factor_cus.replace(factor_name, factor_name + "_" + "_".join(
                [k + str(v) for k, v in custom_param_dict.items()]))
        custom_factor_dict[factor_name].append(script_factor_cus)

    factors_and_args_list = []
    resFactorList = []
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
            #print('[FactorCalcBatch] {} - parse factor ok'.format(factor_name))


    temp_str_list = []
    rseList = []
    for i in range(len(factors_and_args_list)):
        temp_str = factors_and_args_list[i] + " as " + "".join("`" + res for res in resFactorList[i])
        rseList += [res for res in resFactorList[i]]
        temp_str_list.append(temp_str)
    metrics = ",".join(temp_str_list)

    # 根据标的后缀 判断是上交所还是深交所标的
    if isinstance(target_securities, list):
        exchange_house = target_securities[0].split(".")[1].lower()
    elif isinstance(target_securities, str):
        exchange_house = target_securities.split(".")[1].lower()
    data_type_transfer = {'enhanced_tick': 'tick_enhanced', 'trade': 'trade', 'tick_l2p': 'tick_l2p_persec',
                          'tick': 'tick', 'index_enhanced': 'tick_index'}

    table_name = exchange_house + "_" + study_scenario + "_" + data_type_transfer[data_type]
    # step1: 加载模块
    s.run("""
        use  DolphinFrame::FactorCalcBatch_3s
        use  DolphinFrame::DataManager    
    """)

    # step2: 加载依赖数据
    print('[FactorCalcBatch] 开始加载依赖数据...')
    start_load = time.time()
    # step3: 计算逻辑
    if data_type == 'enhanced_tick':
        load_depend_data = '''
            data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
            data = select * from data where (M_MDTime>=09:30:00 and M_MDTime<=11:30:00) or (M_MDTime>=13:00:00 and M_MDTime<=14:56:00)
            '''.format(startDate=start_date, endDate=end_date, table_name=table_name,
                       target_securities=target_securities)
        s.run(load_depend_data)
        data_clean = '''  
            need_select = select M_MDDate, M_HTSCSecurityID from data group by M_MDDate, M_HTSCSecurityID  having count(*)>={market_data_threshold}
            data = ej(data, need_select, `M_MDDate`M_HTSCSecurityID)
            data
        '''
        input_data = s.run(data_clean)
    elif data_type in ['trade','index_enhanced']:
        load_depend_data = '''
            data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
            data = select * from data where (MDTime>=09:30:00 and MDTime<=11:30:00) or (MDTime>=13:00:00 and MDTime<=14:56:00)
            '''
        input_data = s.run(load_depend_data)
    elif data_type in ['tick_l2p', 'future_tick']:
        load_depend_data = '''
            data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
            data = select * from data where (M_MDTime>=09:30:00 and M_MDTime<=11:30:00) or (M_MDTime>=13:00:00 and M_MDTime<=14:56:00)
            data
        '''
        input_data = s.run(load_depend_data)
    elif data_type in ['tick']:
        if exchange_house.lower() == 'hk':
            load_depend_data = '''
                data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
                data = select * from data where (M_MDTime>=09:30:00 and M_MDTime<=12:00:00) or (M_MDTime>=13:00:00 and M_MDTime<=16:00:00)
                data
                '''.format(startDate=start_date, endDate=end_date, table_name=table_name,
                           target_securities=target_securities)
            input_data = s.run(load_depend_data)
        if exchange_house.lower() == 'cf':
            load_depend_data = '''
                    data = getMarketData_Remote(stock={target_securities}, startTime={startDate}, endTime={endDate}, tableName=`{table_name})
                    data = select * from data where (M_MDTime>=09:30:00 and M_MDTime<=11:30:00) or (M_MDTime>=13:00:00 and M_MDTime<=14:56:00)
                    data
                    '''.format(startDate=start_date, endDate=end_date, table_name=table_name,
                               target_securities=target_securities)
            input_data = s.run(load_depend_data)

        end_load = time.time()
        print('[FactorCalcBatch] 依赖数据加载完成，cost={}'.format(end_load - start_load))

    if data_type in ['tick', 'tick_l2p', 'enhanced_tick']:
        star_merge = time.time()
        input_data['M_MDTime'] = input_data['M_MDTime'].astype(str).apply(
            lambda x: x[11:].replace(":", "").replace(".", ""))
        input_data['M_MDDate'] = input_data['M_MDDate'].astype(str).apply(lambda x: x.replace("-", ""))
        merge_data = pd.merge(input_data, custom_data, left_on=['M_MDDate', 'M_MDTime'], right_on=['MDDate', 'MDTime'],
                              how='left')
        merge_data = merge_data.sort_values(['M_MDDate', 'M_MDTime'])
        s.upload({"merge_data": merge_data})
        s.run("""
        merge_data.replaceColumn!(`M_MDDate, temporalParse(merge_data.M_MDDate, 'yyyyMMdd'))
        merge_data.replaceColumn!(`M_MDTime, temporalParse(string(merge_data.M_MDTime),"HHmmssSSS"))
        colnames = merge_data.schema().colDefs.name
        coltypes = merge_data.schema().colDefs.typeInt
        t=table(1:0,colnames, coltypes)
        db=database("",VALUE,2010.01.01..2030.12.31)
        input_data=db.createPartitionedTable(t,`input_data,`M_MDDate)
        input_data.append!(merge_data)
        merge_data = NULL
        """)
    elif data_type in ['trade','index_enhanced']:
        star_merge = time.time()
        input_data['MDTime'] = input_data['MDTime'].astype(str).apply(
            lambda x: x[11:].replace(":", "").replace(".", ""))
        input_data['MDDate'] = input_data['MDDate'].astype(str).apply(lambda x: x.replace("-", ""))
        merge_data = pd.merge(input_data, custom_data, left_on=['MDDate', 'MDTime'], right_on=['MDDate', 'MDTime'],
                              how='left')
        merge_data = merge_data.sort_values(['MDDate', 'MDTime'])
        s.upload({"merge_data": merge_data})
        s.run("""
        merge_data.replaceColumn!(`MDDate, temporalParse(merge_data.MDDate, 'yyyyMMdd'))
        merge_data.replaceColumn!(`MDTime, temporalParse(string(merge_data.MDTime),"HHmmssSSS"))
        colnames = merge_data.schema().colDefs.name
        coltypes = merge_data.schema().colDefs.typeInt
        t=table(1:0,colnames, coltypes)
        db=database("",VALUE,2010.01.01..2030.12.31)
        input_data=db.createPartitionedTable(t,`input_data,`MDDate)
        input_data.append!(merge_data)
        merge_data = NULL
        """)
    end_merge = time.time()
    print('[FactorCalcBatch] 数据融合完成，cost={}'.format(end_merge - star_merge))

    # 拼接select 函数
    start_calc = time.time()
    calc_func = f'''  
        calc_factors_and_save_batch_dates(input_data=input_data, metrics="{metrics}", data_type='{data_type}')
        '''
    res = s.run(calc_func)
    end_calc = time.time()
    print('[FactorCalcBatch] 因子计算完成，cost={}'.format(end_calc - start_calc))

    return res


if __name__ == "__main__":

    target_securities = ['688599.SH', '688363.SH', '688029.SH']

    if env == 'uat':
        t1 = time.time()
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'factors')
        config_path = '/'.join(os.path.abspath(__file__).split('/')[:-2] + ['config', 'factor_config.json'])
        non_factor_path = "/app/dolphindb/server/modules/NonFactor"

        res = calc_factors_by_config(config_path=config_path, file_path=file_path, start_date='20220620',
                                     end_date='20220630',
                                     target_securities=target_securities,
                                     return_mode='show', non_factor_path=non_factor_path)
        print(res.head())
        print(len(res))
        t2 = time.time()
        print("耗时：", t2 - t1)

    if env == 'prd':
        file_path = '/'.join(os.path.abspath(__file__).split('/')[:-2] + ['factors'])
        # config_path = '/'.join(os.path.abspath(__file__).split('/')[:-2] + ['config'])
        config_path = '/'.join(os.path.abspath(__file__).split('/')[:-2] + ['config', 'factor_config.json'])
        res = calc_factors_by_config(config_path=config_path, file_path=file_path, start_date='20220620',
                                     end_date='20220630',
                                     target_securities=target_securities, return_mode='show')
        print(res)
