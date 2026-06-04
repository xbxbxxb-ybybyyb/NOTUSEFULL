import os
import json
import pandas as pd
from xquant.strategy.ats_backtest.batch_runner import BatchRunner
from xquant.strategy.ats_backtest.analyze.analyze_tool import AnalyzeTool
from xquant.compute.ray_cluster import start_ray_cluster, recycle_ray_cluster
import time
import traceback
import uuid
import math
from tqdm import tqdm
from datetime import datetime
from artifacts import exp_artifacts, model_save_and_evaluate

def ats_main(symbol,signal_path, trade_result_path, param_json_path, start_date = None, end_date = None):
    #####################  设置回测路径  ##################
    #策略jar包存储路径，用户需提前上传
    strategy_path = "/data/user/016869/AutoMiningFrame/trade_data/mm_strategy/strategy_jar/0423/"
    lib_path = "/data/user/016869/AutoMiningFrame/trade_data/mm_strategy/strategy_jar/lib_dol/"
    # 策略日志存储路径，按照策略ID分别打包成不同zip包。创建失败的策略实例无日志zip包
    datapath = eval("f\"" + signal_path+"\"")
    outputpath = eval("f\"" +trade_result_path+"\"")
    json_path = eval("f\"" +param_json_path+"\"")
    log_path = outputpath#os.path.join("/dfs/user/013150/", "log_new/")
    print("strategy_path:", strategy_path)

    #####################  设置回测资源  ##################
    param_list = []
    cpus_per_node = 4
    mem_per_node = 20
    workers = 4
    params_path = os.path.dirname(param_json_path)
    t = BatchRunner(
        strategy_path=strategy_path,
        params_path=params_path,
        log_path=log_path,
        lib_path=lib_path,
        cpus_per_node = cpus_per_node,
        mem_per_node = mem_per_node,
        workers=workers,
        local_cluster = True, auto_close=False)

    ##################### 创建回测任务  ##################
    with open(json_path, 'r',encoding='utf-8') as f:
        strategy_param = json.load(f)
    strategy_param["策略标的"] = symbol
    date_list = sorted([date_str[:-4] for date_str in sorted(os.listdir(datapath)) if date_str.endswith("txt")])
    if not start_date and not end_date:
        start_date, end_date = date_list[0], date_list[-1]
    else:
        start_date = max(date_list[0], pd.to_datetime(start_date).strftime("%Y-%m-%d"))
        end_date = min(date_list[-1], pd.to_datetime(end_date).strftime("%Y-%m-%d"))
    print(datapath, start_date ,end_date)
    param_json = {
#         "Strategy": "STARAccumulativeSubStrategy",
        "Strategy": "STARDynamicStopProfitSubStrategy",
        "MarketDataTunnel": "CUSTOMIZED",
        "BackTestTimeFrame": "PERIOD_Tick",
        "ReportTimeFrame": "PERIOD_Tick",
        "Match": "TRADE",
        "Environment":"UAT",
        "CustomizedXmlFile": "bean.xml",
        "BaseCash": 5000000,
        "Commission": 0.0003,
        "StampDuty": 0.001,
        "Universe": [{"Symbol": symbol, "Quantity": 200000, "BuySecAcc": "1", "SellSecAcc": "1", "BuyTradeAcc": "1", "SellTradeAcc": "1", "PortfolioNo": "1", "PortfolioType": "1"}],
        "StartDate": None, "EndDate": None, "SpecHistoryMDService": "XQUANT",
        "StrategyType":"CONSUMER",
        'PublisherFile':os.path.join(datapath,"{}.txt".format(start_date)),
        'SpecHisotryMDServiceParam': {'xquantStartDate': start_date, 'xquantEndDate': end_date},
        "StrategyParam": strategy_param
    }
    param_list.append(param_json)


    t_sta = time.time()
    print("len(param_list)):", len(param_list))
    res_dict = t.run(param_list)
    analyze_tool = AnalyzeTool(log_path=log_path, res_dict=res_dict)
    task_ids = analyze_tool.get_all_task_ids()
    result = []
    records = []
    
    if not os.path.exists(outputpath):
        os.makedirs(outputpath)
        
    for t_id in task_ids:
        resp_df = analyze_tool.get_result_by_task_id(t_id)
        # 获取本次任务的执行流水
        try:
            trade_records_dict = analyze_tool.get_trade_records_by_task_id(t_id)
            trade_records_df = pd.concat(list(trade_records_dict.values())).sort_values(by=["filledDate"])
            pnl_dict = analyze_tool.get_last_trade_reports_by_task_id(t_id)
            pnl = pd.concat(list(pnl_dict.values()))
            # print(pnl)
            # print(trade_records_df)
            pnl.to_excel(outputpath + "{}_{}_result.xlsx".format(symbol,start_date))
            trade_records_df.to_excel(outputpath + "{}_{}_records.xlsx".format(symbol,start_date))
            result.append(pnl)
            records.append(trade_records_df)
        except:
            print(traceback.print_exc())
            print("error trade records", t_id)
            continue
    print("ATSQuant 回测耗时： ", time.time() - t_sta)

    try:
        result_df = pd.concat(result)
        result_df.to_excel(outputpath + "{}_result.xlsx".format(symbol))
        result_df = pd.concat(records).sort_values(by=["filledDate"])
        result_df.to_excel(outputpath + "{}_records.xlsx".format(symbol))
    except Exception as e:
        print(traceback.print_exc())
        print("error trade result", e)

