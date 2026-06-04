import os
import time
#os.system("sh /dfs/group/800657/COO/packages/install.sh")
#os.system('cp -r /dfs/group/800657/COO/packages/artifacts /opt/anaconda3/lib/python3.8/site-packages/')

def start_server():
#    os.system("""
#    curl ftp://168.8.2.68/016869/dolphin_server/start.sh -u "ftphzh:ftphzh2602" -O && sh start.sh
#    """)
    os.system("""
    cd /home/appadmin
    cp /dfs/group/800657/COO/packages/dolphin/dolphindb-1.30.21.1-cp38-cp38-manylinux_2_12_x86_64.manylinux2010_x86_64.whl ./
    pip install /home/appadmin/dolphindb-1.30.21.1-cp38-cp38-manylinux_2_12_x86_64.manylinux2010_x86_64.whl
    # update automining python sdk
    cp /dfs/group/800657/COO/packages/dolphin/automining-1.7.4.tar.gz ./
    pip install /home/appadmin/automining-1.7.4.tar.gz --no-deps
    # update Dolphindb server
    cp /dfs/group/800657/COO/packages/dolphin/DolphinDB_Linux64_V2.00.12.2.zip ./
    unzip -oq DolphinDB_Linux64_V2.00.12.2.zip
    # start dolphindb server
    cd server && chmod -R 777 dolphindb && cp /dfs/group/800657/COO/packages/dolphin/dolphindb.lic ./ && sh startSingle.sh $1 $2
    """)
    time.sleep(3)
    return

#start_server()


import ray
# sys.path.insert(0, "/data/user/013150/online_scripts/another_crontab_tasks")
# os.system("sh /data/user/013150/online_scripts/another_crontab_tasks/install.sh")
# os.system("sh /data/user/013150/online_scripts/another_crontab_tasks/start.sh")
from xquant.factordata import FactorData
from generate_parquet_utils import *
from artifacts.signal_evaluate import *
from generate_pdf import *
from artifacts.utils import load_model_config
from xquant.factordata import FactorData
import pandas as pd
import datetime as dt
import time
from data_move import data_sync


def main(exp_list, start_date, end_date, flag_generate_parquet, flag_winloss, flag_generate_percent_parquet,
         update_ret_flag, factor_type="real_factor", winloss_save_path=None):
    model_type = "l2p"
    ################################################################################
    first_point = False
    if first_point:
        detail_base_dir = "/dfs/group/800657/library/tmp_l3_event/l3_signal_evaluate_mid_first"
    else:
        detail_base_dir = "/dfs/group/800657/library/tmp_l3_event/l3_signal_evaluate_mid"

    # 计算信号文件
    if flag_generate_parquet:
        for label_name, exp_name, version_alias, symbol_list, data_type in exp_list:
            if "l3" in exp_name and not "noflying" in version_alias:
                model_type = "l3"
            model_path = f"/dfs/group/800657/exp_results/{exp_name}/{version_alias}/saved_models"
            # symbol_list = sorted(list(pd.read_json(os.path.join(model_path, "threshold.json")).keys()))
            #if version_alias not in ['HS_l2p']:
            #    continue
            ############################### 生成信号文件 l2p l3  ###############################
            t0 = time.time()
            if model_type=="l2p":
                model_file_type = "onnx"
                start_generate_signal([[label_name, exp_name, version_alias]], symbol_list, start_date, end_date,
                                      data_type=data_type, model_file_type=model_file_type,
                                      factor_type=factor_type)
                print("start_generate_signal_l2p spend {} s".format(time.time() - t0))
            elif model_type == 'l3':
                model_file_type = "pickle"
                start_generate_signal([[label_name, exp_name, version_alias]], symbol_list, start_date, end_date,
                                      data_type=data_type, model_file_type=model_file_type,
                                      l3_flag=True, factor_type=factor_type)
                print("start_generate_signal_l3 spend {} s".format(time.time() - t0))

    # 计算0阈值信号文件
    if flag_generate_percent_parquet:
        for label_name, exp_name, version_alias, symbol_list, data_type in exp_list:
            if "l3" in exp_name and not "noflying" in version_alias:
                model_type = "l3"
            #if version_alias not in ['HS_l2p']:
            #    continue
            #print(len(symbol_list))
            #symbol_list = symbol_list[450:]
            if model_type == "l2p":
                start_generate_percent_signal([[label_name, exp_name, version_alias]], symbol_list, start_date, end_date)
            elif model_type == 'l3':
                start_generate_percent_signal([[label_name, exp_name, version_alias]], symbol_list, start_date, end_date, l3_flag=True)

    # 信号止盈止损评价
    if flag_winloss:
        for label_name, exp_name, version_alias, symbol_list, data_type in exp_list:
            if "l3" in exp_name and not "noflying" in version_alias:
                model_type = "l3"
            model_path = f"/dfs/group/800657/exp_results/{exp_name}/{version_alias}/saved_models"
            # symbol_list = sorted(list(pd.read_json(os.path.join(model_path, "threshold.json")).keys()))
            ############################### 生成信号文件 l2p l3  ###############################
            #if version_alias not in ['HS_l2p']:
            #    continue
            t0 = time.time()
            if model_type=="l2p":
                start_evaluate_signal([[label_name, exp_name, version_alias]], symbol_list, start_date, end_date,
                                      winloss_save_path=winloss_save_path)
                print("start_evaluate_signal_l2p spend {} s".format(time.time() - t0))
            elif model_type == 'l3':
                start_evaluate_signal([[label_name, exp_name, version_alias]], symbol_list, start_date, end_date,
                                      l3_flag = True, winloss_save_path=winloss_save_path)
                print("start_evaluate_signal_l3 spend {} s".format(time.time() - t0))
        # ############################### 信号评价 ###############################
        # t0 = time.time()
        # target_type = "mid"  # parse_target_type(label_name)
        # if target_type == "mid":
        #     para = {
        #         "longMinTriggerRatio": 1.0,
        #         "shortMinTriggerRatio": -1.0,
        #         "longTriggerRatioPercentile": 99,
        #         "shortTriggerRatioPercentile": 1,
        #         "lossLimit": -0.005,
        #         "winLimit": 0.005,
        #         "target_type": "mid"
        #     }
        # elif target_type == "longshort":
        #     para = {
        #         "longMinTriggerRatio": 1.0,
        #         "shortMinTriggerRatio": -1.0,
        #         "longTriggerRatioPercentile": 99,
        #         "shortTriggerRatioPercentile": 1,
        #         "lossLimit": -0.002,
        #         "winLimit": 0.0015,
        #         "target_type": "longshort"
        #     }
        # else:
        #     raise Exception("target_type error: ", target_type)
        # if update_ret_flag:
        #     main_grid_evaluate([[label_name, exp_name, version_alias]], symbol_list, target_type,
        #                    start_date, end_date, para,
        #                    base_dir=detail_base_dir, verbose=2,
        #                    first_point=False, flying_adjust=False)
        #     print("signal_evaluate spend {} s".format(time.time() - t0))
        # ############################### 生成收益明细excle与评价pdf  ###############################
        #     pdf_save_base_dir = f"/dfs/group/800657/exp_results/{exp_name}/"
        #     genarate_pdf([[label_name, exp_name, version_alias]], symbol_list,
        #              start_date, end_date,
        #              input_base_dir=detail_base_dir,
        #              save_base_dir = pdf_save_base_dir, weight_by_daynum = True)
    ray.shutdown()


