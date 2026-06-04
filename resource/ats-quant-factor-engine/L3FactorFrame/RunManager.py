import json
import time
import sys
import os
import numpy as np
import pandas as pd
import polars as pl
import pyarrow as pa
from L3FactorFrame.FactorManager import FactorManager
from MarketDataManager import MarketDataManager, get_l3_trade_order_data

sys.path.append("/root/codes/ats-quant-factor-engine")
sys.path.append("/root/codes/ats-quant-factor-engine/build")
from atsfactor import FactorManager as FactorManager_C, MarketDataManagerOption, ArrowTableMarketDataManager


class RunManager:
    def __init__(self, symbol, date, base_dir, factor_type="py"):
        self.symbol = symbol
        self.date = date
        self.base_dir = base_dir
        self.factor_type = factor_type
        self.runner = None
        self.marketDataManager = None
        self.option = None
        self.mdm = None
        self.factors_c = []
        self.values_c = []
        if self.factor_type == "py":
            self.marketDataManager = MarketDataManager(symbol, date, base_dir)
            # self.runner = FactorManager(marketDataManager)
        elif self.factor_type == "c++":
            self.option = MarketDataManagerOption()
            self.option.type = MarketDataManagerOption.MarketDataManagerType.ARROW_TABLE
        else:
            raise Exception("factor_type参数支持py或c++两个类型输入。")

    def trans_param_c(self, symbol, date, factor_params):
        # factor_params 为可传json文件路径或者dict类型的参数
        param = {
            "factors": [],
            "name": symbol + date + str(int(time.time() * 10000 // 10000))
        }
        if isinstance(factor_params, dict):
            conf = factor_params
        elif isinstance(factor_params, str) and os.path.isfile(factor_params):
            with open(factor_params, "r") as f:
                conf = json.load(f)
        else:
            raise Exception("【factor_params】为配置参数的字典或配置参数的json文件路径！")

        for fac in conf:
            if not isinstance(conf[fac], list):
                continue
            self.factors_c.append(fac)
            if len(conf[fac]) == 0:
                continue
            elif len(conf[fac]) == 1:
                add_conf = {"type": fac}
                if isinstance(conf[fac][0], dict):
                    add_conf.update(conf[fac][0])
                param["factors"].append(add_conf)
            else:
                for i in conf[fac]:
                    add_conf = {"type": fac}
                    if isinstance(i, dict):
                        add_conf.update(i)
                    else:
                        continue
                    param["factors"].append(add_conf)
        return param

    def __init_runner(self, factor_params=None):
        if self.factor_type == "py":
            self.runner = FactorManager(self.marketDataManager)
        else:
            params = self.trans_param_c(self.symbol, self.date, factor_params)
            params = json.dumps(params)
            self.runner = FactorManager_C(params, self.option)

    def register_factor(self, factor_params, factor_path=None, mkt_data_dir=None):
        self.__init_runner(factor_params)
        if self.factor_type == "py":
            self.runner.register_factor(factor_params, factor_path=factor_path)
        else:
            tick_df_1s = self.load_marketdata(self.symbol, self.date, mkt_data_dir)
            table = pa.table(tick_df_1s.to_pandas())
            self.mdm = ArrowTableMarketDataManager(table)

    def run(self):
        if self.factor_type == "py":
            self.runner.calc_loop()
        else:
            while not self.mdm.is_end():
                self.mdm.next()
                self.runner.caculate()
                self.values_c.append(self.runner.values())

    def get_all_factor_values(self, save_mode=False):
        if self.factor_type == "py":
            value_df = self.runner.get_all_factor_values(save_base_dir=self.base_dir, save_mode=save_mode)
        else:
            value_df = pl.from_pandas(pd.DataFrame(self.values_c, columns=self.factors_c)).with_columns(
                MDDate=pl.lit(self.date))
            if save_mode:
                if not os.path.exists(os.path.join(self.base_dir, "{}".format(self.symbol))):
                    try:
                        os.mkdir(os.path.join(self.base_dir, "{}".format(self.symbol)))
                    except:
                        time.sleep(0.1)
                save_path = os.path.join(self.base_dir, "{}/{}-{}.pqt".format(self.symbol, self.symbol, self.date))
                value_df.write_parquet(save_path)
        return value_df

    def load_marketdata(self, symbol, date, base_dir="/root/codes/ats-quant-factor-engine/dataset"):
        tick_df, order_df, trade_df, cancel_df = get_l3_trade_order_data(symbol, date, base_dir=base_dir)
        # TODO: 增加TradeVolume字段
        tick_df = tick_df.join(order_df, on="SeqNo").rename({
            "AskPrice": "asks_price",
            "BidPrice": "bids_price",
            "AskVolume": "asks_qty",
            "BidVolume": "bids_qty",
            "AskNum": "asks_count",
            "BidNum": "bids_count",
            "OrderType": "msg_order_type",
            "TradeType": "msg_trade_type",
            "SeqNo": "last_seq_num",
            "Price": "msg_price",
            "Volume": "msg_qty",
            "Amount": "msg_amt",
            "TradeVolume": "msg_trade_qty",
            "MDTime": "mdtime"
        }).select(["DateTime", 'mdtime', 'last_price', 'asks_price', 'bids_price', 'asks_qty',
                   'bids_qty', 'asks_count', 'bids_count', 'high_price', 'low_price',
                   'prev_close_price', 'ttl_volume', 'ttl_turn_over', 'ttl_trade_num',
                   'avg_ask_price', 'avg_bid_price', 'recvtime',
                   'msg_trade_type', 'msg_order_type', 'msg_bsflag', 'msg_price',
                   'msg_qty', 'msg_amt', 'msg_buy_no', 'msg_sell_no', 'last_seq_num']).with_columns(
            finished_time=pl.col('recvtime'),
            mdtime=pl.concat_str([pl.lit("20240116"), pl.col('mdtime')]).cast(pl.Int64)
        )
        # 将行情时间采样为1s，每秒取最新的一条
        how_method_dict = {}
        for col in tick_df.columns:
            if col not in ["DateTime"]:
                how_method_dict[col] = pl.col(col).last()
        # polars的resample不会补全缺失的秒
        tick_df_1s = tick_df.with_columns(pl.col("DateTime").set_sorted()). \
            group_by_dynamic(index_column='DateTime', every='1s', closed="right", label="right").agg(
            **how_method_dict).select(pl.all().exclude("DateTime"))
        return tick_df_1s
