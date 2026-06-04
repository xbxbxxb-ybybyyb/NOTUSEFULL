import time
import ray
# sys.path.insert(0, "/data/user/013150/online_scripts/another_crontab_tasks")
# os.system("sh /data/user/013150/online_scripts/another_crontab_tasks/install.sh")
# os.system("sh /data/user/013150/online_scripts/another_crontab_tasks/start.sh")
from xquant.factordata import FactorData
from generate_parquet_utils import *
from artifacts.signal_evaluate import *
from generate_pdf import *


def main(symbol_list, start_date, end_date, flag_generate_parquet, flag_winloss, update_ret_flag):
    ray.init(num_cpus=20, local_mode=False, log_to_driver=True)
    model_type = "l2p"
    data_type = "tick_l2p"
    ################################################################################
    first_point = False
    if first_point:
        detail_base_dir = "/dfs/group/800657/library/tmp_l3_event/l3_signal_evaluate_mid_first"
    else:
        detail_base_dir = "/dfs/group/800657/library/tmp_l3_event/l3_signal_evaluate_mid"
    # pdf_save_base_dir = "/dfs/group/800657/self_winloss_data"

    for label_name, exp_name, version_alias in exp_list:
        if "l3" in exp_name and not "noflying" in version_alias:
            model_type = "l3"
        # TODO 为每个模型添加测试的标的
        if exp_name == "l2p_kc100_v1" and version_alias == "l2p_kc100_v1":
            symbol_list = ["688498.SH"]
        elif exp_name == "unite_kc" and version_alias == "unite_kc":
            symbol_list = ["688256.SH"]
            data_type = "enhanced_tick_norm"
        elif exp_name == "tick_kc_basket" and version_alias == "tick_kc_basket":
            symbol_list = ["688256.SH", "688981.SH", "688012.SH"]
            data_type = "enhanced_tick_norm"
        elif exp_name == "tick_688017.SH" and version_alias == "tick_688017.SH":
            symbol_list = ["688017.SH"]
            data_type = "enhanced_tick_norm"
        elif exp_name == "l2p_kc_basket" and version_alias == "l2p_kc_basket":
            symbol_list = ["688012.SH", "688390.SH", "688047.SH", "688271.SH", "688041.SH", "688256.SH"]
            # symbol_list = ["688012.SH", "688041.SH"]
        elif exp_name == "l2p_688981.SH_v1.1" and version_alias == "l2p_688981.SH_v1.1":
            symbol_list = ["688981.SH"]
        elif exp_name == "l2p_688111.SH_v1.1" and version_alias == "l2p_688111.SH_v1.1":
            symbol_list = ["688111.SH"]
        elif exp_name == "l2p_688036.SH" and version_alias == "l2p_688036.SH":
            symbol_list = ["688036.SH"]
        elif exp_name == "l2p_HS800_high" and version_alias == "l2p_HS800_high":
            symbol_list = ["002920.SZ", "300033.SZ", "300223.SZ", "300308.SZ", "300394.SZ", "300474.SZ", "300896.SZ"]
        elif exp_name == "l2p_HS800_low" and version_alias == "l2p_HS800_low":
            symbol_list = ["000977.SZ", "300418.SZ", "002281.SZ"]
        elif exp_name == "l2p_kc2_log" and version_alias == "l2p_kc2_log":
            symbol_list = ["688981.SH", "688012.SH", "688256.SH", "688047.SH", "688041.SH", "688017.SH", "688498.SH",
                            "688271.SH", "688052.SH", "688008.SH"]
            # symbol_list = ["688256.SH"]
        elif exp_name in ["signal_df_0802", "signal_df_0802_resnet"]:
            symbol_list = ["688981.SH", "688256.SH"]
        elif exp_name == "exp_l3_zzkc_flying4_levelone":
            symbol_list = ["688981.SH", "688012.SH", "688256.SH", "688047.SH", "688041.SH", "688017.SH", "688498.SH",
                            "688271.SH", "688052.SH", "688008.SH"]
        elif exp_name == "l3_zzkc_flying4_log2" and version_alias == "l3_zzkc_flying4_log2":
            symbol_list = ["688981.SH", "688012.SH", "688256.SH", "688047.SH", "688041.SH", "688017.SH", "688498.SH",
                            "688271.SH", "688052.SH", "688008.SH"]
        elif exp_name == "exp_l3_zzkc_flying4":
            symbol_list = ["688981.SH", "688012.SH", "688256.SH", "688047.SH", "688041.SH", "688017.SH", "688498.SH",
                        "688271.SH", "688052.SH", "688008.SH"]
        # elif exp_name == "KC_LabelFirstPeak_th10_60s_log":
        #     symbol_list = ["688271.SH", "688052.SH", "688012.SH", "688981.SH", "688017.SH", "688256.SH",
        #                    "688047.SH", "688041.SH", "688498.SH"]
        else:
            symbol_list = symbol_list

        ############################### 生成信号文件 l2p l3  ###############################
        fa = FactorData()
        t0 = time.time()
        today_date = time.strftime("%Y%m%d")
        if model_type=="l2p":
            model_file_type = "onnx"
            start_generate_and_evaluate_signal([[label_name, exp_name, version_alias]], symbol_list, start_date,
                                               end_date, model_file_type=model_file_type, data_type=data_type,
                                               winloss_save_path = None,
                                               flag_generate_parquet = flag_generate_parquet, flag_winloss = flag_winloss)
            print("start_generate_parquet_l2p spend {} s".format(time.time() - t0))
        elif model_type == 'l3':
            model_file_type = "pickle"
            start_generate_and_evaluate_signal([[label_name, exp_name, version_alias]], symbol_list, start_date, end_date,
                                               model_file_type=model_file_type, data_type=data_type,
                                               l3_flag=True, winloss_save_path = None,
                                               flag_generate_parquet=flag_generate_parquet, flag_winloss=flag_winloss
                                               )
            print("start_generate_parquet_l3 spend {} s".format(time.time() - t0))
        ############################### 信号评价 ###############################
        t0 = time.time()
        target_type = "mid"  # parse_target_type(label_name)
        if target_type == "mid":
            para = {
                "longMinTriggerRatio": 1.0,
                "shortMinTriggerRatio": -1.0,
                "longTriggerRatioPercentile": 99,
                "shortTriggerRatioPercentile": 1,
                "lossLimit": -0.005,
                "winLimit": 0.005,
                "target_type": "mid"
            }
        elif target_type == "longshort":
            para = {
                "longMinTriggerRatio": 1.0,
                "shortMinTriggerRatio": -1.0,
                "longTriggerRatioPercentile": 99,
                "shortTriggerRatioPercentile": 1,
                "lossLimit": -0.002,
                "winLimit": 0.0015,
                "target_type": "longshort"
            }
        else:
            raise Exception("target_type error: ", target_type)
        if update_ret_flag:
            main_grid_evaluate([[label_name, exp_name, version_alias]], symbol_list, target_type,
                           start_date, end_date, para,
                           base_dir=detail_base_dir, verbose=2,
                           first_point=False, flying_adjust=False)
            print("signal_evaluate spend {} s".format(time.time() - t0))
        ############################### 生成收益明细excle与评价pdf  ###############################
            pdf_save_base_dir = f"/dfs/group/800657/exp_results/{exp_name}/"
            genarate_pdf([[label_name, exp_name, version_alias]], symbol_list,
                     start_date, end_date,
                     input_base_dir=detail_base_dir,
                     save_base_dir = pdf_save_base_dir, weight_by_daynum = True)
    ray.shutdown()


