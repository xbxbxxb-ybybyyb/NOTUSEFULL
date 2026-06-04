# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
import os
import numpy as np
import pickle
from System.TradingDay import getNDaysOff, getTradingDay
from xquant.factordata import FactorData
from xquant.bonddata import BondData
from xquant.xqutils.xqfile import HDFSFile
s = FactorData()
bd = BondData()
hf = HDFSFile()


EXCEPTIONS = [
    ["Stock", "INF", "向前取日频数据整个行业有停牌等交易异常问题导致成交量为0计算出现NaN，且对于整个行业只有一个值，计算框架默认不存储"],
    ["Stock", "Panel", "INF中可能有None或NaN"],
    ["Stock", "Panel", "刚上市若干天无行业分类信息"],  # 已处理，仅处理了SW2的情况
    ["Stock", "All", "更名导致历史数据缺失"],  # 已处理
    ["CB", "All", "开盘即临停，当天时间戳只有1个"],  # 已处理
    ["All", "All", "上市第一天取日频数据且该日频数据对计算来说是必须的会导致当天全部NaN，计算框架默认不存储"],
]

EXCLUDED_LIST = [
    "110030.SH",  # TradeStatus与实际可取到数据不一致，已经退市；
]


PARDON_DICT = {
    "001872.SZ": ("20180710", "20181130"),  # 更名
    "001914.SZ": ("20180102", "20191129"),  # 更名
    "601360.SH": ("20180102", "20180307"),  # 更名
}


N_QUERY = 180


