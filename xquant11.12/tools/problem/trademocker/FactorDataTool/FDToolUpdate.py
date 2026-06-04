#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/3/3 15:31
import ray
import pandas as pd
from FactorDataTool.Config import HSET_HBASE_COLUMNS, HSI_HBASE_COLUMNS, CBOND_STOCK_HBASE_COLUMNS
from FactorDataTool.Config import MARKET_TYPE, INDEX_TYPE
from FactorDataTool.Config import CITICS_I_CODE, CITICS_II_CODE, SW_I_CODE, SW_II_CODE, SW_SHENWAN_MAP
from FactorDataTool.Config import CITICS, SW
from FactorDataTool.Config import INDEX_FUTURE_CODE, INDEX_FUTURE_HBASE_COLUMNS
from xquant.factordata import FactorData
from xquant.bonddata import BondData
from xquant.futuredata import FutureData
import multiprocessing as mp
from xquant.xqutils.helper import multicore_init
from Utils.HelpFunc import split_calc_date_into_group, get_trading_day


class FDToolUpdate:
    def __init__(self, library):
        self.library = library

        self.fa = FactorData()
        self.bd = BondData()
        self.fd = FutureData()

    def update_hset_hsi(self, start_date, end_date):
        self.update_hset(start_date, end_date)
        self.update_hsi(start_date, end_date)

    def update_hset(self, start_date, end_date):
        print("Start Update Hset Info {}-{}".format(start_date, end_date))
        self.update_hset_market(start_date, end_date)
        self.update_hset_index(start_date, end_date)
        self.update_hset_industry(start_date, end_date)

    def update_hset_market(self, start_date, end_date):
        trading_day_list = self.fa.tradingday(start_date, end_date)
        for trading_day in trading_day_list:
            for market in MARKET_TYPE:
                stock_set = self.fa.hset("MARKET", trading_day, market)[["stock"]]
                stock_set.columns = HSET_HBASE_COLUMNS
                if not stock_set.empty:
                    self.fa.update_factor_value(self.library, stock_set, market, trading_day)

    def update_hset_index(self, start_date, end_date):
        trading_day_list = self.fa.tradingday(start_date, end_date)
        for trading_day in trading_day_list:
            for index in INDEX_TYPE:
                stock_set = self.fa.hset("INDEX", trading_day, index)[["stock"]]
                stock_set.columns = HSET_HBASE_COLUMNS
                if not stock_set.empty:
                    self.fa.update_factor_value(self.library, stock_set, index, trading_day)

    def update_hset_industry(self, start_date, end_date):
        trading_day_list = self.fa.tradingday(start_date, end_date)
        for trading_day in trading_day_list:
            ### 中信一级和二级行业
            for indus in CITICS_I_CODE + CITICS_II_CODE:
                indus_code = CITICS + "." + indus
                stock_set = self.fa.hset("INDUSTRY", trading_day, indus_code)[["stock"]]
                stock_set.columns = HSET_HBASE_COLUMNS
                if not stock_set.empty:
                    self.fa.update_factor_value(self.library, stock_set, indus, trading_day)

            ### 申万一级和二级行业
            for indus in SW_I_CODE + SW_II_CODE:
                indus_code = SW + "." + indus
                stock_set = self.fa.hset("INDUSTRY", trading_day, indus_code)[["stock"]]
                stock_set.columns = HSET_HBASE_COLUMNS
                if not stock_set.empty:
                    self.fa.update_factor_value(self.library, stock_set, indus, trading_day)

                    ### 同时复制对应WIND申万代码行业信息
                    indus_shenwan = SW_SHENWAN_MAP.get(indus)
                    self.fa.update_factor_value(self.library, stock_set, indus_shenwan, trading_day)

    def update_hsi(self, start_date, end_date):
        print("Start Update Hsi Info {}-{}".format(start_date, end_date))
        trading_day_list = self.fa.tradingday(start_date, end_date)
        for trading_day in trading_day_list:
            alla_his = self.fa.hset("MARKET", trading_day, "ALLA_HIS")["stock"].tolist()
            citics1 = self.fa.hsi(alla_his, trading_day, industryType="CITICS", industryLevel=1)[["stock", "industry_code"]]
            citics2 = self.fa.hsi(alla_his, trading_day, industryType="CITICS", industryLevel=2)[["stock", "industry_code"]]
            sw1 = self.fa.hsi(alla_his, trading_day, industryType="SW", industryLevel=1)[["stock", "industry_code"]]
            sw2 = self.fa.hsi(alla_his, trading_day, industryType="SW", industryLevel=2)[["stock", "industry_code"]]
            citics = pd.merge(citics1, citics2, on="stock")
            sw = pd.merge(sw1, sw2, on="stock")
            shenwan1 = sw1.copy()
            shenwan1["industry_code"] = sw1["industry_code"].apply(lambda x: self.get_shenwan_code(x))
            shenwan2 = sw2.copy()
            shenwan2["industry_code"] = sw2["industry_code"].apply(lambda x: self.get_shenwan_code(x))
            shenwan = pd.merge(shenwan1, shenwan2, on="stock")
            indus_df = pd.merge(pd.merge(citics, sw, on="stock"), shenwan, on="stock")
            indus_df.columns = HSI_HBASE_COLUMNS
            self.fa.update_factor_value(self.library, indus_df, trading_day, "20200102")

    def get_shenwan_code(self, sw_code):
        if pd.isnull(sw_code):
            return sw_code
        else:
            return SW_SHENWAN_MAP[sw_code]

    def update_cbond_stock_map(self, start_date, end_date):
        print("Start Update CBond Stock Mapping Info {}-{}".format(start_date, end_date))
        trading_day_list = self.fa.tradingday(start_date, end_date)
        for trading_day in trading_day_list:
            all_cbond = self.bd.get_bond_set(trading_day, "kzz")
            cbond_info = self.fa.get_factor_value( "WIND_CCBondIssuance",
                                                   factors=["S_INFO_WINDCODE", "IS_CONVERTIBLE_BONDS", "S_INFO_COMPCODE"],
                                                   S_INFO_WINDCODE=all_cbond, IS_CONVERTIBLE_BONDS="1").dropna().drop_duplicates()
            cbond_info = cbond_info.set_index("S_INFO_WINDCODE")["S_INFO_COMPCODE"]

            stock_info = self.fa.get_factor_value("WIND_AShareDescription",
                                                  factors=["S_INFO_WINDCODE", "S_INFO_COMPCODE", "S_INFO_LISTDATE"],
                                                  S_INFO_LISTDATE=["<{}".format(trading_day)]).dropna().drop_duplicates()
            stock_info = stock_info.set_index("S_INFO_COMPCODE")
            stock_counts = stock_info["S_INFO_WINDCODE"].index.value_counts()

            cbond_stock_map = {}
            for cbond in cbond_info.index:
                comp_code = cbond_info.loc[cbond]
                if comp_code in stock_info.index:
                    if stock_counts.loc[comp_code] > 1:
                        cbond_stock_map[cbond] = stock_info.loc[comp_code].sort_values("S_INFO_LISTDATE",
                            ascending=False)["S_INFO_WINDCODE"].tolist()[-1]
                    else:
                        cbond_stock_map[cbond] = stock_info.loc[comp_code, "S_INFO_WINDCODE"]
            cbond_stock_df = pd.DataFrame([list(cbond_stock_map.keys()), list(cbond_stock_map.values())]).T
            cbond_stock_df.columns = CBOND_STOCK_HBASE_COLUMNS
            self.fa.update_factor_value(self.library, cbond_stock_df, trading_day, "20200102")

    def update_index_future_info(self, start_date, end_date):
        """"""
        print(" Start Update Index Future Contract Info {}-{} ".format(start_date, end_date))
        trading_day_list = self.fa.tradingday(start_date, end_date)
        for trading_day in trading_day_list:
            for future in INDEX_FUTURE_CODE:
                main_contract = self.fd.get_change_date(future, trading_day, "ZL00")[0]
                sub_main_contract = self.fd.get_change_date(future, trading_day, "ZL01")[0]
                all_contract = self.fd.get_instrument_all(future, trading_day, trading_day)
                index_future_set = pd.DataFrame([main_contract, sub_main_contract, all_contract]).T
                index_future_set.columns = INDEX_FUTURE_HBASE_COLUMNS
                if not index_future_set.empty:
                    self.fa.update_factor_value(self.library, index_future_set, "{}_IdF".format(future), trading_day)

