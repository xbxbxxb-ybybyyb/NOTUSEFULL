import sys
from DataAPI.DataToolkit import *
from ParallelTrain.config_path import *
from ParallelTrain.model.LinearRegression import *
from ParallelTrain.model.XgbSP import *



import time
import pandas as pd
import os
from ParallelTrain import update_sample


def update_single_model(model_config):
    model_file = model_config['model_file']
    root_path = model_config['model_para']['root_path']
    train_date = model_config['train_date']
    model_name = model_config['model_para']['model_name']
    strategy_type = model_config['strategy_type']
    train_flag = model_config['model_para']['train_flag']
    check_model = model_config['model_para']['check_model']
    gap = model_config['model_para']['gap']
    train_window = model_config['model_para']['train_window']
    sample = model_config['model_para']['sample']
    factor_list = model_config['model_para']['factor_dict'][strategy_type]
    predict_date_list = model_config['predict_date_list']
    label_name = model_config['model_para']['label_name']

    root_model_path = root_path+'/{}/Model_File_{}_{}/ModelSaved'.format(strategy_type, model_name, strategy_type)
    root_predict_path = root_path+'/{}/Model_File_{}_{}/SignalFile'.format(strategy_type, model_name, strategy_type)

    if not os.path.exists(root_model_path):
        os.makedirs(root_model_path)
    if not os.path.exists(root_predict_path):
        os.makedirs(root_predict_path)

    params = model_config['model_para']
    params.update({'model_path': root_model_path,
                   'prediction_path': root_predict_path,
                   'strategy_type': strategy_type,
                   'factor_list': factor_list})

    execstr = model_file+'(params)'
    model = eval(execstr)
    if train_flag:
        model_retrain_date = get_n_days_off(train_date, -gap-train_window)[:-gap]
        time_start = time.time()
        print('{}_{}_{} training begins at {}'.format(model_name, strategy_type, train_date, time.asctime(time.localtime(time_start))))
        if check_model:
            if os.path.exists('{}/{}_{}_{}.pickle'.format(root_model_path, model_name, strategy_type, train_date)):
                print('model exist:', '{}/{}_{}_{}.pickle'.format(root_model_path, model_name, strategy_type, train_date))
            else:
                if not sample:
                    model.get_model(model_retrain_date, train_date)
                else:
                    print(model_retrain_date)
                    sample_data = update_sample.load_sample(factor_list, model_retrain_date, strategy_type, label_name, gap)
                    model.get_model(sample_data, train_date)
        else:
            if not sample:
                model.get_model(model_retrain_date, train_date)
            else:
                sample_data = update_sample.load_sample(factor_list, model_retrain_date, strategy_type, label_name, gap)
                model.get_model(sample_data, train_date)
        time_end = time.time()
        print('{}_{}_{} training ends at {} and lasts {} min'.format(model_name, strategy_type, train_date, time.asctime(time.localtime(time_end)), int((time_end-time_start)/60)))
    if len(predict_date_list) > 0:
        time_start = time.time()
        print('{}_{}_{} predicting begins at {}'.format(model_name, strategy_type, train_date, time.asctime(time.localtime(time_start))))
        for today_date in predict_date_list:
            sample_data = update_sample.load_sample(factor_list, [today_date], strategy_type, label_name, gap)
            model.label_predict(sample_data, train_date, today_date)
        time_end = time.time()
        print('{}_{}_{} predicting ends at {} and lasts {} min'.format(model_name, strategy_type, train_date, time.asctime(time.localtime(time_end)), int((time_end - time_start) / 60)))


if __name__ == '__main__':
    # map_config = pd.read_pickle('/data/user/054703/Apollo/StrategySelectStockIntraDay/config_data/map_config_dict_test_1629388975.9146445.pkl')
    # update_single_model(map_config[0])
    map_config = pd.read_pickle(sys.argv[2])
    update_single_model(map_config[int(sys.argv[1])])