if __name__ == "__main__":
    tick2_stock_list = ['605168.SH', '605376.SH', '688146.SH']
    # exp_list = [
    #     # ###############################KG101###################################
    #     # ("LabelFirstPeak_th10_120s", "KG101_model",'HS_big'),
    #     # ("LabelFirstPeak_th10_120s", "KG101_model", 'HS_mid'),
    #     # ("LabelFirstPeak_th10_120s", "KG101_model", 'HS_sml'),
    #     # ("LabelFirstPeak_th10_120s", "KG101_model", 'HS_tick'),
    #     ("LabelFirstPeak_th10_120s", "KG101_model", 'HS_tick2_new'),
    #     # ("LabelFirstPeak_th10_120s", "KG101_model", 'HS_tick2_add'),
    # ]

    # data_type = "tick_l2p"
    # data_type = "enhanced_tick_norm"
    s = FactorData()
    cur_date = time.strftime("%Y%m%d")
    parse_date = s.tradingday(cur_date, -1)[0]

    time_now = dt.datetime.now().strftime("%H%M%S")
    print(time_now)
    if time_now[:2] < "16":
        start_date = end_date = s.tradingday(parse_date, -2)[0]
        start_date = pd.to_datetime(start_date).strftime("%Y-%m-%d")
        end_date = pd.to_datetime(end_date).strftime("%Y-%m-%d")
    else:
        start_date = end_date = pd.to_datetime(parse_date).strftime("%Y-%m-%d")
    start_date='2024-11-26'
    end_date = '2024-11-26'
    print(f"开始更新{start_date}-{end_date}的数据")
    ray.init(num_cpus=20, local_mode=False, log_to_driver=True)

    flag_generate_parquet = False
    flag_generate_percent_parquet = False
    flag_winloss = True
    update_ret_flag = False
    exp_config_list = load_model_config()
    winloss_save_path = "/dfs/group/800657/COO/StrategyBacktest/winloss_data/"
    # winloss_save_path = None
    main(exp_config_list, start_date, end_date, flag_generate_parquet= flag_generate_parquet,
         flag_winloss = flag_winloss,flag_generate_percent_parquet=flag_generate_percent_parquet,
         update_ret_flag = update_ret_flag, winloss_save_path=winloss_save_path)





