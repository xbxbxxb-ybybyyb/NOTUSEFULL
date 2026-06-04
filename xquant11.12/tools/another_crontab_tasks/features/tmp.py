import os
import json
import sys
import time
from AutoMiningFrame.DataCaculation.entry.FactorCalcBatch import calc_factors_by_config
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
import argparse
import pandas as pd
import ray


def create_factor_config(file_path, config_path, factor_list=None):
    res_dict = {}
    a = open(config_path, 'w')
    # path = os.path.join(os.path.dirname(__file__), "../factors/InfoTech/StockMMRetV1Factors")
    # path = "../factors/InfoTech/StockMMRetV1Factors"

    path = file_path
    for root, dir, files in os.walk(path):
        for file in files:
            content = open(os.path.join(root, file), "r").read()
            # 过滤因子条件1： L2P中缺失的字段
            if "M_NumOfferOrders" in content or "M_NumBidOrders" in content or "SellCount" in content or "BuyCount" in content or 'M_NumTrades' in content:
                print("{}因子无法参与L2p计算！".format(file[:-4]), content)
                continue
            # if file.startswith("FactorT") and file[7].isupper():
            #     continue
            # if not file.startswith("Factor"):
            #     continue

            if factor_list:
                if file[:-4] in factor_list:
                    res_dict[file[:-4]] = [{}]
            else:
                res_dict[file[:-4]] = [{}]
    a.write(json.dumps(res_dict))
    a.close()
    print("配置文件：factor_config.json 已生成！")


def update_factordata(start_date, end_date, target_securities=None, return_mode="show",
                      study_scenario="stock", config_path = None, file_path = None, non_factor_path=None, user_id="016869",
                      factor_type="factor"):
    if not isinstance(target_securities, list):
        raise Exception("参数target_securities为列表形式，如['688599.SH']，请重新输入！")
    # file_path_1 = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-2]), "factors/InfoTech")
    # file_path = os.path.join(file_path_1, "StockMMRetV1Factors")
    df = calc_factors_by_config(config_path, file_path, start_date, end_date,
                                target_securities, return_mode,
                                study_scenario=study_scenario,
                                non_factor_path=non_factor_path,
                                data_type='tick_l2p'
                                )
    print(df)
    fd = FactorProvider(user_id)
    # 更新存储个人因子库数据
    # fd.save_personal_data_to_dfs(res=df, factor_type=factor_type)
    fd.save_public_data_to_dfs(res=df, factor_type='factor', data_type='tick_l2p')


def update_labeldata(start_date, end_date, target_securities=None, return_mode="show",
                      study_scenario="stock", config_path = None, file_path = None, non_factor_path=None, user_id="016869",
                      factor_type="factor"):
    if not isinstance(target_securities, list):
        raise Exception("参数target_securities为列表形式，如['688599.SH']，请重新输入！")
    # file_path_1 = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-2]), "factors/InfoTech")
    # file_path = os.path.join(file_path_1, "StockMMRetV1Factors")
    df = calc_factors_by_config(config_path, file_path, start_date, end_date,
                                target_securities, return_mode,
                                study_scenario=study_scenario,
                                non_factor_path=non_factor_path,
                                data_type='tick_l2p'
                                )
    print(df)
    fd = FactorProvider(user_id)
    # 更新存储个人因子库数据
    # fd.save_personal_data_to_dfs(res=df, factor_type=factor_type)
    fd.save_public_data_to_dfs(res=df, factor_type='label', data_type='tick_l2p')


def main(target_securities, start_date, end_date, factor_list=None, calc_factor = True, calc_label = True):
    # 生成因子配置信息文件json格式
    if type(target_securities) == str:
        target_securities = [target_securities]

    return_mode = 'show'
    study_scenario = 'stock'
    # 存放NoneFactor的目录，本项目是把StockMMRetV1NoneFactor文件夹放入/home/appadmin/server/modules/并改名为NoneFactor
    # non_factor_path = "/home/appadmin/server/modules/NoneFactor"


    if False:
        factor_name_list = list(fd.load_info_from_dfs(factor_type, source_type=source_type, data_type="tick_l2p"))
        file_path = "/data/user/016869/online_scripts/shen/DolphindbFactors/factors/InfoTech/StockMMRetV1Factors"
        config_factor_path = "/data/user/016869/online_scripts/shen/DolphindbFactorsConfig/factor_config_all.json"
        non_factor_path = "/data/user/016869/online_scripts/shen/DolphindbFactors/factors/InfoTech/StockMMRetV1NoneFactor"
    else:
        config_factor_path = "/data/user/016869/online_scripts/shen/DolphindbFactorsConfig/factor_config_gai.json"
        file_path = "/data/user/016869/AutoMiningFrame/688536FactorNew"
        non_factor_path = "/data/user/016869/AutoMiningFrame/688536NoneFactor"
        create_factor_config(file_path, config_factor_path)
        factor_name_list = list(json.load(open(config_factor_path, "r")).keys())

    if calc_factor:
        update_factordata(start_date, end_date, target_securities=target_securities, return_mode=return_mode,
                          study_scenario=study_scenario, config_path=config_factor_path, file_path = file_path, non_factor_path=non_factor_path)
    if calc_label:
        lable_name_list = ['LabelFirstPeak_th10_60s_OnlyUp', 'LabelFirstPeak_th10_120s_OnlyDw',
                           'LabelFirstPeak_th10_60s', 'LabelFirstPeak_th15_120s',
                           'LabelFirstPeak_th15_120s_OnlyDw', 'LabelReferenceMidPx',
                           'LabelFirstPeak_th10_60s_OnlyDw', 'LabelFirstPeak_th10_120s',
                           'LabelFirstPeak_th20_240s_OnlyDw', 'LabelFirstPeak_th15_120s_OnlyUp',
                           'LabelFirstPeak_th20_240s', 'LabelFirstPeak_th20_240s_OnlyUp',
                           'LabelFirstPeak_th10_120s_OnlyUp']

        label_file_path = "/data/user/013150/online_scripts/shen/DolphindbFactors/labels/InfoTech/Factors"
        label_non_factor_path = "/data/user/013150/online_scripts/shen/DolphindbFactors/labels/InfoTech/NoneFactors"
        config_label_path = "/data/user/016869/online_scripts/shen/DolphindbFactorsConfig/label_config_gai.json"
        create_factor_config(label_file_path, config_label_path)

        update_labeldata(start_date, end_date, target_securities=target_securities, return_mode=return_mode,
                          study_scenario=study_scenario, config_path=config_label_path, file_path=label_file_path, non_factor_path=label_non_factor_path)