def get_backtest_path(symbol,  process_singal = True, online_path = False,  **kwargs):
    """
    :param symbol:
    :param process_singal: 为True将读取Parquet文件并生成txt文件
    :param online_path: 为False转为Artifacts格式，为True为线上路径格式
    :param kwargs:
    :return:
    """
    # online_path, 是否读取线上信号文件路径
    if online_path:
        # dir_dict = {"688012.SH": "688012.SH_trade_v1.2"}
        # stock = "688012.SH"
        # signal_dir = f"/data/user/016869/AutoMiningFrame/trade_data/COO/{stock}-{dir_dict[stock]}/mm_ai_signal/online"
        pred_th_up = kwargs["pred_th_up"]
        pred_th_dw = kwargs["pred_th_dw"]
        label_name = kwargs["label_name"]
        exp_name = kwargs["exp_name"]
        flag = False
        for exp_name in [exp_name]+["unite_semi_v1.1", "semi_v1.1", "computer_v1.1", "nation_innovation_v1.1"]:
            base_dir = f"/data/user/013150/trade_data/COO/{exp_name}"
            parquet_path = os.path.join(base_dir, f"signal_files/{label_name}-{symbol}.parquet")
            if not os.path.exists(parquet_path):
                continue
            flag = True
            break
        if flag == False:
            raise Exception("无满足要求的线上文件格式！", parquet_path)
        signal_dir = os.path.join(base_dir, f"{label_name}-{symbol}/pred_th_up@{'%.2f'%pred_th_up}-pred_th_dw@{'%.2f'%abs(pred_th_dw)}/signal_files_processed")
        if process_singal:
            signal_df_load = pd.read_parquet(parquet_path)
            # 存储该阈值信号文件
            model_save_and_evaluate.model_signal_process_long_short_pred_th_classify(signal_df_load,
                                                                                 pred_th_up=pred_th_up,
                                                                                 pred_th_dw=pred_th_dw,
                                                                                 symbol=symbol,
                                                                                 signal_process_base_dir=signal_dir)
    else:
        exp_name = kwargs["exp_name"]
        version_alias = kwargs["version_alias"]
        pred_th_up = kwargs["pred_th_up"]
        pred_th_dw = kwargs["pred_th_dw"]
        label_name = kwargs["label_name"]
        # expa = exp_artifacts.ExpArtifacts(exp_name=exp_name, exp_base = "/dfs/group/800657/exp_results")
        expa = exp_artifacts.ExpArtifacts(exp_name=exp_name)
        expa.activate_version_to_save(version_alias = version_alias)
        signal_dir = expa.path_of_signal_process_save(evaluate_type="long_short_pred_th_classify",
                                                                   version_alias=version_alias,
                                                                   label_name=label_name,
                                                                   symbol=symbol,
                                                                   pred_th_up=pred_th_up, pred_th_dw=pred_th_dw)
        if process_singal:
            signal_df_load = expa.model_signal_load(version_alias = version_alias, label_name=label_name, symbol=symbol)
            model_save_and_evaluate.model_signal_process_long_short_pred_th_classify(signal_df_load, pred_th_up=pred_th_up,
                                                                                     pred_th_dw=pred_th_dw,
                                                                                     symbol=symbol,
                                                                                     signal_process_base_dir=signal_dir)

    return signal_dir