class Guardian:
    def __init__(self, asset_type: str, factor_lib: str, data_lib: str, stock: str, factor_list: list, factor_config: list,
                 start_date: str, end_date: str, tick_lib: str = None, anchor_to_tick: bool = False):
        self.asset_type = asset_type
        self.factor_lib = factor_lib
        self.data_lib = data_lib
        self.stock = stock
        self.factor_list = factor_list
        self.start_date = start_date
        self.end_date = end_date
        self.tick_lib = data_lib if tick_lib is None else tick_lib
        self.anchor_to_tick = anchor_to_tick

        self.check_date_list, self.ipo_date = self.__get_check_date_list()
        self.factor_config_dict = {each.get("FactorName", each["ClassName"]): each for each in factor_config}
        self.exclude_date_set = set()  # 对于转债，把开盘即临停日期记录下来；对于截面因子，把刚上市没有行业分类的日期记录下来

    def __get_check_date_list(self):
        if self.stock not in EXCLUDED_LIST:
            if self.asset_type in ["INF", "Index", "Synthesized"]:
                check_date_list = list(map(str, getTradingDay(int(self.start_date), int(self.end_date))))
                ipo_date = None
            else:
                status_df = s.get_factor_value(self.data_lib, "{}".format(self.stock), "20200102", ["D_Date", "D_TradeStatus", "D_Volume"])
                status_df = status_df.set_index("D_Date")
                if self.asset_type in ["Stock", "ETF", "Future"]:
                    idx = ((~status_df["D_TradeStatus"].isnull())
                           & (status_df["D_TradeStatus"] != "待核查")
                           & (status_df["D_TradeStatus"] != "停牌")
                           & (status_df["D_Volume"]).astype(float) != 0)
                elif self.asset_type == "CB":
                    idx = ((~status_df["D_TradeStatus"].isnull())
                           & (status_df["D_TradeStatus"] != "待核查")
                           & (status_df["D_TradeStatus"] != "停牌")
                           & (status_df["D_TradeStatus"] != "0")
                           & (status_df["D_Volume"]).astype(float) != 0)
                else:
                    raise ValueError("Unknown assets type.")
                if self.stock in PARDON_DICT:
                    exclude_date_list = s.tradingday(PARDON_DICT[self.stock][0], PARDON_DICT[self.stock][1])
                    idx = np.array([each not in exclude_date_list for each in status_df.index]) & idx
                status_df = status_df.loc[idx].loc[self.start_date: self.end_date, :]
                check_date_list = status_df.index.to_list()
                ipo_date = status_df[status_df["D_TradeStatus"] == "N"].index.to_list()
                ipo_date = ipo_date[0] if len(ipo_date) > 0 else None
            return check_date_list, ipo_date
        else:
            return [], None

    def check_completeness_1by1(self):
        # if self.stock.endswith("SH"):
        #     factor_list = [factor for factor in self.factor_list if not factor.startswith("factor") or
        #                    ("O" not in self.factor_config_dict[factor]["DataSource"] and
        #                     "C" not in self.factor_config_dict[factor]["DataSource"])]
        # else:
        factor_list = self.factor_list

        check_result = []
        for date in self.check_date_list:
            if factor_list:
                try:
                    temp_data = s.get_factor_value(self.factor_lib, self.stock, date, factor_list)
                    uncalculated_factor_list = [each for each in factor_list if each not in temp_data.columns]
                    check_result.extend([(self.stock, date, factor) for factor in uncalculated_factor_list])
                except:
                    if self.anchor_to_tick:
                        try:
                            if self.stock.endswith("SH"):
                                temp_data = s.get_factor_value("Channel1STickDataLibSH2023", self.stock, date, ["T_Time"], compress = True)["T_Time"]
                            else:
                                temp_data = s.get_factor_value("Channel1STickDataLibSZ2023", self.stock, date, ["T_Time"], compress = True)["T_Time"]
                            check_result.extend([(self.stock, date, factor) for factor in factor_list])
                        except:
                            pass
                    else:
                        #  转债：排除开盘即临停的日期
                        if self.asset_type == "CB":
                            temp_data = s.get_factor_value(self.data_lib, self.stock, date, ["T_Time"])["T_Time"]
                            if np.nansum((temp_data > "093012000") & (temp_data < "145700000")) >= 10:
                                check_result.extend([(self.stock, date, factor) for factor in factor_list])
                        else:
                            check_result.extend([(self.stock, date, factor) for factor in factor_list])
        return check_result
    def check_completeness(self):
        # 功能：检查计算完整性

        # 进行时间段切分，否则查询可能超长报错
        check_date_list = self.check_date_list
        n = len(check_date_list) // N_QUERY if len(check_date_list) % N_QUERY == 0 else len(check_date_list) // N_QUERY + 1

        check_result = []
        if len(self.check_date_list) > 0:
            for factor in self.factor_list:
                # 使用了Order上交所股票跳过
                if factor.startswith("factor") and self.stock.endswith("SH") and \
                        ("O" in self.factor_config_dict[factor]["DataSource"] or
                         "C" in self.factor_config_dict[factor]["DataSource"]):
                    continue

                # 判断是否是截面因子，是否需要对上市第一天进行特殊处理
                if factor.startswith("factor"):
                    config = self.factor_config_dict[factor]
                    if config["FactorType"] == "IPANEL" or config["FactorType"] == "PANEL":
                        daily_length = config.get("DailyLength", 0)
                        minute_length = config.get("MinuteLength", 0)
                        tick_length = config.get("TickLength", 0)
                        max_length = np.nanmax([daily_length, minute_length, tick_length])
                    else:
                        max_length = 0
                else:
                    max_length = 0

                # 分段进行判断
                for i in range(n):
                    temp_check_date_list = check_date_list[i*N_QUERY: (i+1)*N_QUERY]
                    existed_date_list = s.search_by_stock_factor(self.factor_lib, self.stock, factor, temp_check_date_list)
                    uncalculated_date_set = set(temp_check_date_list).difference(set(existed_date_list)).difference(self.exclude_date_set)
                    if max_length > 0 and self.ipo_date is not None and self.ipo_date in uncalculated_date_set:
                        uncalculated_date_set.remove(self.ipo_date)
                    # 转债：排除开盘即临停的日期
                    if self.asset_type == "CB" and len(uncalculated_date_set) > 0:
                        for each in uncalculated_date_set:
                            temp_data = s.get_factor_value(self.data_lib, self.stock, each, ["T_Time"])["T_Time"]
                            if np.nansum((temp_data > "093012000") & (temp_data < "145700000")) < 10:
                                self.exclude_date_set.add(each)
                    uncalculated_date_set = uncalculated_date_set.difference(self.exclude_date_set)
                    # 股票：排除刚上市无行业分类日期
                    if factor.startswith("factor") and self.asset_type == "Stock" and len(uncalculated_date_set) > 0 and \
                            self.factor_config_dict[factor]["FactorType"] == "IPANEL" and "INFGroup" in self.factor_config_dict[factor]:
                        for each in uncalculated_date_set:
                            ind = s.hsi([self.stock], str(getNDaysOff(int(each), 1)), "SW", 2)
                            if ind.shape[0] == 0:
                                self.exclude_date_set.add(each)
                            else:
                                comp = s.get_factor_value("INFactor", ind["industry_code"].values[0], str(getNDaysOff(int(each), 1)), ["symbols"]).iloc[0, 0]
                                if self.stock not in comp:
                                    self.exclude_date_set.add(each)
                    uncalculated_date_set = uncalculated_date_set.difference(self.exclude_date_set)
                    # 股票衍生截面因子：排除刚上市无行业分类日期
                    if factor.startswith("factor") and self.asset_type == "Stock" and len(uncalculated_date_set) > 0 and \
                            self.factor_config_dict[factor]["FactorType"] == "IPANEL" and "ClassName" not in self.factor_config_dict[factor]:
                        for each in uncalculated_date_set:
                            ind = s.hsi([self.stock], str(getNDaysOff(int(each), 1)), "SW", 1)
                            if ind.shape[0] == 0:
                                self.exclude_date_set.add(each)
                    uncalculated_date_set = uncalculated_date_set.difference(self.exclude_date_set)
                    # 记录
                    if len(uncalculated_date_set) > 0:
                        check_result.extend([(self.stock, each, factor) for each in uncalculated_date_set])

        return check_result

    def check_invalid(self, threshold):
        # 功能：检查NA/Inf
        # asset_type: str, factor_lib: str, data_lib: str, stock: str, factor_list: list,
        # start_date: str, end_date: str
        check_result = []
        for date in self.check_date_list:
            try:
                data = s.get_factor_value(self.factor_lib, self.stock, date, self.factor_list)
                invalid_factor_set = set()
                if np.any(np.isnan(data)):
                    invalid_factor_set = invalid_factor_set.union(set(self.factor_list))
                invalid_factor_set = invalid_factor_set.union(set(data.columns[np.any(data.abs() > threshold, axis=0)]))
                if len(invalid_factor_set) > 0:
                    check_result.extend([(self.stock, date, each) for each in invalid_factor_set])
            except:
                pass
        return check_result

    def check_consistency(self, mirror_lib: str, epsilon: float):
        # 功能：检查漂移/变更因子代码后新计算因子值与存量是否一致
        # asset_type: str, factor_lib: str, data_lib: str, stock: str, factor_list: list,
        # start_date: str, end_date: str
        check_result = []
        for date in self.check_date_list:
            try:
                data_origin = s.get_factor_value(self.factor_lib, self.stock, date, self.factor_list)
                data_new = s.get_factor_value(mirror_lib, self.stock, date, self.factor_list)
                diff = (data_origin - data_new).abs()
                inconsistent_factor_set = set(diff.columns[np.any(diff > epsilon, axis=0)].to_list())
                if len(inconsistent_factor_set) > 0:
                    check_result.extend([(self.stock, date, each) for each in inconsistent_factor_set])
            except:
                pass
        return check_result

    def check_nonexistence(self):
        # 检查因子值是否不存在
        check_date_list = list(map(str, getTradingDay(int(self.start_date), int(self.end_date))))
        check_result = []
        for date in check_date_list:
            try:
                data = s.get_factor_value(self.factor_lib, self.stock, date, self.factor_list)
                for factor in data.columns:
                    check_result.append((self.stock, date, factor))
            except:
                pass
        return check_result


