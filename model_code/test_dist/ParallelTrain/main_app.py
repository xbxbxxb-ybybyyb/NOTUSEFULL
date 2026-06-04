try:
    from sklearn.externals.joblib import Parallel, delayed
except:
    from joblib import Parallel, delayed
# from xquant.compute.aimr import AIMR
import sys
import os
from DataAPI.DataToolkit import *


import pandas as pd



def cmd_help(t, path):
    """
    :param t: model_config_dict
    :param path:  多组计算数据任务
    :return:
    """
    os.system('python3 '+'./ParallelTrain/update_single_model.py '+str(t)+' '+path)

    # sys.path.insert(0, 'ParallelTrain/')
    # os.system('python3 '+'./ParallelTrain/update_single_model.py '+str(t)+' '+path)


def parallel_run_model(model_para_dict, config_data_path, config_data_name, num_threads=3, multi_process=True):
    def get_key_by_value(s_dict, value):
        return [k for k, v in s_dict.items() if v == value]
    model_list = model_para_dict.keys()
    model_config_list = []
    for model in model_list:
        test_start_date = model_para_dict[model]['start_date']
        test_end_date = model_para_dict[model]['end_date']
        update_model_period = model_para_dict[model]['update_model_period']
        train_test_map = get_train_test_map(test_start_date, test_end_date, update_model_period)
        train_date_list = sorted(list(set([v for k, v in (train_test_map.items())])))
        print('Train model:{}\nTrain date:{}'.format(model_para_dict[model]['model_name'], train_date_list))
        for train_date in train_date_list:
            strategy_type_list = model_para_dict[model]['times']
            for strategy_type in strategy_type_list:       
                model_config = {'model_file': model,
                                'model_para': model_para_dict[model],
                                'train_date': train_date,
                                'strategy_type': strategy_type,
                                'predict_date_list': get_key_by_value(train_test_map, train_date)}

                model_config_list.append(model_config)
                   
    model_config_dict = dict(zip(np.arange(len(model_config_list)), model_config_list))
    if not os.path.exists(config_data_path+'/config_data/'):
        os.makedirs(config_data_path+'/config_data/')
    map_config_path = config_data_path+'/config_data/map_config_dict_'+config_data_name+'_'+str(time.time())+'.pkl'
    pd.to_pickle(model_config_dict, map_config_path)
    print('###########Train#############')
    if multi_process:
        Parallel(num_threads)(delayed(cmd_help)(k, map_config_path) for k in model_config_dict)
    else:
        from ParallelTrain.update_single_model import update_single_model
        for k in model_config_dict:
            update_single_model(model_config_dict[k])
    return model_config_dict


def get_train_test_map(start_date, end_date, update_model_period):
    trading_day = get_trading_day(start_date, end_date)
    trading_day_fri = get_friday_trading_days(start_date, end_date)
    trading_day = get_trading_day(trading_day_fri[0], trading_day[-1])
    i_1 = 0
    train_test_map = {}
    temp_train_date = trading_day[0]
    for i in range(trading_day.__len__()-1):
        if i == 0 or (trading_day[i] in trading_day_fri and i - i_1 >= update_model_period):
            i_1 = i
            temp_train_date = trading_day[i]
        train_test_map.update({trading_day[i+1]: temp_train_date})
    return train_test_map


def main():
    # param = eval(AIMR.getParam())
    test_start_date = 20200111
    test_end_date = 20200217
    update_model_period = 5
    times = ['vwap']
    addressManagement = AddressManagement(x_cloud=True)
    root_path =  "/tmp/012620/own/Apollo/StrategySelectStockDay"
    config_data_name = 'test'

    fs = pd.read_pickle("factor_list.pkl")
    # factor_file_name = 'factor_algo.xlsx'
    # factor_dir = addressManagement.get_root() + "/Apollo/Stocklist/"
    factor_dict = {}
    for time_ in times:
        # test_factor = list(pd.read_excel(factor_dir + factor_file_name, sheet_name=time_, header=None).values.flatten())
        factor_dict[time_] = fs
    #LinearRegression,XgbSP
    model_para_dict = {'XgbSP': {'start_date': test_start_date,
                                            'end_date': test_end_date,
                                            'update_model_period': update_model_period,
                                            'times': times,
                                            'root_path': root_path,
                                            'factor_dict': factor_dict,
                                            'label_name': 'vwap_re',
                                            'gap': 5,
                                            'model_name': 'XgbSP_test',
                                            'train_window': 240,
                                            'sample': True,
                                            'train_flag': True,
                                            'check_model': True}}

    parallel_run_model(model_para_dict, config_data_path=root_path, config_data_name=config_data_name, num_threads=2, multi_process=False)


if __name__ == '__main__':
    main()