if __name__ == "__main__":
    exp_list = [
        # #################################################################################
        # # （1）线上l3模型, 只用l3数据点进行预测 (柱状图紫色)
        # ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98_log2'),  # 对数底为2
        # # （2）新模型一： 增加多档突破事件点，选取l3数据点+30%非l3数据点训练  （柱状图蓝色）
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_zzkc_flying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_flying5_amp_log2'),
        # # （3）新模型二： 增加多档突破事件点+若干斜率因子，选取l3数据点+30%非l3数据点训练 （柱状图红色）
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_zzkc_flying5_levelone",  'LabelFirstPeakAdjust0_th12_60s_factor98_levelone_facevent_amp_log2'),
        # # （3）新模型三： l3数据点不加入训练，增加多档突破事件点，选取l3数据点+30%非l3数据点训练 （柱状图红色）
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_zzkc_flying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_zz500amt_levelone_noflying_log2'),
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_hs300_flying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_hs300_levelone_noflying_log2'),
        # ("LabelFirstPeakAdjust0_th12_60s", "exp_l3_hs300_flying5_levelone", 'LabelFirstPeakAdjust0_th12_60s_factor98_hs300_levelone_facevent_noflying_log2'),
        # ###############################20240828###################################
        # ("LabelFirstPeak_th05_60s", "exp_l3_hs300_flying5_levelone", 'LabelFirstPeak_th05_60s_factor98_hs300mid_levelone_flying5_log2'),
        # ("LabelFirstPeak_th10_120s", "exp_l3_hs300_flying5_levelone", 'LabelFirstPeak_th10_120s_factor98_hs300mid_levelone_flying5_log2'),
        # ###############################20240828###################################
        # ("LabelFirstPeak_th05_60s", "exp_l3_hs300_new_flying5_levelone", 'LabelFirstPeak_th05_60s_LabelFirstPeak_th05_60s_factor98_hs300_close60_levelone_flying5_log2_hs300_close60'),
        # ("LabelFirstPeak_th10_120s", "exp_l3_hs300_new_flying5_levelone", 'LabelFirstPeak_th10_120s_factor133_arbitrade0_120_log2_lr'),
        # ("LabelFirstPeak_th05_60s", "exp_l3_hs300_new_flying5_levelone", 'LabelFirstPeak_th05_60s_factor133_arbitrage0_120_log2_1r'),
        # ###############################20241002###################################
        # ###############################arbitrade0_120###################################
        # ("LabelFirstPeak_th10_120s_wap_th05", "exp_l3_hs300_new_flying5_levelone", 'LabelFirstPeak_th10_120s_wap_th05_factor133_arbitrade0_120_log2'),
        # ("LabelFirstPeak_th05_120s_wap", "exp_l3_hs300_new_flying5_levelone", 'LabelFirstPeak_th05_120s_wap_factor133_arbitrade0_120_log2'),
        ("LabelFirstPeakAdjust0_th10_60s", "exp_l3_hs300_new_flying5_levelone", 'LabelFirstPeakAdjust0_th10_60s_factor133_arbitrade0_120_log2'),
        ("LabelFirstPeak_th10_120s", "exp_l3_hs300_new_flying5_levelone",  'LabelFirstPeak_th10_120s_factor133_arbitrade0_120_log2'),
        ("LabelFirstPeak_th10_120s", "exp_l3_hs300_new_noflying5_levelone", 'LabelFirstPeak_th10_120s_factor133_arbitrade0_120_log2_noflying'),
        # ###############################arbitrade100_160###################################
        # ("LabelFirstPeak_th10_120s_wap_th05", "exp_l3_hs300_new_flying5_levelone", 'LabelFirstPeak_th10_120s_wap_th05_factor133_arbitrade100_160_log2'),
        # ("LabelFirstPeak_th10_120s", "exp_l3_hs300_new_flying5_levelone", 'LabelFirstPeak_th10_120s_factor133_arbitrade100_160_log2'),
        # # ("LabelFirstPeak_th05_120s_wap", "exp_l3_hs300_new_flying5_levelone",'LabelFirstPeak_th05_120s_wap_factor133_arbitrade100_160_log2')
        # ("LabelFirstPeak_th10_120s", "exp_l3_hs300_new_noflying5_levelone",'LabelFirstPeak_th10_120s_factor133_arbitrade100_160_log2_noflying'),
        # ("LabelFirstPeakAdjust0_th10_60s", "exp_l3_hs300_new_flying5_levelone",'LabelFirstPeakAdjust0_th10_60s_factor133_arbitrade100_160_log2')
    ]
    #########################  arbitrade0_120 #########################
    symbol_list = pd.read_csv("/dfs/group/800657/exp_results/zz500_dataset/20240927110913_0_120.csv", header=None)[0].tolist()
    #########################  arbitrade100_160 #########################
    # symbol_list = pd.read_csv("/dfs/group/800657/exp_results/zz500_dataset/20240927110913_100_160.csv", header=None)[0].tolist()
    #########################  close60 #########################
    # symbol_list = pd.read_csv("/dfs/group/800657/exp_results/zz500_dataset/hs300_select_close60.csv", header=None)[0].tolist()
    # symbol_list = pd.read_csv("/dfs/group/800657/exp_results/zz500_dataset/hs300_select_mid.csv", header=None)[0].tolist()

    # symbol_list = ["688981.SH", "688012.SH", "688256.SH", "688047.SH", "688041.SH", "688017.SH", "688506.SH","688498.SH",
    #                "688271.SH", "688052.SH", "688008.SH", "688390.SH", "688525.SH", "688036.SH", "688052.SH"]
    # symbol_list = ["688981.SH", "688012.SH", "688256.SH", "688047.SH", "688041.SH", "688017.SH", "688506.SH","688498.SH",
    #                "688271.SH"][:1]
    start_date = "2024-08-01"
    end_date = "2024-09-30"

    flag_generate_parquet = True
    flag_winloss = True
    update_ret_flag = False
    main(symbol_list, start_date, end_date, flag_generate_parquet= flag_generate_parquet,
         flag_winloss = flag_winloss,
         update_ret_flag = update_ret_flag)





