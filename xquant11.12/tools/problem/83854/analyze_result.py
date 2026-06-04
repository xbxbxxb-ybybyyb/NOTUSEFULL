import os
import json
import Analyzer.TotalSummary as TotalSummary
import Analyzer.sta_daily as sta_daily
import Analyzer.summary_data as summary_data
import Analyzer.zip_model as zip_model
from xquant.pyfile import Pyfile


def remove_relative(path):
    if 'SHARE_21' in path:
        path = path.replace('SHARE_21', '$21')
    elif '$21' in path:
        pass
    else:
        while path[0] == '/':
            path = path[1:]
        index = path.index('/')
        path = path[index + 1:]
    return path


def analyze_result(portfolio, today_str, hdfs_root, result_dir_name, bt_dir):
    # CHECK
    if not os.path.exists('/data/user/666888/BT_Results/sources/' + today_str):
        os.makedirs('/data/user/666888/BT_Results/sources/' + today_str)
    elif os.path.exists('/data/user/666888/BT_Results/sources/' + today_str + '/' + result_dir_name):
        raise Exception('Path already exists: /data/user/666888/BT_Results/sources/' + today_str + '/' + result_dir_name)
    if not os.path.exists('/data/user/666888/BT_Results/results/' + today_str):
        os.makedirs('/data/user/666888/BT_Results/results/' + today_str)
    elif os.path.exists('/data/user/666888/BT_Results/results/' + today_str + '/' + result_dir_name):
        raise Exception('Path already exists: /data/user/666888/BT_Results/results/' + today_str + '/' + result_dir_name)
    if result_dir_name.startswith('cv'):
        excel_name = 'result_merged.xls'
    elif result_dir_name.startswith('bt'):
        excel_name = 'result_all.xls'
    else:
        raise Exception('Neither cv nor bt does the result_dir_name start with: ' + result_dir_name)

    # TRANSFER
    py = Pyfile()
    bt_dir = remove_relative(bt_dir)
    with py.open(bt_dir + portfolio + '_quantity.json', 'rb') as f:
        config = f.read()
        config = json.loads(config)
    hdfs_root = remove_relative(hdfs_root)
    py.download('/data/user/666888/BT_Results/sources/' + today_str + '/' + result_dir_name, hdfs_root + result_dir_name)

    # SUMMARIZE
    TotalSummary.summary(today_str, result_dir_name, portfolio, excel_name, config)
    sta_daily.summary(today_str, result_dir_name)
    summary_data.summary(today_str, result_dir_name)

    # TO GPU WEB
    if not os.path.exists('/data/user/666888/BT_Results/zipped/' + today_str):
        os.mkdir('/data/user/666888/BT_Results/zipped/' + today_str)
    zip_model.zip_file('/data/user/666888/BT_Results/sources/' + today_str + '/' + result_dir_name + '/',
                       '/data/user/666888/BT_Results/zipped/' + today_str, 'source-' + result_dir_name)
    zip_model.zip_file('/data/user/666888/BT_Results/results/' + today_str + '/' + result_dir_name + '/',
                       '/data/user/666888/BT_Results/zipped/' + today_str, 'result-' + result_dir_name)


def main():
    analyze_result(
        portfolio='z500',
        today_str='20181217',
        hdfs_root='666888/bt/',
        result_dir_name='bt-20181217-20181217-z500-use-cv-09_10-zz500-wide_close',
        bt_dir='SHARE_21/ModelProduction/20180901_end/bt_info/20181217-20181217/z500/'
    )


if __name__ == '__main__':
    main()