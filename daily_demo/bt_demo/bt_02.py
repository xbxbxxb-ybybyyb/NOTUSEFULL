# -*- coding: utf-8 -*-

import os
import configparser

from xquant.futuredata import FutureData
from xbrain import XBrain
from strategy_02 import StrategyExample

def main():
    # 读取参数配置文件
    conf_path = os.path.join(os.path.dirname(__file__), 'settings.ini')
    config = configparser.ConfigParser()
    config.read(conf_path, encoding='utf-8')


    # 解析参数
    instrument = config['data']['instrument']
    start = config['data']['start.date'].replace('/', '')
    end = config['data']['end.date'].replace('/', '')
    time_frame = config['data']['time.frame']


    # 通过 XQuant API 获取回测数据，并整理数据成回测框架可识别的数据格式：
    # 包含 ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'] 字段，其中 Datetime 为 %Y%m%d%H%M%S%f
    fd = FutureData()
    data = fd.get_future_data(
        symbol='{}ZL'.format(instrument),
        start_time='{}000000000'.format(start),
        end_time='{}235959000'.format(end),
        bar_size=time_frame,
        method=True,
        contract_type='ZL00'
    )
    data = data[['MDDate', 'MDTime', 'OpenPx', 'HighPx', 'LowPx', 'ClosePx', 'TotalVolumeTrade']]
    data.columns = ['MDDate', 'MDTime', 'Open', 'High', 'Low', 'Close', 'Volume']
    data['Datetime'] = data.apply(lambda x: x['MDDate'] + x['MDTime'], axis=1)
    data = data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]

    data.to_csv("/data/user/013150/future_data.csv")
    # 创建回测框架 XBrain 实例
    xbrain = XBrain()
    ####################################################################


    # 初始化回测框架
    xbrain.init(config)
    ####################################################################


    # 加载数据到回测框架
    # 注：需要告知框架数据的粒度，即 time_frame, compression，用于时间对齐：
    # 若数据为 1 分钟K，则 time_frame = 'K_1MIN', compression=1,
    # 若数据为 5 分钟K，则 time_frame = 'K_1MIN', compression=5.
    xbrain.add_data(df=data, time_frame=time_frame, compression=1, name='{}ZL00'.format(instrument))
    ####################################################################


    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    xbrain.add_strategy(StrategyExample)
    ####################################################################


    # 运行回测
    xbrain.backtest_run()
    ####################################################################


    # 生成回测报告
    xbrain.generate_report()
    ####################################################################



if __name__ == '__main__':
    main()

    # 注：任务运行结束后可能会出现以下异常信息，并不会影响运行结果，可以忽略。
    # Error in sys.excepthook:
    #
    # Original
    # exception
    # was:
