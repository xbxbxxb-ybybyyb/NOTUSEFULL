import datetime as dt
import numpy as np
import pandas as pd
import json
import shutil
import os
import io
import time
from xquant.pyfile import Pyfile


def log2signal(log_file_path, local_output_rootdir, config, date):
    py = Pyfile()
    if py.exists(local_output_rootdir):
        py.delete(local_output_rootdir, recursive=True)
    
    all_values = {}
    sid_sets = {}
    config_dict = {}
    for c in config:
        config_dict.update({c['model']: c})
        sid_sets.update({c['model']: {'non_univ': set(), 'universe': set()}})
        all_values.update({c['model']: {'non_univ': {}, 'universe': {}}})
    
    paused_sid = set()
    lines = py.read(log_file_path)
    f = py.open(log_file_path, 'rb')
    lines = f.read(10000000000)
    f.close()
    # print(lines[-50:])
    lines = lines.decode('UTF-8')
    # print(lines[-50:])
    # lines = lines.decode('UTF-8')
    lines = lines.split('\n')
    print('*** Last several lines in buffer: ***')
    print(lines[-3])
    print(lines[-2])
    print(lines[-1])
    last_line = ''
    for line in lines:
        try:
            s = line.index('[')
            e = line.index(']')
            sid = line[s + 1: e]
        except Exception as e:
            print('the last line is ' + last_line)
            continue
        last_line = line
        if 'Universe' in line:
            is_universe = line.split(':')[-1]
            if 'true' in is_universe:
                for model in sid_sets.keys():
                    if model + ',' in line:
                        sid_sets[model]['universe'].add(sid)
                        break
            else:
                for model in sid_sets.keys():
                    if model + ',' in line:
                        sid_sets[model]['non_univ'].add(sid)
                        break
        if 'Strategy Paused' in line:
            paused_sid.add(sid)
            continue
        if 'prediction_0' not in line:
            continue
        line = line.strip('\n')
        pieces = line.split('=')
        symbol = pieces[1].split(',')[0]
        time = pieces[2].split(',')[0]
        if time < '09:31:15':
            continue
        long_1min = float(pieces[3].split(',')[0])
        short_1min = float(pieces[4].split(',')[0])
        long_2min = float(pieces[5].split(',')[0])
        short_2min = float(pieces[6].split(',')[0])
        long_5min = float(pieces[7].split(',')[0])
        short_5min = float(pieces[8].split(';')[0])
        if sid in paused_sid:
            continue
           
        for model in sid_sets.keys():
            if sid in sid_sets[model]['non_univ']:
                if symbol not in all_values[model]['non_univ']:
                    all_values[model]['non_univ'].update({symbol: {'Timestamp': [], 'Ticktime': [], '1minLong': [], '1minShort': [], '2minLong': [],
                             '2minShort': [], '5minLong': [], '5minShort': []}})
                inner_dict = all_values[model]['non_univ'][symbol]
                timestamp = date + ' ' + time
                timestamp = dt.datetime.strptime(timestamp, '%Y%m%d %H:%M:%S').timestamp()
                inner_dict['Timestamp'].append(timestamp)
                inner_dict['Ticktime'].append(time)
                inner_dict['1minLong'].append(long_1min)
                inner_dict['1minShort'].append(short_1min)
                inner_dict['2minLong'].append(long_2min)
                inner_dict['2minShort'].append(short_2min)
                inner_dict['5minLong'].append(long_5min)
                inner_dict['5minShort'].append(short_5min)
            elif sid in sid_sets[model]['universe']:
                if symbol not in all_values[model]['universe']:
                    all_values[model]['universe'].update({symbol: {'Timestamp': [], 'Ticktime': [], '1minLong': [], '1minShort': [], '2minLong': [],
                             '2minShort': [], '5minLong': [], '5minShort': []}})
                inner_dict = all_values[model]['universe'][symbol]
                timestamp = date + ' ' + time
                timestamp = dt.datetime.strptime(timestamp, '%Y%m%d %H:%M:%S').timestamp()
                inner_dict['Timestamp'].append(timestamp)
                inner_dict['Ticktime'].append(time)
                inner_dict['1minLong'].append(long_1min)
                inner_dict['1minShort'].append(short_1min)
                inner_dict['2minLong'].append(long_2min)
                inner_dict['2minShort'].append(short_2min)
                inner_dict['5minLong'].append(long_5min)
                inner_dict['5minShort'].append(short_5min)
    # with open('5161001_quantity.json', 'r') as fj:
        # ori_qty = json.load(fj)
    # qtys = {}
    # for symbol in dict.keys():
        # qty = ori_qty['quantity'][symbol]
        # qtys.update({symbol: qty})

    # with open('quantities.json', 'w') as fj:
        # data = {'quantity': qtys}
        # json.dump(data, fj)
        
    for model in sid_sets.keys():
        for symbol in all_values[model]['non_univ'].keys():
            timestamps = np.array(all_values[model]['non_univ'][symbol]['Timestamp'])
            ticktimes = np.array(all_values[model]['non_univ'][symbol]['Ticktime'])
            long_1min = np.array(all_values[model]['non_univ'][symbol]['1minLong'])
            long_2min = np.array(all_values[model]['non_univ'][symbol]['2minLong'])
            long_5min = np.array(all_values[model]['non_univ'][symbol]['5minLong'])
            short_1min = np.array(all_values[model]['non_univ'][symbol]['1minShort'])
            short_2min = np.array(all_values[model]['non_univ'][symbol]['2minShort'])
            short_5min = np.array(all_values[model]['non_univ'][symbol]['5minShort'])
            full = [timestamps, ticktimes, long_1min, short_1min, long_2min, short_2min, long_5min, short_5min]
            full = np.array(full)
            full = full.transpose()
            data = pd.DataFrame(full,
                                columns=['Timestamp', 'Ticktime', '1minLong', '1minShort', '2minLong', '2minShort', '5minLong',
                                         '5minShort'])
            # data.drop_duplicates(subset=['Timestamp'], inplace=True)
            with py.open(local_output_rootdir + model + '/model/' + symbol + '/' + symbol + '_' + date + '.csv', 'wb') as fout:
                data.to_csv(fout, index=False)
        for symbol in all_values[model]['universe'].keys():
            timestamps = np.array(all_values[model]['universe'][symbol]['Timestamp'])
            ticktimes = np.array(all_values[model]['universe'][symbol]['Ticktime'])
            long_1min = np.array(all_values[model]['universe'][symbol]['1minLong'])
            long_2min = np.array(all_values[model]['universe'][symbol]['2minLong'])
            long_5min = np.array(all_values[model]['universe'][symbol]['5minLong'])
            short_1min = np.array(all_values[model]['universe'][symbol]['1minShort'])
            short_2min = np.array(all_values[model]['universe'][symbol]['2minShort'])
            short_5min = np.array(all_values[model]['universe'][symbol]['5minShort'])
            full = [timestamps, ticktimes, long_1min, short_1min, long_2min, short_2min, long_5min, short_5min]
            full = np.array(full)
            full = full.transpose()
            data = pd.DataFrame(full,
                                columns=['Timestamp', 'Ticktime', '1minLong', '1minShort', '2minLong', '2minShort', '5minLong',
                                         '5minShort'])
            with py.open(local_output_rootdir + model + '/universe/' + symbol + '/' + symbol + '_' + date + '.csv', 'wb') as fout:
                data.to_csv(fout, index=False)
        if all_values[model]['non_univ']:
            py.copyToShare(config_dict[model]['copy_to_hdfs_path_non_univ_hdfs'], local_output_rootdir + model + '/model/')
            # nfs_path = config_dict[model]['copy_to_share_path_non_univ_nfs']
            # if not os.path.exists(nfs_path):
                # os.mkdir(nfs_path)
            # if os.path.exists(nfs_path + date):
                # shutil.rmtree(nfs_path + date)
            # os.mkdir(nfs_path + date)
            # py.download(nfs_path + date, local_output_rootdir + model + '/model/')

        if all_values[model]['universe']:
            py.copyToShare(config_dict[model]['copy_to_hdfs_path_universe_hdfs'], local_output_rootdir + model + '/universe/')
            # nfs_path = config_dict[model]['copy_to_share_path_universe_nfs']
            # if not os.path.exists(nfs_path):
                # os.mkdir(nfs_path)
            # if os.path.exists(nfs_path + date):
                # shutil.rmtree(nfs_path + date)
            # os.mkdir(nfs_path + date)
            # py.download(nfs_path + date, local_output_rootdir + model + '/universe/')

