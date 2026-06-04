import numpy as np
import datetime as dt
import os
import polars as pl
import traceback
import importlib.util
import copy
import time
# from xquant.xqutils.perf_profile import profile


def get_factor_module(factor_name, file_path):
    # 遍历文件夹下的所有.py文件
    file_path_list = []
    for root, dirs, files in os.walk(file_path):
        for file in files:
            # 获取文件名称
            if not file.endswith('.py'):
                continue
            file_name, file_tail = file.split('.')[:2]
            # 获取文件绝对路径
            file_abs_path = os.path.join(root, file)
            if file_name == factor_name and file_tail == 'py':
                file_path_list.append(file_abs_path)
    if len(file_path_list) == 0:
        raise Exception("无法加载因子类：文件夹'{}'下无与因子{}同名的因子文件，请指定正确的file_path因子文件目录！".format(
            file_path, factor_name))
        return
    elif len(file_path_list) > 1:
        print("匹配到多个因子文件:" + " ".join(
            i for i in file_path_list) + "，请指定正确的file_path因子文件目录！")
        return
    else:
        return file_path_list[0]
    return


# 根据因子名 去指定的路径下找到和因子名相同的因子文件 并加载其中的因子类
def get_fac_class(factor_name, file_path):
    file_abs_path = get_factor_module(factor_name, file_path)
    module_spec = importlib.util.spec_from_file_location(factor_name, file_abs_path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    try:
        cls = getattr(module, factor_name)
    except:
        raise Exception("ERROR: Please keep factor class name same as factor name!")
    return cls



class FactorManager:
    def __init__(self, marketDataManager, verbose = 0) -> None:
        self.marketDataManager = marketDataManager
        self.error_list = []
        self.factor_list = []
        self.event_list = []
        self.nonfactor_list = []
        self.nonfactor_instance_cache = {}
        self.sysinfo_list = ["Timestamp", "MDTime", "SeqNo", "DateTime"]#特殊的预留列，如timestamp、MDTime、SeqNo、DateTime
        self.factor_path = None
        self.event_path = None
        self.nonfactor_path = None
        self.verbose = verbose

    def __set_factor_path(self, factor_path):
        factor_list_all = [i.split(".")[0] for i in os.listdir(factor_path) if i.endswith("py")]
        self.factor_path = factor_path
        return factor_list_all

    def __set_event_path(self, event_path):
        self.event_path = event_path
        event_list_all = [i.split(".")[0] for i in os.listdir(event_path) if i.endswith("py")]
        return event_list_all

    def __set_nonfactor_path(self, nonfactor_path):
        self.nonfactor_path = nonfactor_path
        nonfactor_list_all = [i.split(".")[0] for i in os.listdir(nonfactor_path) if i.endswith("py")]
        return nonfactor_list_all

    def register_factor(self, config, factor_path = None, event_path = None, nonfactor_path = None):
        factor_list_all, event_list_all = [], []
        if factor_path:
            factor_list_all = self.__set_factor_path(factor_path)#加载当前目录上有的因子
        if event_path:
            event_list_all = self.__set_event_path(event_path)
        else:
            event_list_all = []
        if nonfactor_path:
            nonfactor_list_all = self.__set_nonfactor_path(nonfactor_path)
        else:
            nonfactor_list_all = []

        # 优先注册nonfactor保证能被其他因子引用到
        for factor_class_name in config:
            if factor_class_name in nonfactor_list_all:
                sub_config = config[factor_class_name]
                nonfactor_class = get_fac_class(factor_class_name, self.nonfactor_path)
                for pidx, param_dict in enumerate(sub_config):
                    try:
                        nonfactor_instance = nonfactor_class(param_dict,self, self.marketDataManager)
                        nonfactor_instance.set_factor_name(factor_class_name, pidx)
                        self.nonfactor_list.append(nonfactor_instance)
                        # print("regist factor success:", str(factor_instance.factor_name))
                    except Exception as e:
                        print("regist nonfactor error:", str(factor_class_name), e)
                        symbol = self.marketDataManager.getSymbol()
                        date = self.marketDataManager.getDate()
                        self.error_list.append((str(factor_class_name), symbol, date))

        for factor_class_name in config:
            if factor_class_name=="SeqNo":
                try:
                    factor_class = get_fac_class(factor_class_name, factor_path)
                except:
                    factor_class = get_fac_class(factor_class_name, event_path)
                if event_path:
                    # 行数不一样，需要两份SeqNo
                    factor_instance = factor_class({}, self, self.marketDataManager)
                    factor_instance.set_factor_name(factor_class_name, 0)
                    self.event_list.append(factor_instance)
                factor_instance = factor_class({}, self, self.marketDataManager)
                factor_instance.set_factor_name(factor_class_name, 0)
                self.factor_list.append(factor_instance)
                continue
            if factor_class_name in event_list_all:
                # 事件
                sub_config = config[factor_class_name]
                factor_class = get_fac_class(factor_class_name, self.event_path)
                for pidx, param_dict in enumerate(sub_config):
                    try:
                        factor_instance = factor_class(param_dict, self, self.marketDataManager)
                        factor_instance.set_factor_name(factor_class_name, pidx)
                        self.event_list.append(factor_instance)
                        # print("regist factor success:", str(factor_instance.factor_name))
                    except Exception as e:
                        print("regist event error:", str(factor_class_name), e)
                        symbol = self.marketDataManager.getSymbol()
                        date = self.marketDataManager.getDate()
                        self.error_list.append((str(factor_class_name), symbol, date))
            elif factor_class_name in nonfactor_list_all:
                pass
            else:
                # 因子
                if factor_class_name not in factor_list_all:
                    print("ERROR: factor or event not found error:", str(factor_class_name))
                    continue
                sub_config = config[factor_class_name]
                factor_class = get_fac_class(factor_class_name, self.factor_path)
                for pidx, param_dict in enumerate(sub_config):
                    try:
                        factor_instance = factor_class(param_dict, self, self.marketDataManager)
                        factor_instance.set_factor_name(factor_class_name, pidx)
                        self.factor_list.append(factor_instance)
                        # print("regist factor success:", str(factor_instance.factor_name))
                    except Exception as e:
                        import traceback
                        print(traceback.print_exc())
                        print("regist factor error:", str(factor_class_name), e)
                        symbol = self.marketDataManager.getSymbol()
                        date = self.marketDataManager.getDate()
                        self.error_list.append((str(factor_class_name), symbol, date))

        if self.verbose>0:
            print("factor length:", len(self.factor_list))
            print([fac.__class__.__name__ for fac in self.factor_list])
            print("event length:", len(self.event_list))
            print([fac.__class__.__name__ for fac in self.event_list])
            print("nonfactor length:", len(self.nonfactor_list))
            print([fac.__class__.__name__ for fac in self.nonfactor_list])

    def get_factor_instance(self, factor_name):
        if self.nonfactor_instance_cache.get(factor_name, None):
            pass
        else:
            flag = False
            for factor_instance in self.nonfactor_list:
                if factor_instance.__class__.__name__ == factor_name:
                    flag = True
                    self.nonfactor_instance_cache[factor_name] = factor_instance
            assert flag, "get_factor_instance获取因子实例{}未找到！".format(factor_name)

        return self.nonfactor_instance_cache.get(factor_name)


    def calc_loop(self, mode = "FULL"):
        def calc_factor(fac):
            try:
                fac.calculate()
            except:
                import traceback
                symbol = self.marketDataManager.symbol
                date = self.marketDataManager.date
                fac.addNanFactorValue()
                print("ERROR-{}-{}-{}".format(symbol, date, self.marketDataManager.dataindex), traceback.print_exc())

        if mode.upper() == "FULL":
            # 全量数据计算
            while self.marketDataManager.idx < len(self.marketDataManager.tick_array)-1:
                self.marketDataManager.broadcast()
                if self.verbose > 0:
                    t0 = time.time()
                for fac in self.event_list+self.nonfactor_list+self.factor_list:
                    if self.verbose >0 :
                        t1 = time.time()
                    calc_factor(fac)
                    if self.verbose >0 :
                        print(fac.__class__.__name__, time.time()-t1)
                if self.verbose > 0:
                    print(f"==============={time.time()-t0}=================")
        elif mode.upper()=="SAMPLE_1S":
            # nonfactor和event全量数据计算，factor按秒采样计算
            while self.marketDataManager.idx < len(self.marketDataManager.tick_array)-1:
                self.marketDataManager.broadcast()
                if self.verbose > 0:
                    t0 = time.time()
                for fac in self.event_list+self.nonfactor_list:
                    if self.verbose >0 :
                        t1 = time.time()
                    calc_factor(fac)
                    if self.verbose >0 :
                        print(fac.__class__.__name__, time.time()-t1)
                for fac in self.factor_list:
                    if fac.__class__.__name__=="SeqNo":
                        # 需要SeqNo merge结果
                        calc_factor(fac)
                        continue
                    if self.marketDataManager.getPrevSampleFlag(1):
                        # 获取一秒采样的标志位, 满足采样标志位才计算
                        if self.verbose >0 :
                            t1 = time.time()
                        calc_factor(fac)
                        if self.verbose >0 :
                            print(fac.__class__.__name__, time.time()-t1)
                    else:
                        fac.addNanFactorValue()
                if self.verbose > 0:
                    print(f"==============={time.time()-t0}=================")

        elif mode.upper() == "ESAMPLE":
            print("WARNING: ESAMPLE只有在事件值非零时计算, 部分因子的计算结果可能不正确！比如按秒采样的因子，会错过很多计算机会！")
            # 只有在事件值非零时计算
            while self.marketDataManager.idx <len(self.marketDataManager.tick_array)-1:
                self.marketDataManager.broadcast()
                flag = False
                if self.verbose > 0:
                    t0 = time.time()
                # （1）先计算事件
                for fac in self.event_list:
                    if self.verbose > 0:
                        t1 = time.time()
                    calc_factor(fac)
                    single_flag = fac.getLastFactorValue()
                    if fac.factor_name not in self.sysinfo_list:
                        flag = bool(single_flag) | flag
                    if self.verbose >0 :
                        print(fac.__class__.__name__, time.time()-t1)
                # （2）满足事件条件时，才计算因子
                if flag:
                    for fac in self.nonfactor_list+self.factor_list:
                        # 需要SeqNo merge结果
                        if fac.__class__.__name__=="SeqNo":
                            calc_factor(fac)
                            continue
                        if self.verbose > 0:
                            t1 = time.time()
                        calc_factor(fac)
                        if self.verbose > 0:
                            print(fac.__class__.__name__, time.time() - t1)

                if self.verbose > 0:
                    print(f"==============={time.time()-t0}=================")
        else:
            raise Exception("计算模式仅支持FULL(全量)、SAMPLE_1S(1s采样)和ESAMPLE(事件触发)三种计算模式！")

    # @profile
    def get_all_factor_values(self, save_mode = False, save_base_dir = "/dfs/group/800657/library/l3_event/event_data/", keep_old_data = False):
        values = []
        columns = []
        values_event = []
        columns_event = []
        len_total = self.marketDataManager.idx+1
        symbol = self.marketDataManager.symbol
        date = self.marketDataManager.date
        ########################
        for factor in self.factor_list:
            value = factor.getFactorValue()
            if not len(value) == 0:
                # values.append(value.reshape(len_total, 1)) #用于concatenate
                if type(value[0]) == int:
                    value.astype(np.float64)
                values.append(value)
                columns.append(factor.factor_name)
            else:
                # values.append(np.full(len_total, np.nan).reshape(len_total, 1))
                values.append(np.full(len_total, np.nan))
                columns.append(factor.factor_name)

        for factor in self.event_list:
            value = factor.getFactorValue()
            if not len(value) == 0:
                # values.append(value.reshape(len_total, 1)) #用于concatenate
                if type(value[0]) == int:
                    value.astype(np.float64)
                values_event.append(value)
                columns_event.append(factor.factor_name)
            else:
                # values.append(np.full(len_total, np.nan).reshape(len_total, 1))
                values_event.append(np.full(len_total, np.nan))
                columns_event.append(factor.factor_name)
        ########################
        import pandas as pd
        import time

        if not os.path.exists(os.path.join(save_base_dir, "{}".format(symbol))):
            try:
                os.mkdir(os.path.join(save_base_dir, "{}".format(symbol)))
            except:
                time.sleep(0.1)
        # 主要耗时，在因子数更多时，需要polars优化性能
        # values1 = np.concatenate(values, axis = 1) #不支持混合类型，会把字段都转换为str
        values1 = np.rec.fromarrays(values, names=",".join(columns))
        if save_mode:
            value_df = pl.from_pandas(pd.DataFrame(values1, columns=columns)).with_columns(MDDate=pl.lit(date))
            if values_event:
                try:
                    values1_event = np.rec.fromarrays(values_event, names=",".join(columns_event))
                    value_df_event = pl.from_pandas(pd.DataFrame(values1_event, columns=columns_event)).with_columns(MDDate=pl.lit(date))
                    value_df = value_df_event.join(value_df,  on = "SeqNo", how = "left")
                except:
                    value_df_event =pd.DataFrame(values_event).T
                    value_df_event.columns=columns_event
                    value_df_event =  pl.from_pandas(value_df_event).with_columns(MDDate=pl.lit(date))
                    value_df = value_df_event.join(value_df,  on = "SeqNo", how = "left")
                target_columns = [col for col in value_df.columns if "_right" not in col]
                value_df = value_df.select(target_columns)
            save_path = os.path.join(save_base_dir, "{}/{}-{}.pqt".format(symbol, symbol, date))
            if os.path.exists(save_path):
                old_value_df = pl.read_parquet(save_path)
                old_value_df = old_value_df.cast({"SeqNo":pl.Int64})
                value_df = value_df.cast({"SeqNo":pl.Int64})
                old_target_columns = old_value_df.columns
                if len(old_value_df) != 0:
                    if not keep_old_data:
                        # 去除重名列, 保留新列
                        value_df = value_df.join(old_value_df, on = "SeqNo", suffix = '_right')
                        new_target_columns = [col for col in value_df.columns if "_right" not in col and col not in old_target_columns]
                        value_df = value_df.select(old_target_columns+new_target_columns)
                    else:
                        # 去除重名列，保留旧列
                        value_df = old_value_df.join(value_df, on = "SeqNo", suffix = '_right')
                        target_columns = [col for col in value_df.columns if "_right" not in col]
                        value_df = value_df.select(target_columns)
            # ESAMPLE模式下，部分SeqNo的Factor可能为null，用0值填充
            value_df = value_df.fill_null(0)
            value_df.write_parquet(save_path)
        else:
            value_df = pd.DataFrame(values1, columns=columns)
            value_df["MDDate"] = date
        return value_df

    def get_all_factor_names(self):
        event_names = [i.factor_name for i in self.event_list]
        factor_names = [i.factor_name for i in self.factor_list if i.factor_name!="SeqNo"]
        return event_names+factor_names

    def get_error_instance(self):
        return self.error_list