def get_online_param(SYMBOL, tradingdate = "2024-06-12"):
    if SYMBOL == "688256.SH":
        StrategyModelName = "unite_kc"
    elif SYMBOL in ["688390.SH", "688047.SH"]:
        StrategyModelName = "l2p_kc_basket"
    elif SYMBOL in ["688041.SH", "688012.SH", "688271.SH"]:
        StrategyModelName = "l3_kc_flying4"
    elif SYMBOL in ["688981.SH"]:
        StrategyModelName = "l2p_688981.SH_v1.1"
    elif SYMBOL in ["688498.SH"]:
        StrategyModelName = "l2p_kc100_v1"
    else:
        raise Exception("no such symbol: ", SYMBOL)
    mm_json_path = f'/data/user/016869/AutoMiningFrame/trade_data/mm_strategy/online_params/{tradingdate}/params_{SYMBOL}_{StrategyModelName}_{tradingdate}.json'
    param_json_path = f"/data/user/013150/tmp/params_{SYMBOL}_{StrategyModelName}.json"
    print("实盘原始策略参数路径: ", mm_json_path)
    print("回测策略参数路径: ", param_json_path)
    with open(mm_json_path, "r") as f:
        mm_json = json.load(f)
    param_json = json.loads(mm_json['mapList'][1]['11044'])
    param_json["信号参数设置"][0]["铺单指定的类型"] = 'OnnxTest'
    param_json["信号参数设置"][0]['订阅铺单信号策略类型'] = 'OnnxTest'
    # param_json['事件应对机制'][0]['单边成交最大控制'] = math.ceil(int(result_df['sell_qty'])/100) * 100
    # param_json['事件应对机制'][0]['单边成交最大控制'] = max(param_json['事件应对机制'][0]['单边成交最大控制'],math.ceil(int(result_df['sell_qty'])/100) * 100)
    mm_json['mapList'][1]['11044'] = param_json
    try:
        param_json.pop("43049")
    except:
        pass
    with open(eval("f\"" +param_json_path+"\""), "w", encoding = "utf-8") as f:
        # json.dump({**mm_json['mapList'][1],**mm_json['mapList'][1]['11044']},f,indent=4, ensure_ascii=False)
        json.dump(param_json,f,indent=4, ensure_ascii=False)
    return param_json_path

if __name__=="__main__":
    symbol_list = [
        # ("688256.SH", 1.3, -1.2),
        # ("688012.SH", 1.3, -1.2),
        # ("688041.SH", 1.3, -1.2),
        # ("688498.SH", 1.3, -1.2),
        ("688981.SH", 1.3, -1.2),
        ("688041.SH", 1.3, -1.2)
    ]

    for SYMBOL, pred_th_up, pred_th_dw in symbol_list:
        #########################解析实盘策略参数############################
        param_json_path = get_online_param(SYMBOL)

        for label_name, exp_name, version_alias in [
            # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_log2_huber1'),
            # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_log2')
            ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98')
        ]:
            # 信号参数网格
            for pred_th_up in [1.4, 1.5, 1.6, 1.7]:
                pred_th_dw = -(pred_th_up-0.1)
                ############################生成信号txt文件####################################
                # process_singal 为True生成信号txt文件
                signal_process_dir = get_backtest_path(SYMBOL, process_singal=True, online_path=False,
                                                       exp_name=exp_name, version_alias=version_alias,
                                                       label_name=label_name, pred_th_up=pred_th_up,
                                                       pred_th_dw=pred_th_dw)

                rt = f"/dfs/group/800657/exp_results/exp_l3_zzkc_flying4/{version_alias}/LabelFirstPeak_th12_60s-{SYMBOL}"
                print("信号路径：", signal_process_dir)
                time.sleep(5)
                ############################开始策略回测####################################
                trade_result_path = os.path.join("/dfs/group/800657/tmp/", f"{SYMBOL}-{uuid.uuid1()}/")
                ats_main(SYMBOL, signal_process_dir, trade_result_path, param_json_path, start_date = "2024-04-26", end_date = "2024-06-13")
                trade_excel_path = os.path.join(os.path.dirname(signal_process_dir), "STARDynamicStopProfitSubStrategy")
                os.makedirs(trade_excel_path, exist_ok=True)
                os.system(f"mv {trade_result_path}/*.xlsx {trade_excel_path} && rm -r " )
                print("ATSQtuat休息一下，不要走开")
