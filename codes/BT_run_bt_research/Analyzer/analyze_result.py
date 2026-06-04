import os
import json
import shutil
import Analyzer.TotalSummary as TotalSummary
import Analyzer.sta_daily as sta_daily
import Analyzer.summary_data as summary_data
from xquant.pyfile import Pyfile


def analyze_result(portfolio, today_str, output_dir, result_dir_name, bt_dir, dir_name):
    source_path = '/data/user/011668/{}/sources/{}'.format(dir_name, today_str)
    result_path = '/data/user/011668/{}/results/{}'.format(dir_name, today_str)
    source_path_dir = '{}/{}'.format(source_path, result_dir_name)
    result_path_dir = '{}/{}'.format(result_path, result_dir_name)

    # CHECK
    if not os.path.exists(source_path):
        os.makedirs(source_path)
    elif os.path.exists(source_path_dir):
        shutil.rmtree(source_path_dir)
    if not os.path.exists(result_path):
        os.makedirs(result_path)
    elif os.path.exists(result_path_dir):
        shutil.rmtree(result_path_dir)
    if result_dir_name.startswith('cv'):
        excel_name = 'result_merged.xls'
    elif result_dir_name.startswith('bt'):
        excel_name = 'result_all.xls'
    else:
        raise Exception('Neither cv nor bt does the result_dir_name start with: ' + result_dir_name)

    # TRANSFER
    py = Pyfile()
    with py.open('{}/{}_quantity.json'.format(bt_dir, portfolio), 'rb') as f:
        config = f.read()
        config = json.loads(config)
    py.download(source_path_dir, output_dir)

    # SUMMARIZE
    TotalSummary.summary(source_path_dir, result_path_dir, excel_name, config)
    sta_daily.summary(result_path_dir)
    summary_data.summary(result_path_dir)
