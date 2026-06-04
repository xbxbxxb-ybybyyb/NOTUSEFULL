import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
import datetime as dt
import pandas as pd
import BT_NEW.TARGET_CODE_300_500 as target_code
import BT_NEW.combine_trade_and_capacity as combine_trade_and_capacity
import BT_NEW.BT_SMALL.CONFIG_SMALL as bt_config_small
import BT_NEW.BT_BIG.CONFIG_BIG as bt_config_big
from xquant.pyfile import Pyfile


def combine_bt_data(is_copy_to_share):
    config_small = bt_config_small.BacktestConfig()
    config_big = bt_config_big.BacktestConfig()

    trade_portfolios = []
    trade_portfolios.extend(config_small.trade_portfolio)
    trade_portfolios.extend(config_big.trade_portfolio)
    today_str = config_small.today_str

    py = Pyfile()
    model_prefix = '20190101_48_end'

    print("Combining {}'s trade and capacity...".format("h300"))
    combine_trade_and_capacity.combine(
        target_code.target_code_300,
        target_code.volume_300,
        today_str,
        today_str,
        'h300'
    )

    print("Combining {}'s trade and capacity...".format("z500"))
    combine_trade_and_capacity.combine(
        target_code.target_code_500,
        target_code.volume_500,
        today_str,
        today_str,
        'z500'
    )

    for portfolio in trade_portfolios:
        print("combining {}'s trade and capacity".format(portfolio))
        file_name = "{}_{}.xlsx".format(today_str, portfolio)
        portfolio_df = pd.read_excel("/data/user/666888/ftp_uploads_bt/" + file_name)
        print(portfolio_df)
        codes = list([_code for _code in portfolio_df.iloc[:, 0]])
        volumes = list([int(_code) for _code in portfolio_df.iloc[:, 3]])
        combine_trade_and_capacity.combine(codes, volumes, today_str, today_str, portfolio)

    if is_copy_to_share:
        portfolios = ['h300', 'z500']
        portfolios.extend(trade_portfolios)

        for portfolio in portfolios:
            print(dt.datetime.now(), "Uploading {}'s trade and capacity to HDFS...".format(portfolio))
            py.upload(
                'ModelProduction/' + model_prefix + '/bt_info/{}-{}/{}/'.format(today_str, today_str, portfolio),
                '/data/user/666888/BT_Trade_OrderCapacity/{}-{}/{}/'.format(today_str, today_str, portfolio)
            )

    print("End")


if __name__ == '__main__':
    combine_bt_data(is_copy_to_share=True)