def load_factor_label_data(target_securities, factor_name_list):
    user_id = '016869'
    fd = FactorProvider(user_id)
    factor_type = 'factor'
    source_type = 'public'
    start_time, end_time = "20200102", "20230630"
    # # 先读取公共库中已存在的因子列表

    factor_df = fd.load_public_data_from_dfs(symbol=target_securities, factor_list=factor_name_list,
                                             start_time=start_time, end_time=end_time, factor_type=factor_type,
                                             data_type='tick_l2p')
    label_df = fd.load_public_data_from_dfs(symbol=target_securities, factor_list=["LabelFirstPeak_th10_120s"],
                                            start_time=start_time, end_time=end_time, factor_type="label",
                                            data_type='tick_l2p')  # 更新存储个人因子库数
    return factor_df, label_df



if __name__ == "__main__":
    if False:
        parser = argparse.ArgumentParser()
        parser.add_argument('-t', '--target_securities', nargs="+", default="688599.SH", type=str,
                            help='input the stock list')
        parser.add_argument('-s', '--start_date', default="20200301", type=str, help='input the start date')
        parser.add_argument('-e', '--end_date', default="20230301", type=str, help='input the end date')
        parser.add_argument('-f', '--factor_list', nargs="+", default=None, type=str, help='input the factor list')

        args = parser.parse_args()
        start_date = args.start_date
        end_date = args.end_date
        factor_list = args.factor_list
        target_securities = args.target_securities

    else:
        start_date =  "20200101"
        end_date = "20231031"
        factor_list = None
        target_securities = [
                            "688008.SH",
                            "688036.SH",
                            "688111.SH",
                            "688012.SH",
                            "603019.SH",
                            "688599.SH",
                            "688981.SH",
                            "688256.SH",
                            "688777.SH",
                            # "000858.SZ",
                            # "002594.SZ",
                            # "002230.SZ",
                            # "000977.SZ",
        ]


    assert target_securities, "target_securities 不能为空"
    assert type(start_date) == str, "开始日期不为空，且必须是str"
    assert type(end_date) == str, "结束日期不为空，且必须是str"
    if False:
        # 计算因子数据
        target_securities = ["688012.SH"]
        for target_security in target_securities:
            main(target_securities=[target_security], start_date=start_date, end_date=end_date, factor_list=factor_list, calc_factor=False,  calc_label=True)
    if True:
        # 评价因子数据
        from artifacts import factor_save_and_evaluate
        import json
        start_date, end_date = "20200102", "20230630"
        config_factor_path = "/data/user/016869/online_scripts/shen/DolphindbFactorsConfig/factor_config_gai.json"
        factor_name_list = list(json.load(open(config_factor_path, "r")).keys())

        for target_security in target_securities:
            factor_df, label_df = load_factor_label_data([target_security], factor_name_list)

            if "timestamp" in factor_df.columns:
                factor_df = factor_df.set_index("timestamp")
            if "timestamp" in label_df.columns:
                label_df = label_df.set_index("timestamp")

            factor_label_df = pd.concat([factor_df, label_df], axis=1)
            result = factor_save_and_evaluate.factor_eval_save_to_dolphindb(factor_label_df,
                                                                            label="LabelFirstPeak_th10_120s",
                                                                            factor_list=factor_name_list,
                                                                            start_date=start_date,
                                                                            end_date=end_date)
            result.to_parquet("/data/user/013150/exp_result/ALL_SYMBOL/{}_all_factor_stats_df.parquet".format(target_security))