def main():
    s_time = time.perf_counter()
    
    date = '20190826'
    #date = dt.datetime.strftime(dt.datetime.now().date(), '%Y%m%d')
    
    log_file_path = '$21/log/AlgoStrategy_{}.log'.format(date)
    # log_file_path = '$21/ProductionLogSignals/logs/AlgoStrategy_{}.log'.format(date)
    local_output_rootdir = 'TEMP2/' # 必须本地
    
    # config = [{'model': 'APPLE_NEW', 
    # 'copy_to_share_path_non_univ_hdfs': '$21/ProductionLogSignals/20190101_end/',
    # 'copy_to_share_path_universe_hdfs': '$21/ProductionLogSignals/universe/',
    # 'copy_to_share_path_non_univ_nfs': '/app/data/666888/ProductionSignals/',
    # 'copy_to_share_path_universe_nfs': '/app/data/666888/ProductionSignalsUniverse/'},
    # {'model': 'APPLE', 
    # 'copy_to_share_path_non_univ_hdfs': '$21/ProductionLogSignals/20190101_48_end/', 
    # 'copy_to_share_path_universe_hdfs': '$21/ProductionLogSignals/universe_new/',
    # 'copy_to_share_path_non_univ_nfs': '/app/data/666888/ProductionSignals/',
    # 'copy_to_share_path_universe_nfs': '/app/data/666888/ProductionSignalsUniverseNew/'}]

    config = [{'model': 'APPLE_NEW', 
    'copy_to_hdfs_path_non_univ_hdfs': 'ProductionLogSignals/20190101_end/',
    'copy_to_hdfs_path_universe_hdfs': 'ProductionLogSignals/universe/',
    'copy_to_share_path_non_univ_nfs': '/data/user/666888/ProductionSignals/',
    'copy_to_share_path_universe_nfs': '/data/user/666888/ProductionSignalsUniverse/'},
    {'model': 'APPLE', 
    'copy_to_hdfs_path_non_univ_hdfs': 'ProductionLogSignals/20190101_48_end/', 
    'copy_to_hdfs_path_universe_hdfs': 'ProductionLogSignals/universe_new/',
    'copy_to_share_path_non_univ_nfs': '/data/user/666888/ProductionSignals/',
    'copy_to_share_path_universe_nfs': '/data/user/666888/ProductionSignalsUniverseNew/'}]
    
    log2signal(log_file_path, local_output_rootdir, config, date)
    e_time = time.perf_counter()
    print('merging time: ' + str(round((e_time - s_time) / 60, 2)) + 'min')

if __name__ == '__main__':
    main()