import os
import json
import sys
import time
from AutoMiningFrame.DataCaculation.entry.FactorCalcBatch import calc_factors_by_config
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
import argparse

def create_factor_config(factor_list=None):
    res_dict = {}
    a = open("factor_config_ct.json", 'w')
    path = os.path.join(os.path.dirname(__file__), "../factors/CentralTrading/CentralTradingMMFactors")

    for root, dir, files in os.walk(path):
        for file in files:
            if factor_list:
                if file[:-4] in factor_list:
                    res_dict[file[:-4]] = [{}]
            else:
                res_dict[file[:-4]] = [{}]
    a.write(json.dumps(res_dict))
    a.close()
    print("配置文件：factor_config_ct.json 已生成！")


def update_factordata(start_date, end_date, target_securities=None, return_mode="show",
                      study_scenario="stock", non_factor_path=None, user_id="016869",
                      factor_type="factor"):
    if not isinstance(target_securities, list):
        raise Exception("参数target_securities为列表形式，如['688599.SH']，请重新输入！")
    file_path_1 = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-2]), "factors/CentralTrading")
    config_path = "./factor_config_ct.json"
    file_path = os.path.join(file_path_1, "CentralTradingMMFactors")
    df = calc_factors_by_config(config_path, file_path, start_date, end_date,
                                 target_securities, return_mode,
                                 study_scenario=study_scenario,
                                 non_factor_path=non_factor_path)
    fd = FactorProvider(user_id)
    # 更新存储个人因子库数据
    #fd.save_personal_data_to_dfs(res=df, factor_type=factor_type)
    for stock in target_securities:
        print(stock)
        df_temp = df[df['M_HTSCSecurityID']==stock]
        fd.save_public_data_to_dfs(res=df_temp, factor_type='factor', data_type='enhanced_tick')
 
def main(target_securities, start_date, end_date, factor_list=None):
    # 生成因子配置信息文件json格式
    if type(target_securities)==str:
        target_securities = [target_securities]
    create_factor_config(factor_list=factor_list)
    return_mode = 'show'
    study_scenario = 'stock'
    # 存放NoneFactor的目录，本项目是把StockMMRetV1NoneFactor文件夹放入/home/appadmin/server/modules/并改名为NoneFactor
    #non_factor_path = "/home/appadmin/server/modules/NoneFactor"
    non_factor_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../factors/CentralTrading/CentralTradingNoneFactors/"))
    update_factordata(start_date, end_date, target_securities=target_securities, return_mode=return_mode,
                      study_scenario=study_scenario, non_factor_path=non_factor_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--target_securities', nargs="+", default="688599.SH", type=str, help='input the stock list')
    parser.add_argument('-s', '--start_date', default="20200301", type=str, help='input the start date')
    parser.add_argument('-e', '--end_date', default="20230301", type=str, help='input the end date')
    parser.add_argument('-f', '--factor_list', nargs="+", default=None, type=str, help='input the factor list')


    args = parser.parse_args()
    start_date = args.start_date
    end_date = args.end_date
    factor_list = args.factor_list
    target_securities = args.target_securities
    assert target_securities, "target_securities 不能为空"
    assert type(start_date)==str, "开始日期不为空，且必须是str"
    assert type(end_date)==str, "结束日期不为空，且必须是str"
        
    main(target_securities=target_securities, start_date=start_date, end_date=end_date, factor_list=factor_list)
