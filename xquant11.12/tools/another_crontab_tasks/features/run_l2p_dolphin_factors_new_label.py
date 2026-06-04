import os
import json
import sys
import time
from AutoMiningFrame.DataCaculation.entry.FactorCalcBatch import calc_factors_by_config
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
import argparse
import pandas as pd
import ray


def create_factor_config(file_path, config_path, factor_list=None, factor_list_except = []):
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
            if file.startswith("FactorT") and file[7].isupper():
                continue
            # if not file.startswith("Factor"):
            #     continue

            if factor_list:
                if file[:-4] in factor_list:
                    # 选中因子
                    res_dict[file[:-4]] = [{}]
            else:
                # 剔除因子
                if file[:-4] not in factor_list_except:
                    res_dict[file[:-4]] = [{}]


    a.write(json.dumps(res_dict))
    a.close()
    print("配置文件：factor_config.json 已生成！")


def update_factordata(start_date, end_date, target_securities=None, return_mode="show",
                      study_scenario="stock", config_path=None, file_path=None, non_factor_path=None, user_id="016869",
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
    fd.save_public_data_to_dfs(res=df, factor_type=factor_type, data_type='tick_l2p')


def update_labeldata(start_date, end_date, target_securities=None, return_mode="show",
                     study_scenario="stock", config_path=None, file_path=None, non_factor_path=None, user_id="016869",
                     factor_type="factor"):
    if not isinstance(target_securities, list):
        raise Exception("参数target_securities为列表形式，如['688599.SH']，请重新输入！")
    # file_path_1 = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-2]), "factors/InfoTech")
    # file_path = os.path.join(file_path_1, "StockMMRetV1Factors")
    print(111111111111111111)
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


def main(target_securities, start_date, end_date, factor_list=None, calc_factor=True, calc_label=True):
    # 生成因子配置信息文件json格式
    if type(target_securities) == str:
        target_securities = [target_securities]

    return_mode = 'show'
    study_scenario = 'stock'
    # 存放NoneFactor的目录，本项目是把StockMMRetV1NoneFactor文件夹放入/home/appadmin/server/modules/并改名为NoneFactor
    # non_factor_path = "/home/appadmin/server/modules/NoneFactor"

    if True:
        # 去除改量纲的因子
        config_factor_path = "/data/user/016869/online_scripts/shen/DolphindbFactorsConfig/factor_config_gai.json"
        factor_name_list = list(json.load(open(config_factor_path, "r")).keys())

        file_path = "/data/user/016869/online_scripts/shen/DolphindbFactors/factors/InfoTech/StockMMRetV1Factors"
        config_factor_path = "/data/user/016869/online_scripts/shen/DolphindbFactorsConfig/factor_config_all.json"
        non_factor_path = "/data/user/016869/online_scripts/shen/DolphindbFactors/factors/InfoTech/StockMMRetV1NoneFactor"
        create_factor_config(file_path, config_factor_path, factor_list_except=factor_name_list)
        factor_name_list = list(json.load(open(config_factor_path, "r")).keys())
        print("factor_list:", len(factor_name_list))
        time.sleep(5)
    else:
        config_factor_path = "/data/user/016869/online_scripts/shen/DolphindbFactorsConfig/factor_config_gai.json"
        file_path = "/data/user/016869/AutoMiningFrame/688536FactorNew"
        non_factor_path = "/data/user/016869/AutoMiningFrame/688536NoneFactor"
        create_factor_config(file_path, config_factor_path)
        factor_name_list = list(json.load(open(config_factor_path, "r")).keys())

    if calc_factor:
        update_factordata(start_date, end_date, target_securities=target_securities, return_mode=return_mode,
                          study_scenario=study_scenario, config_path=config_factor_path, file_path=file_path,
                          non_factor_path=non_factor_path)
    if calc_label:
        # lable_name_list = ['LabelFirstPeak_th10_60s_OnlyUp', 'LabelFirstPeak_th10_120s_OnlyDw',
        #                    'LabelFirstPeak_th10_60s', 'LabelFirstPeak_th15_120s',
        #                    'LabelFirstPeak_th15_120s_OnlyDw', 'LabelReferenceMidPx',
        #                    'LabelFirstPeak_th10_60s_OnlyDw', 'LabelFirstPeak_th10_120s',
        #                    'LabelFirstPeak_th20_240s_OnlyDw', 'LabelFirstPeak_th15_120s_OnlyUp',
        #                    'LabelFirstPeak_th20_240s', 'LabelFirstPeak_th20_240s_OnlyUp',
        #                    'LabelFirstPeak_th10_120s_OnlyUp']

        label_file_path = "/data/user/013150/online_scripts/shen/DolphindbFactors/labels/InfoTech/Factors"
        label_non_factor_path = "/data/user/013150/online_scripts/shen/DolphindbFactors/labels/InfoTech/NoneFactors"
        config_label_path = "/data/user/016869/online_scripts/shen/DolphindbFactorsConfig/label_config_gai_new_lable.json"
        # config_label_path = "/data/user/016869/online_scripts/shen/DolphindbFactorsConfig/label_config_gai.json"
        # 【注意】根据目录下标签生成配置文件
        #create_factor_config(label_file_path, config_label_path)

        update_labeldata(start_date, end_date, target_securities=target_securities, return_mode=return_mode,
                         study_scenario=study_scenario, config_path=config_label_path, file_path=label_file_path,
                         non_factor_path=label_non_factor_path)
    return config_factor_path


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


def connect_ddb(data_type):
    import dolphindb as ddb
    s = ddb.session()
    if data_type == 'tick_l2p':
        s.connect(host="168.17.249.172", port=8902, userid="admin", password="123456")
    elif data_type in ['enhanced_tick','enhanced_tick_norm']:
        s.connect(host="168.17.250.48", port=8902, userid="admin", password="123456")
    return s

def save_factor_analysis(analysis_res, stock, label_name, factor_name_list, data_type='tick_l2p'):
    cols = ['MDDate', 'test_factor', 'label', 'stock', 'valid_count', 'skew', 'kurt', 'factor_std', 'label_std',
            'normal_ic', 'rank_ic', 'auto_corr_1', 'auto_corr_3', 'auto_corr_5', 'corr', 'trade_long_return_0.1',
            'trade_short_return_0.1', 'long_p_value_0.1', 'short_p_value_0.1', 'trade_long_return_0.2',
            'trade_short_return_0.2',
            'long_p_value_0.2', 'short_p_value_0.2', 'stratified_trade_long_return_5',
            'stratified_trade_short_return_5',
            'stratified_long_p_value_5', 'stratified_short_p_value_5',
            'stratified_trade_long_return_10', 'stratified_trade_short_return_10', 'stratified_long_p_value_10',
            'stratified_short_p_value_10']
    analysis_res['stock'] = stock
    analysis_res = analysis_res[cols]
    analysis_res = analysis_res.rename(columns={'test_factor': 'factor_name', 'label': 'label_name'})
    analysis_res.columns = [i.replace(".", "") for i in analysis_res.columns]
    analysis_res['MDDate'] = analysis_res['MDDate'].astype(str)
    s = connect_ddb(data_type)
    if data_type in ['enhanced_tick', 'enhanced_tick_norm']:
        dbName = 'dfs://PublicData/analysisdata/EnhancedTick'
        if data_type == 'enhanced_tick':
            tbName = 'online_factor_analysis'
        else:
            tbName = 'online_norm_factor_analysis'

    elif data_type == 'tick_l2p':
        dbName = 'dfs://PublicData/analysisdata/EnhancedTickL2P'
        tbName = 'online_factor_analysis'

    s_date_dol = start_date[:4] + '.' + start_date[4:6] + '.' + start_date[6:]
    e_date_dol = end_date[:4] + '.' + end_date[4:6] + '.' + end_date[6:]
    s.upload({'analysis_res': analysis_res})
    # 判断是否已有数据
    script_check_data = f'''
    select count(*) from loadTable("{dbName}",`{tbName}) where MDDate in {s_date_dol}..{e_date_dol},stock=='{stock}',label_name=='{label_name}',factor_name in {factor_name_list}

    '''
    # print(script_check_data)
    cnt = s.run(script_check_data)

    if cnt.iloc[0, 0] > 0:
        print("先删除")
        script_delete = f'''
        delete from loadTable("{dbName}",`{tbName}) where MDDate in {s_date_dol}..{e_date_dol},stock=='{stock}',label_name=='{label_name}',factor_name in {factor_name_list}
        '''
        s.run(script_delete)
    print(analysis_res)
    save_data = f"""
        dbName = "{dbName}"
        tbName = `{tbName}
        tb = loadTable(dbName, tbName)
        analysis_res.replaceColumn!(`MDDate, temporalParse(analysis_res.MDDate, `yyyyMMdd))
        tb.append!(analysis_res)
    """
    s.run(save_data)
    return


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
        date = sys.argv[1]#"20240613"#datetime.now().strftime("%Y%m%d")
        start_date = date
        end_date = date
        # start_date = "20240603"
        # end_date = "20240603"
        #
        # start_date = "20240511"
        # end_date = "20240516"
        factor_list = None
        # target_securities = pd.read_csv("kc50.csv", header=None)[0].tolist()
        target_securities1 = pd.read_csv("kc_amt_swing.csv", header=None)[0].tolist()
        # target_securities = pd.read_csv("zz500.csv", header=None)[0].tolist()[44:]
        target_securities2 = pd.read_csv("zz500_select74_tmp.csv", header=None)[0].tolist()
        target_securities3 = pd.read_csv("/dfs/group/800657/exp_results/zz500_dataset/20240927110913_0_120.csv", header=None)[0].tolist()
        target_securities4 = pd.read_csv("/dfs/group/800657/exp_results/zz500_dataset/20240927110913_100_160.csv", header=None)[0].tolist()
        target_securities = sorted(list(set(target_securities1+target_securities2+target_securities3+target_securities4)))
        # target_securities = ["688256.SH"]
        # target_securities = ["688012.SH", "000977.SZ", "688981.SH", "688256.SH", "688111.SH"]

    assert target_securities, "target_securities 不能为空"
    assert type(start_date) == str, "开始日期不为空，且必须是str"
    assert type(end_date) == str, "结束日期不为空，且必须是str"
    if True:
        # 计算因子数据
        # ("20200101", "20201231"), ("20210101", "20211231")
        for target_security in target_securities:
            for start_date, end_data in [(start_date, end_date)]:#[("20210101", "20210630"), ("20210701", "20211231")]:#[ ("20220101", "20220630"), ("20220701", "20221231"), ("20230101", "20230630"),("20230701", "20231231")]:
                config_factor_path = main(target_securities=[target_security], start_date=start_date, end_date=end_date, factor_list=factor_list,
                     calc_factor=False, calc_label=True)
    if False:
        # 评价因子数据
        from artifacts import factor_save_and_evaluate
        import json

        start_date, end_date = "20210102", "20231230"
        # config_factor_path = "/data/user/016869/online_scripts/shen/DolphindbFactorsConfig/factor_config_gai.json"
        # config_factor_path = "/data/user/016869/online_scripts/shen/DolphindbFactorsConfig/factor_config_all.json"
        factor_name_list = list(json.load(open(config_factor_path, "r")).keys())

        for target_security in target_securities:
            factor_df, label_df = load_factor_label_data([target_security], factor_name_list)

            if "timestamp" in factor_df.columns:
                factor_df = factor_df.set_index("timestamp")
            if "timestamp" in label_df.columns:
                label_df = label_df.set_index("timestamp")

            factor_label_df = pd.concat([factor_df, label_df], axis=1)
            analysis_res = factor_save_and_evaluate.factor_eval_save_to_dolphindb(factor_label_df,
                                                                            label="LabelFirstPeak_th10_120s",
                                                                            factor_list=factor_name_list,
                                                                            start_date=start_date,
                                                                            end_date=end_date)
            save_factor_analysis(analysis_res, target_security, "LabelFirstPeak_th12_60s", factor_name_list, data_type='tick_l2p')
            # result.to_parquet(
            #     "/data/user/013150/exp_result/ALL_SYMBOL/{}_all_factor_stats_df.parquet".format(target_security))
