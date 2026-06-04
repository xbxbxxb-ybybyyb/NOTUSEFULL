import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
import shutil
import json
import Analyzer.TotalSummary as TotalSummary
import Analyzer.sta_daily as sta_daily
import Analyzer.summary_data as summary_data
import Analyzer.zip_model as zip_model
from xquant.pyfile import Pyfile

portfolios = ["800", "big"]
model_prefix = '20190101_48_end'
excel_name = 'result_all.xls'
sources_dir = "/data/user/666888/BT_Results/sources/"
result_dir_names = ["production", "research"]


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


def combine_bt_sources(sources_dir, today_str):
    if (os.path.exists(sources_dir + today_str + "/production")
            or os.path.exists(sources_dir + today_str + "/research")):
        raise Exception("Mulu Cunzai")

    os.mkdir(sources_dir + today_str + "/production")
    os.mkdir(sources_dir + today_str + "/research")
    
    for bt_dir in os.listdir(sources_dir + today_str):
        if "800-production" in bt_dir:
            for file in os.listdir(sources_dir + today_str + "/" + bt_dir):
                shutil.copytree(
                    sources_dir + today_str + "/" + bt_dir + "/" + file,
                    sources_dir + today_str + "/production/" + file
                )
        if "800-research" in bt_dir and "Model20191101_48" not in bt_dir:
            for file in os.listdir(sources_dir + today_str + "/" + bt_dir):
                shutil.copytree(
                    sources_dir + today_str + "/" + bt_dir + "/" + file,
                    sources_dir + today_str + "/research/" + file
                )
        if "big-production" in bt_dir:
            for file in os.listdir(sources_dir + today_str + "/" + bt_dir):
                shutil.copytree(
                    sources_dir + today_str + "/" + bt_dir + "/" + file,
                    sources_dir + today_str + "/production/" + file
                )
        if "big-research" in bt_dir and "Model20191101_48" not in bt_dir:
            for file in os.listdir(sources_dir + today_str + "/" + bt_dir):
                shutil.copytree(
                    sources_dir + today_str + "/" + bt_dir + "/" + file,
                    sources_dir + today_str + "/research/" + file
                )


def combine_configs(model_prefix, today_str, portfolios):
    py = Pyfile()
    combined_config = {"quantity": {}}
    for portfolio in portfolios:
        bt_dir = ('666888/ModelProduction/{}/bt_info/{}-{}/{}/'
                  .format(model_prefix, today_str, today_str, portfolio))
        bt_dir = remove_relative(bt_dir)

        with py.open(bt_dir + portfolio + '_quantity.json', 'rb') as f:
            config = f.read()
            config = json.loads(config)
        combined_config["quantity"].update(config["quantity"])

    return combined_config


def analyze_combined_sources(today_str, result_dir_name, portfolio, excel_name, config):
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
    import BT_NEW.BT_SMALL.CONFIG_SMALL as bt_config_small
    config = bt_config_small.BacktestConfig()
    today_str = config.today_str
    
    combine_bt_sources(sources_dir, today_str)
    combined_config = combine_configs(model_prefix, today_str, portfolios)
    
    for result_dir_name in result_dir_names:
        analyze_combined_sources(today_str, result_dir_name, "", excel_name, combined_config)


if __name__ == '__main__':
    main()

