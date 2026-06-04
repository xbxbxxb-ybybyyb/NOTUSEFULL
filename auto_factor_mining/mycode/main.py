import sys
from os import path
import os 
import math
import datetime
import warnings
warnings.filterwarnings('ignore')

from gplearn_my.genetic import SymbolicTransformer
from data.eval_data import parallel_evaluate_data
import argparse
import numpy as np
import pandas as pd
import time
import json
import pickle
import logging
from recorder import init_logging
from xquant.factordata import FactorData
from pdf_and_excel import *
s = FactorData()

def data_selection(time_sta,time_end, all_data, fac_name, target):
    """
        从全量数据中筛选部分数据作为训练集，OOS，验证，测试
        input：
           time_sta: 获取日期开始
           time_end: 获取日期结束
           all_data: 传入的全量数据
           fac_name: 所需列名（因子）
           target：  标的
    """
    day = s.tradingday(time_sta, time_end)
    day = [int(i) for i in sorted(day)]
    df = all_data[all_data.index.get_level_values(0).isin(day)]
    X_arr = np.nan_to_num(df[fac_name].copy())
    y_arr = np.nan_to_num(df[target].copy())    
    return X_arr, y_arr, df.index

def train_est(all_data, json_file, save_root_dir, decap_file):
    """
        遗传因子挖掘训练部分
        input：
           json_file: 配置文件路径
           all_data: 传入的全量数据
           save_root_dir: 保存文件的根路径
        return：
           est_gp
    """
    save = False
    restrict = False
    with open(json_file, 'r') as f:
        setup_json = json.load(f)
        f.close()

    logger.info(str(setup_json))

    fac_name = setup_json['factor_name']
    fac_para = setup_json['fac_para']
    time_sta = str(setup_json["data_info"]["train"][0]) 
    time_end = str(setup_json["data_info"]["train"][1])
    print("Train time period: ", time_sta, time_end)
    assert len(fac_name) == len(fac_para)
    print('fac_name',fac_name)    
    target = '1Day_return'

    #X_train_arr, y_train_arr, data_index = data_selection('20151201', '20151220', all_data, fac_name,target)  
    X_train_arr, y_train_arr, data_index = data_selection(time_sta, time_end, all_data, fac_name,target)  
    print('训练总数:' , len(X_train_arr))  
    function_set = setup_json['function_set']
    target = '1Day_return'
    
    est_gp = SymbolicTransformer(
                            feature_names = fac_name, 
                            function_set = function_set,
                            generations = setup_json['generation'],
                            n_components = setup_json['n_components'],
                            population_size = setup_json['population'],
                            hall_of_fame = setup_json['hall_of_fame'],
                            tournament_size = setup_json['tournament_size'], 
                            random_state = setup_json['random_state'],
                            verbose=2,
                            metric="apearson",
                            init_depth=eval(setup_json['init_depth']),
                            init_method=setup_json['init_method'],
                            parsimony_coefficient=setup_json["parsimony_coefficient"], # 0.004 
                            #parsimony_coefficient = 'auto',
                            p_crossover =setup_json['p_crossover'],
                            p_subtree_mutation = setup_json['p_subtree_mutation'],
                            p_hoist_mutation = setup_json['p_hoist_mutation'],
                            p_point_mutation = setup_json['p_point_mutation'],
                            p_point_replace = setup_json['p_point_replace'],
                            n_jobs = setup_json['n_jobs'],
                            const_range= None, 
                            warm_start=False,
                            low_memory=True,
                            stopping_criteria = 1,
                            decap_file = decap_file,
                            restrict_type=restrict,
                            terminal_types=fac_para
                         )         
    # Start training
    time1 = time.time()
    est_gp = est_gp.fit(X_train_arr, y_train_arr, more_params={"min_expression_len": 3, "data_index": data_index})
    print(est_gp)
    print(est_gp._best_programs[0])
    time2 = time.time()
    print('耗时:' + str((time2-time1)/3600) + 'h')

    file_name = json_file.split('/')[-1].split('.')[0]
    try:
        if not os.path.exists(save_root_dir+ file_name):
            os.mkdir(save_root_dir+ file_name)
        with open(save_root_dir + file_name + '/formula.pkl' , 'wb') as f:
            pickle.dump(est_gp, f)
        print('保存成功：' + save_root_dir + file_name + '/formula.pkl')
    except:
        print('保存失败,返回est_gp')    
    return est_gp

