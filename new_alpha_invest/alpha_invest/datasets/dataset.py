from xquant.factordata import FactorData
import os
import pandas as pd
from alpha_invest import alpha_logger
from alpha_invest.datasets.data_utils import get_n_days_off, convert_df_index_type
from alpha_invest.datasets.factor import get_panel_daily_pv_df,get_factor_values
from alpha_invest.datasets.tag import load_label

class DataSetManager:
    def __init__(self, start_date, end_date, universe = "ALLA", label_period =1, factor_path = None, label_path = None):
        """
        :param start_date:
        :param end_date:
        :param universe:
        :param label_period:  标签的计算周期，如5，表示拿5天后的值计算标签。
        :param factor_path: 依赖的因子数据路径
        """
        self.base_factor = None
        self.universe = universe
        self.label_period = label_period
        self.factor_path = factor_path
        self.label_path = label_path

        self.fa = FactorData()
        self.query_date_list = self.fa.tradingday(start_date, end_date)  # 获取起止日期list
        self.start_date_int = self.query_date_list[0]  # 确保start_date_int是交易日
        self.end_date_int = self.query_date_list[-1]  # 确保end_date_int是交易日，以利于后续计算BACKWARD2（前复权）时定位用

        self.stock_list = self.get_stock_universe(self.universe)
        alpha_logger.debug("stock num: {}".format(len(self.stock_list)))
        alpha_logger.debug("start_date_int: {} , end_date_int: {}".format(self.start_date_int, self.end_date_int))

    def get_stock_universe(self, universe):
        return self.fa.hset('MARKET', self.start_date_int, universe)["stock"].tolist()

    def get_factor_data(self, factor_list, test_mode = False):
        """
        规范：返回格式为字典，key为因子名，value为截面因子dataframe，行业date，列为stock。
        :param factor_list:
        :return:
        """
        # TODO: 需保证label_data和factor_data数据一致（长度一致，顺序一致）
        factor_dict = {}
        if test_mode:
            pv_factors = ['close', 'open', 'high', 'low', 'pre_close', 'volume', 'amt', 'pct_chg', 'turn', 'twap', 'vwap',
                          'buy_twap', 'buy_twap_fill_rate', 'sell_twap', 'sell_twap_fill_rate', 'buyable_volume',
                          'sellable_volume', 'vwap', 'dealnum', 'buy_vwap', 'sell_vwap', 'suspension', 'UpPrice',
                          'DownPrice', 'UpPrice2', 'DownPrice2', "adjfactor"]
            for fac in factor_list:
                if fac in pv_factors:
                    df = get_panel_daily_pv_df(self.stock_list, self.query_date_list, fac, adj_type = "BACKWARD2")
                else:
                    df = get_factor_values(self.stock_list, self.query_date_list, [fac])
                df.index = [int(day) for day in df.index]
                df = convert_df_index_type(df, 'date_int', 'timestamp')
                factor_dict[fac] = df
        else:
            for fac in factor_list:
                try:
                    df = pd.read_pickle(os.path.join(self.factor_path, f'{fac}.pkl'))
                    df = df[df.index.isin(self.query_date_list)]
                    df.index = [int(day) for day in df.index]
                    df = convert_df_index_type(df, 'date_int', 'timestamp')
                    factor_dict[fac] = df
                except:
                    import traceback
                    print(traceback.print_exc())
                    raise Exception(f"DataSetManager: 所填的依赖因子{fac}不存在！")
        return factor_dict

    def get_label_data(self, label_type='vwap_excess_300', test_mode = False):
        """
        规定返回格式为：截面因子dataframe，行业date，列为stock。
        :param label_type:
        :return:
        """
        #TODO: 需保证label_data和factor_data数据一致,(长度一致，顺序一致)
        if test_mode:
            df = load_label(self.stock_list, self.query_date_list , label_type=label_type, holding_period = self.label_period)
        else:
            label_name = f"{label_type}_{self.label_period}d"
            try:
                df = pd.read_pickle(os.path.join(self.label_path, f'{label_name}.pkl'))
                df = df[df.index.isin(self.query_date_list)]
                df.index = [int(day) for day in df.index]
                df = convert_df_index_type(df, 'date_int', 'timestamp')
            except:
                import traceback
                print(traceback.print_exc())
                raise Exception(f"DataSetManager: 所填的依赖标签{label_name}不存在！")

        return df


if __name__=="__main__":
    ds = DataSetManager("20190101", "20191231")
    df_factor = ds.get_factor_data(["close"])
    df_lable = ds.get_label_data(label_type='vwap_excess_300')
    print(df_factor)
    print(df_lable)