def addFactors(library):
    factor_names = HSET_HBASE_COLUMNS + HSI_HBASE_COLUMNS + CBOND_STOCK_HBASE_COLUMNS + INDEX_FUTURE_HBASE_COLUMNS
    for factor in factor_names:
        try:
            FactorData().add_factor(library, [factor])
        except Exception as e:
            print(e)

def run_meta_task(library, start_date, end_date):
    instance = FDToolUpdate(library)
    instance.update_hset_hsi(start_date, end_date)
    instance.update_cbond_stock_map(start_date, end_date)
    # instance.update_index_future_info(start_date, end_date)

@ray.remote
def execute_task(task):
    run_meta_task(task["library"], task["start_date"], task["end_date"])

def run_ray(task_list, execute_task, options={"ray.num_cpus": 20, "object_store_memory": 10 ** 9 * 20}):
    num_cpus = 8
    object_store_memory = 10**9*8
    task_num = len(task_list)
    if options is not None:
        if "ray.num_cpus" in options:
            num_cpus = min(int(options["ray.num_cpus"]), task_num)
        if "ray.object_store_memory" in options:
            object_store_memory = min(options["ray.object_store_memory"], 10**9*num_cpus)

    assert multicore_init() == True
    ray.init(num_cpus=num_cpus, object_store_memory=object_store_memory)
    ray.get([execute_task.remote(task) for task in task_list])

    ray.shutdown()


if __name__=="__main__":
    library = "ZeusDataLib"
    start_date = "20210824"
    end_date = "20210824"
    mode = "Local" # "MultiProcess", "Ray"

    # addFactors(library)

    trading_days = get_trading_day(start_date, end_date)
    date_groups = split_calc_date_into_group(trading_days, 20)

    if mode == "Local":
        for group in date_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            run_meta_task(library, sub_start_date, sub_end_date)

    elif mode == "MultiProcess":
        task_list = []
        for group in date_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            task = (library, sub_start_date, sub_end_date, )
            task_list.append(task)

        if len(task_list) > 0:
            assert multicore_init() == True
            pool = mp.Pool(processes=min(20, len(task_list)))
            for task in task_list:
                pool.apply_async(run_meta_task, task)
            pool.close()
            pool.join()

    elif mode == "Ray":
        task_list = []
        for group in date_groups:
            sub_start_date = group[0]
            sub_end_date = group[-1]
            task = dict()
            task["library"] = library
            task["start_date"] = sub_start_date
            task["end_date"] = sub_end_date
            task_list.append(task)

        run_ray(task_list, execute_task)