def evaluate(all_data, json_file, est_gp, save_path, decap_file):  
    with open(json_file, 'r') as f:
        setup_json = json.load(f)
    fac_name = setup_json['factor_name']
    target = '1Day_return'

    time_sta = str(all_data.index[0][0])
    time_end = str(all_data.index[-1][0])
    
    X, y, index = data_selection(time_sta, time_end, all_data, fac_name, target)

    save_path = save_path + json_file.split('/')[-1].split('.')[0]
    print('save evaluate parquet to',save_path)
    result = parallel_evaluate_data(est_gp, decap_file, X, y, index,  
                                        save_path, save=True, 
                                        n_jobs=-1)
    # n_jobs=math.ceil(setup_json['n_jobs']/2)
    return result

if __name__ == '__main__':
    start_time = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_path",  help="please specify json file path")
    parser.add_argument("--data_path",  help="please specify json data path")
    parser.add_argument("--save_path",  help="please specify json save path")    
    parser.add_argument("--decap_file", help="please specify decap_file path")        
    args = parser.parse_args()
    print('###############################################')
    print(args.json_path)
    print(args.data_path)
    print(args.save_path)
    print(args.decap_file)

    # json_path = "../setup/gplearn_config/param.json"
    # save_path = "../factor_result/"
    # data_path = "../data/all_data.parquet"
    # decap_file = "../data/decap_file.parquet"
    # python3
    # main.py - -json_path ${json_path} - -data_path ${data_path} - -save_path ${save_path} - -decap_file ${decap_file}


    if not os.path.exists(args.save_path):
        os.mkdir(args.save_path)

    # today_date = datetime.datetime.now().strftime("%Y%m%d")
    # result_path = args.save_path + today_date + '/'

    result_path = args.save_path + args.json_path.split('/')[-1].split('.')[0] + '/'
    # if not os.path.exists(result_path):
    #     os.mkdir(result_path)


    logger = init_logging('../logger/logger.log')
    logger.info('初始化日志')

    # process init data
    print("启动数据加载！")
    df1 = pd.read_parquet(args.data_path).reset_index()
    trading_day = list(set(df1['mddate']))
    stock_list = list(set(df1['stock'])) 
    df1['mddate'] = df1['mddate'].astype('int64')
    print('数据总数: %d 股票总数: %d 交易日总数：%d'  %(len(df1), len(stock_list), len(trading_day)))  
    df1 = df1.set_index(['mddate','stock'])
    df1 = df1.fillna(0)
    print("Load data successfully from", args.data_path)
    print("完成数据加载！")

    print("遗传规划生成因子基于训练集训练启动！")
    est_gp = train_est(df1, args.json_path, args.save_path, args.decap_file)
    decap_file = est_gp.decap_file
    # print（decap_file）
    print("遗传规划生成因子基于训练集训练完成！")

    # eval
    factor_info = evaluate(df1, args.json_path, est_gp, args.save_path, decap_file)
    print("factor_info", factor_info)

    # train

    # report
    with open(args.json_path, 'r') as f:
        setup_json = json.load(f)
        f.close()
    data_info = setup_json["data_info"]
    factor_info = summary(est_gp, decap_file, result_path, 10, df1, data_info, factor_info)

    # 剪枝
    est_gp.decap_file = []
    save_path = args.save_path + args.json_path.split('/')[-1].split('.')[0] + '/formula.pkl'
    with open(save_path , 'wb') as f:
        pickle.dump(est_gp, f)
    print('保存成功：' + save_path)