def get_factor_guardian_root(user_id):
    if "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ:
        root = f'/{user_id}/FactorCheckLog'
    else:
        root = 'FactorCheckLog'
    return root


def update_check_result(user_id, check_result, stock: str, start_date: str, end_date: str, intermediate_log_path: str):
    root = get_factor_guardian_root(user_id)
    path = "{}/{}".format(root, intermediate_log_path)
    if not hf.exists(path):
        hf.mkdir(path)

    file = "{}/{}_{}_{}.pickle".format(path, stock, start_date, end_date)

    with hf.open(file, "wb") as f:
        pickle.dump(check_result, f)


def collect_check_result(user_id, intermediate_log_path: str, check_result_file: str, return_check_result=False):
    root = get_factor_guardian_root(user_id)
    path = "{}/{}".format(root, intermediate_log_path)

    if hf.exists(path):
        file_list = hf.listdir(path)
        check_result_set = set()
        factor_set = set()
        for file in file_list:
            with hf.open("{}/{}".format(path, file), "rb") as f:
                data = f.read()
                temp_check_result_list = pickle.loads(data)
                for each in temp_check_result_list:
                    check_result_set.add((each[0], each[1]))
                    factor_set.add(each[2])

        check_result = (sorted(factor_set), sorted(check_result_set))

        path_result = f'/data/user/{user_id}/FactorCheck'
        if not os.path.exists(path_result):
            os.makedirs(path_result)
        file_result = "{}/{}.pickle".format(path_result, check_result_file)
        with open(file_result, "wb") as f:
            pickle.dump(check_result, f)
        print(file_result, "has been saved.")
        if return_check_result:
            return False, check_result
        else:
            return False
    else:
        print("WARNING: {} is not existed.".format(path))
        if return_check_result:
            return True, ([], [])
        else:
            return True


def get_check_samples(user_id, asset_type: str, samples_number: int, start_date: str, end_date: str, sample_file: str,
                      replace: bool, factor_list: list = None):
    # replace 指的是每天股票池是否相同
    if replace:
        if asset_type == "Stock":
            stock_list = s.hset("MARKET", end_date, "ALLA")["stock"].to_list()
        elif asset_type == "CB":
            stock_list = bd.get_bond_set(end_date, "kzz")
        else:
            raise Exception("Unsupported asset type.")
        samples = sorted(np.random.choice(stock_list, samples_number, replace=False).tolist())
    else:
        trading_day_list = list(map(str, getTradingDay(int(start_date), int(end_date))))
        samples = []
        for date in trading_day_list:
            if asset_type == "Stock":
                stock_list = s.hset("MARKET", date, "ALLA")["stock"].to_list()
            elif asset_type == "CB":
                stock_list = bd.get_bond_set(end_date, "kzz")
            else:
                raise Exception("Unsupported asset type.")
            samples.extend([(each, date) for each in np.random.choice(stock_list, samples_number, replace=False).tolist()])
        samples = (factor_list, samples)

    path_samples = f'/data/user/{user_id}/FactorCheck'
    if not os.path.exists(path_samples):
        os.makedirs(path_samples)
    file = "{}/{}.pickle".format(path_samples, sample_file)
    with open(file, "wb") as f:
        pickle.dump(samples, f)
    print(file, "has been saved.")


