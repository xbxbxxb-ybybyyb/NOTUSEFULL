import json
import hashlib
import os
import pandas as pd
import time
import pickle
from .save_to_mongo import MongoDB
import inspect
from xquant.factordata import FactorData
from xquant.setXquantEnv import xquantEnv
import re
from artifacts import model_save_and_evaluate
from artifacts import online_model
from artifacts import backtest_save_and_evaluate
import traceback
from copy import deepcopy


def is_folder_empty(folder_path):
    with os.scandir(folder_path) as entries:
        for entry in entries:
            if entry.is_file() or entry.is_dir():
                return False
    return True


class ExpArtifacts:
    """
    管理一次实验中，模型训练和策略回测相关的数据和成果。
    """

    def __init__(self, exp_name):
        """
        :param exp_name:
        """
        self.exp_name = exp_name
        if xquantEnv == 0:
            self.exp_path = os.path.join("/data/user/quanttest007/013150/exp_result/", self.exp_name)
        else:
            self.exp_path = os.path.join("/data/user/016869/exp_result/", self.exp_name)

        self.is_activated = False
        self.exp_version_path = None
        self.version_alias = None

        self.db = MongoDB()
        self.__make_dirs()
        self.model_config_dict = None
        self.model_long_value_d = None
        self.fa = FactorData()

    def path_of_exp_version(self):
        if self.exp_version_path:
            return self.exp_version_path
        else:
            raise Exception("请先调用activate_version_to_save绑定实验版本号！")

    def path_of_signal_process_save(self, evaluate_type="single_label_th_classify", version_alias = None, **kwargs):
        if not self.exp_version_path:
            if not version_alias:
                raise Exception("请指定version_alias参数，指定实验版本号！")
            else:
                signal_process_save_path_single_label_th_classify = "f\""+os.path.join(self.exp_path,
                                                                                 version_alias,
                                                                                "{label_name}-{symbol}",
                                                                                "label_th@{'%.1f'%label_th1}-probs_up@{'%.2f'%probs_up}-probs_dw@{'%.2f'%probs_dw}/",
                                                                                "signal_files_processed")+"\""
        else:
            signal_process_save_path_single_label_th_classify = self.signal_process_save_path_single_label_th_classify

        for key, value in kwargs.items():
            # 将关键字参数转换为变量
            # exec(f"{key} = '{value}'")
            locals()[key] = value
        if evaluate_type == "single_label_th_classify":
            try:
                return eval(signal_process_save_path_single_label_th_classify)
            except:
                print(traceback.print_exc())
                raise Exception("路径信息缺少初始化变量！")
        else:
            raise Exception("evaluate_type仅支持以下范围：[single_label_th_classify]")

    def path_of_backtest_signal_process_save(self, evaluate_type="single_label_th_classify", **kwargs):
        for key, value in kwargs.items():
            # 将关键字参数转换为变量
            # exec(f"{key} = '{value}'")
            locals()[key] = value
        if evaluate_type == "single_label_th_classify":
            try:
                # 解析信号名称和标的
                label, stock = os.path.basename(os.path.abspath(
                    os.path.join(self.backtest_signal_process_save_path_single_label_th_classify, "../.."))).split("-")
                return eval(self.backtest_signal_process_save_path_single_label_th_classify)
            except:
                print(traceback.print_exc())
                raise Exception("路径信息缺少初始化变量！")
        else:
            raise Exception("evaluate_type仅支持以下范围：[single_label_th_classify]")

    def activate_version_to_save(self, model_config, version_alias):
        # TODO: 测试用例覆盖, 在notebook中运行，多次实例化ExpArtifacts时
        if not isinstance(version_alias, str):
            raise ValueError(f"version_alias: {version_alias} 应为str类型！")
        self.model_config_dict = model_config
        # self.__check_and_save_config_version(model_config, version_alias, reg_type="model")
        if not self.version_alias:
            self.version_alias = version_alias
        if self.version_alias != version_alias:
            raise Exception(f"version_alias只能初始化一次，当前的version_alais为{self.version_alias}")
        self.exp_version_path = os.path.join(self.exp_path, self.version_alias)
        self.model_save_path = os.path.join(self.exp_version_path, "saved_models")
        self.signal_save_path = os.path.join(self.exp_version_path, "signal_files")
        self.signal_process_base_dir_single_label_th_classify = os.path.join(self.exp_version_path,
                                                                             "{label_name}-{symbol}",
                                                                             "label_th@{'%.1f'%label_th1}-probs_up@{'%.2f'%probs_up}-probs_dw@{'%.2f'%probs_dw}/")

        self.signal_process_save_path_single_label_th_classify = "f\"" + os.path.join(
            self.signal_process_base_dir_single_label_th_classify,
            "signal_files_processed") + "\""
        self.backtest_signal_process_save_path_single_label_th_classify = "f\"" + os.path.join(
            self.signal_process_base_dir_single_label_th_classify,
            "{strategy_name}-{strategy_version_alis}",
        ) + "\""
        print("*" * 15 + "路径信息" + "*" * 15)
        print("EXP_VERSION_PATH: ", self.exp_version_path)
        print("SIGNAL_PROCESS_BASE_DIR: ", self.signal_process_base_dir_single_label_th_classify)
        print("*" * 38)
        # print("signal_process_save_path_single_label_th_classify:", self.signal_process_save_path_single_label_th_classify)
        # print("backtest_signal_process_save_path_single_label_th_classify: ", self.backtest_signal_process_save_path_single_label_th_classify)
        self.is_activated = True

    def regist_config(self, config, config_alias, reg_type="strategy", **kwargs):
        assert reg_type in ["strategy", "model"], "参数类型必须为strategy或model"
        config_c = deepcopy(config)
        version = self.__check_and_save_config_version(config_c, config_alias, reg_type="strategy", **kwargs)
        return version

    def get_regist_config(self, config_alias):
        df_v = self.load_exp_params(version_alias=config_alias)
        if df_v.empty:
            print("没有config_alias：{} 对应的参数信息！".format(config_alias))
            return
        if "params_jsonstr" in df_v.columns.tolist():
            params_jsonstr = df_v.iloc[0]["params_jsonstr"]
            params = json.loads(params_jsonstr)
        else:
            print("没有config_alias：{} 对应的参数信息！".format(config_alias))
            return
        if "params_jsonstr_extra" in df_v.columns.tolist():
            params_jsonstr_extra = df_v.iloc[0]["params_jsonstr_extra"]
            params_extra = json.loads(params_jsonstr_extra)
            for key in list(params_extra.keys()):
                key_lst = key.split("|")
                # 剔除较长字段时只遍历了两层
                if len(key_lst) == 2:
                    params[key_lst[0]][key_lst[1]] = params_extra[key]
                elif len(key_lst) == 3:
                    params[key_lst[0]][key_lst[1]][key_lst[2]] = params_extra[key]
        return params

    def __make_dirs(self, model_path=None):
        if not os.path.exists(self.exp_path):
            os.makedirs(self.exp_path)
        if model_path and not os.path.exists(model_path):
            os.makedirs(model_path)

    def __list_format(self, list_data):
        # 把列表中的所有单个元素都转为str类型
        for i in range(len(list_data)):
            if isinstance(list_data[i], list):
                self.__list_format(list_data[i])
            else:
                list_data[i] = str(list_data[i])
        return list_data

    def __sort_list(self, list_data):
        # 把嵌套列表最里层的列表做排序然后转为str
        for i in range(len(list_data)):
            if isinstance(list_data[i], list):
                try:
                    list_data[i].sort()
                    list_data[i] = str(list_data[i])
                except TypeError:
                    self.__sort_list(list_data[i])
        return list_data

    def sort_list(self, list_data):
        # 把单个元素都转为str类型
        list_data = self.__list_format(list_data)
        types = [isinstance(ld, list) for ld in list_data]
        # 对列表的嵌套列表从最内层逐层排序并转为str
        while True in types:
            list_data = self.__sort_list(list_data)
            types = [isinstance(ld, list) for ld in list_data]
        # 最后对所有的str类型排序
        list_data.sort()
        return list_data

    def get_target_key(self, config_d, target_key):
        for key, value in config_d.items():
            if key == target_key:
                return value
            else:
                if isinstance(value, dict):
                    res = self.get_target_key(value, target_key)
                    if res:
                        return res
        return []

    def align_dict(self, mapping):
        # 规范字典元素，使其为列表的值排序后返回
        for key, value in mapping.items():
            if isinstance(value, dict):
                self.align_dict(mapping[key])
            elif isinstance(value, list):
                value1 = self.sort_list(value)
                mapping[key] = value1
            else:
                mapping[key] = value
        return mapping

    def get_version_by_config(self, config_dict):
        """
        根据config_dict生成版本号
        :param config_dict:
        :return:
        """
        assert type(config_dict) == dict
        # 如果config_dict的value类型为是list，或者dict，需要对value内容排序之后，再生成版本号
        # 生成版本号的dict不包含版本号别名
        if "version_alias" in config_dict:
            del config_dict["version_alias"]
        # 把配置文件转为json排序嵌套的字典元素
        config_dict_d = json.dumps(config_dict, sort_keys=True, separators=(",", ":"))
        # 转为字典
        config_dict_l = json.loads(config_dict_d)
        # 格式化
        config_dict_a = self.align_dict(config_dict_l)
        config_json_new = json.dumps(config_dict_a, sort_keys=True, separators=(",", ":"))
        version = hashlib.sha256(config_json_new.encode()).hexdigest()
        return version

    def __check_long_value(self, ddict, limit_len=10):
        # 暂时只校验字典的前两层，如果为列表的值内有字典元素则不做剔除
        long_value_d = {}
        for key1 in list(ddict.keys()):
            if isinstance(ddict[key1], dict):
                for key2 in list(ddict[key1].keys()):
                    # 如果值类型为float或int等则len()会报错
                    # 如果值的长度大于给定值，则把字段中的该键值对删除，添加到long_value_d
                    if isinstance(ddict[key1][key2], list):
                        # 如果为列表的值内有字典元素则不做剔除
                        dict_b = [isinstance(i, dict) for i in ddict[key1][key2]]
                        if sum(dict_b) == 0 and len(ddict[key1][key2]) >= limit_len:
                            uk = key1 + "|" + key2
                            long_value_d[uk] = ddict[key1][key2]
                            del ddict[key1][key2]
            elif isinstance(ddict[key1], list):
                if len(ddict[key1]) >= limit_len:
                    long_value_d[key1] = ddict[key1]
                    del ddict[key1]
        return ddict, long_value_d

    def __save_params_json(self, save_path):
        # 保存参数文件，分为两部分，一部分是value特别长的参数，一部分是剩下的
        # 全参数json文件
        with open(os.path.join(save_path, "params_jsonstr.json"), "w") as fp:
            json.dump(self.model_config_dict, fp)
        # 未参与参数版本号计算的key的参数json文件
        if self.model_long_value_d:
            with open(os.path.join(save_path, "params_jsonstr_extra.json"), "w") as fp:
                json.dump(self.model_long_value_d, fp)

    def __check_and_save_config_version(self, config_dict, version_alias, reg_type="model", **kwargs):
        """
        :param config_dict:
        :return:
        """
        if type == "model":
            assert "factor_name_list" in config_dict.keys(), "模型参数必须key包含factor_name_list!"
            assert "tagger_name_list" in config_dict.keys(), "模型参数必须key包含tagger_name_list!"
            assert "symbol_list" in config_dict.keys(), "模型参数必须key包含symbol_list!"
            assert "train_start_time" in config_dict.keys(), "模型参数必须key包含train_start_time!"
            assert "train_end_time" in config_dict.keys(), "模型参数必须key包含train_end_time!"
            assert "valid_start_time" in config_dict.keys(), "模型参数必须key包含valid_start_time!"
            assert "valid_end_time" in config_dict.keys(), "模型参数必须key包含valid_end_time!"
            assert "test_start_time" in config_dict.keys(), "模型参数必须key包含test_start_time!"
            assert "test_end_time" in config_dict.keys(), "模型参数必须key包含test_end_time!"

        config_dict_c = deepcopy(config_dict)
        config_dict_c_str = str(config_dict_c)
        stock_pattern = re.compile(r"\d{6}.SZ|\d{6}.SH")
        config_dict_c_str = re.sub(stock_pattern, "$SECURITYID", config_dict_c_str)
        config_dict_c = eval(config_dict_c_str)

        config_dict_v, model_long_value_d = self.__check_long_value(config_dict_c, 10)
        if reg_type == "model":
            self.model_long_value_d = model_long_value_d
        version_new = self.get_version_by_config(config_dict_v.copy())
        json_df = self.db.load_configs()
        if json_df.empty:
            version_alias_list = []
            version_list = []
        else:
            # 版本号别名
            version_alias_list = json_df["version_alias"].tolist()
            # 版本号-hash256值
            version_list = json_df["hash256"].tolist()
        if version_alias in version_alias_list:
            # 若版本号别名已存在，要求新旧参数版本号必须一致
            version_old = json_df[json_df["version_alias"] == version_alias].iloc[0]["hash256"]
            assert version_new == version_old, "历史实验已存储和当前version_alias相同的参数，如果是新参数实验，请设置一个不同的version_alias！"
        elif version_new in version_list:
            # 若版本号已存在，要求新旧版本号别名必须一致，让用户用以前的版本号别名
            version_alias_old = json_df[json_df["hash256"] == version_new].iloc[0]["version_alias"]
            assert version_alias == version_alias_old, f"历史实验已存在该参数版本号，对应参数别名为{version_alias_old},请设置一个相同的version_alias！"
        else:
            # 保存一条数据到mongoDB表结构
            config_dict_json = json.dumps(config_dict_v, sort_keys=True, separators=(",", ":"))
            if model_long_value_d:
                params_jsonstr_extra = json.dumps(model_long_value_d, sort_keys=True, separators=(",", ":"))
            else:
                params_jsonstr_extra = None
            if reg_type == "model":
                exp_type = "model_config"
            elif reg_type == "strategy":
                exp_type = "strategy_config"
            else:
                raise ValueError("【reg_type】参数暂时只支持model、strategy")

            self.db.exp_params_todb(exp_id=self.exp_name, version_alias=version_alias,
                                    hash256=version_new, exp_type=exp_type,
                                    params_jsonstr=config_dict_json,
                                    params_jsonstr_extra=params_jsonstr_extra)
        if reg_type == "model":
            params_json_path = os.path.join(self.exp_path, version_alias)
            self.__make_dirs(params_json_path)
            if not os.path.exists(os.path.join(params_json_path, "params_jsonstr.json")):
                self.__save_params_json(params_json_path)
        elif reg_type == "strategy":
            for k, v in kwargs.items():
                locals()[k] = v
            params_json_path = eval(self.backtest_signal_process_save_path_single_label_th_classify)
            self.__make_dirs(params_json_path)
            if not os.path.exists(os.path.join(params_json_path, "params_jsonstr.json")):
                with open(os.path.join(params_json_path, "params_jsonstr.json"), "w") as fp:
                    json.dump(config_dict, fp)
                if model_long_value_d:
                    with open(os.path.join(params_json_path, "params_jsonstr_extra.json"), "w") as fp:
                        json.dump(config_dict, fp)
        else:
            raise ValueError("【reg_type】参数暂时只支持model、strategy")

        return version_new

    def model_file_save(self, model_obj, mode, overwrite=False):
        """
        :param model_obj:
        :param mode:
        :param overwrite:
        :return:
        """
        assert self.is_activated, "要存储数据必须先调用activate_version_to_save方法，指定实验版本号！"
        model_save_path = self.model_save_path
        self.__make_dirs(model_save_path)

        factor_name_list = self.get_target_key(self.model_config_dict, "factor_name_list")
        if type(mode) == str:
            mode = [mode]
        exists_flag = False
        if "pickle" in mode or "pkl" in mode:
            exists_flag = os.path.exists(os.path.join(model_save_path, "tmp_model.pickle.dat")) or exists_flag
        elif "onnx" in mode:
            exists_flag = os.path.exists(os.path.join(model_save_path, "model.onnx")) or exists_flag

        # 如果模型文件存在且overwrite为True则覆盖写入，或模型文件不存在直接写入，否则备份后再写入
        if not exists_flag:
            model_save_and_evaluate.save_model_and_factor_list(factor_name_list, model_obj, mode, model_save_path)
        else:
            if overwrite == True:
                # 如，将原本的self.exp_path备份为self.exp_path_20231023093030，再创建一个新的self.exp_path
                date = time.strftime("%Y%m%d%H%M%S")
                bak_path = self.exp_version_path + "_" + date
                print(f"将重写模型文件，原本的实验版本号已备份为：{bak_path}。")
                os.system("mv {} {}".format(self.exp_version_path, bak_path))
                self.__make_dirs(model_save_path)
                if not os.path.exists(os.path.join(self.exp_version_path, "params_jsonstr.json")):
                    self.__save_params_json(self.exp_version_path)
                model_save_and_evaluate.save_model_and_factor_list(factor_name_list, model_obj, mode, model_save_path)
            else:
                raise Exception("模型文件已存在，若要覆盖存储，请设置overwrite参数为True！")
        # collection是操作的Mongo集合名，不涉及mongo则传“-”，operate是操作类型，可以写get，insert，update，load
        self.db.user_event_todb(exp_id=self.exp_name, version_alias=self.version_alias,
                                event_type=inspect.currentframe().f_code.co_name,
                                collection="-", operate="insert",
                                params={"mode": mode, "overwrite": overwrite})
        print("模型文件保存完毕")
        return True

    def model_file_load(self, version_alias, mode="pickle"):
        if mode not in ["pickle", "pkl", "onnx"]:
            raise ValueError("mode参数只支持: pickle, pkl, onnx.")
        model_save_path = os.path.join(self.exp_path, version_alias, "saved_models")
        if not os.path.exists(model_save_path):
            raise Exception("暂无version_alias：{}的模型文件存储路径：{}".format(version_alias, model_save_path))
        model_obj = model_save_and_evaluate.load_model(mode, model_save_path)
        self.db.user_event_todb(exp_id=self.exp_name, version_alias=self.version_alias,
                                event_type=inspect.currentframe().f_code.co_name,
                                collection="-", operate="get", params={"mode": mode})
        return model_obj

    def model_signal_save(self, label_name, symbol, tm_values, yhat_values, y_values,
                          target_values, period=120, target_type="mid", increment=False):
        """
        信号文件存储到指定位置, 原始格式存储，不包含5分类信息
        :param model_config:
        :param version_alias:
        :param label_name:
        :param symbol:
        :param tm_values:
        :param yhat_values:
        :param y_values:
        :param target_values:
        :param period:
        :param target_type:
        :return:
        """
        assert self.exp_version_path, "要存储数据必须先调用activate_version_to_save方法，指定实验版本号！"
        signal_save_path = self.signal_save_path
        self.__make_dirs(signal_save_path)
        sig_df = model_save_and_evaluate.generate_signal_without_class(t_values=tm_values, yhat_values=yhat_values,
                                                                       y_values=y_values,
                                                                       target_values=target_values, period=period,
                                                                       target_type=target_type)
        parquet_name = os.path.join(signal_save_path, f"{label_name}-{symbol}.parquet")
        print("save signal source file:  ", parquet_name)
        if not increment:
            sig_df.to_parquet(parquet_name)
        else:
            if not os.path.exists(parquet_name):
                sig_df.to_parquet(parquet_name)
            else:
                self.__signal_increment(parquet_name, sig_df)
        self.db.user_event_todb(exp_id=self.exp_name, version_alias=self.version_alias,
                                event_type=inspect.currentframe().f_code.co_name,
                                collection="-", operate="insert",
                                params={"label_name": label_name, "symbol": symbol, "period": period,
                                        "target_type": target_type})
        return sig_df



    def __signal_increment(self, sig_path, sig_df_incre):
        sig_df_old = pd.read_parquet(sig_path)
        incre_index = sig_df_incre.index
        sig_df_old = sig_df_old[~sig_df_old.index.isin(incre_index)]
        sig_df_new = pd.concat([sig_df_old, sig_df_incre])
        sig_df_new.sort_index(inplace=True)
        sig_df_new.to_parquet(sig_path)
        return sig_df_new

    def model_signal_load(self, version_alias, label_name, symbol):
        """
        加载信号数据
        :param version_alias:
        :param label_name:
        :param symbol:
        :return:
        """
        signal_save_path = os.path.join(self.exp_path, version_alias, "signal_files")
        sig_df = pd.read_parquet(os.path.join(signal_save_path, f"{label_name}-{symbol}.parquet"))
        self.db.user_event_todb(exp_id=self.exp_name, version_alias=self.version_alias,
                                event_type=inspect.currentframe().f_code.co_name,
                                collection="-", operate="get",
                                params={"version_alias": version_alias, "label_name": label_name, "symbol": symbol})
        return sig_df

    def model_signal_process_single_label_th_classify(self, label_name, symbol, label_th1, probs_up, probs_dw,
                                                      label_th2=2, njobs=None):
        assert self.is_activated, "要存储数据必须先调用activate_version_to_save方法，指定实验版本号！"
        signal_df = self.model_signal_load(self.version_alias, label_name, symbol)
        signal_process_base_dir = eval(self.signal_process_save_path_single_label_th_classify)
        self.__make_dirs(signal_process_base_dir)
        # 五分类转换
        sig_df, table1_json, table2_json = model_save_and_evaluate.generate_probs_single_label_th_classify(signal_df,
                                                                                                           label_th1,
                                                                                                           label_th2,
                                                                                                           probs_up,
                                                                                                           probs_dw,
                                                                                                           amp=6,
                                                                                                           symbol = symbol,
                                                                                                           signal_process_base_dir = signal_process_base_dir
                                                                                                           )
        with open(os.path.join(os.path.dirname(signal_process_base_dir), f"th{'%.1f' % label_th1}_table1.json"),
                  "w") as f:
            json.dump(table1_json, f, indent=4)

        with open(os.path.join(os.path.dirname(signal_process_base_dir), f"th{'%.1f' % label_th2}_table2.json"),
                  "w") as f:
            json.dump(table2_json, f, indent=4)

        print(
            "########### label_th1:{}  probs_up:{}  probs_dw:{} ###############".format(label_th1, probs_up, probs_dw))
        print("signal_process_base_dir:", signal_process_base_dir)
        self.db.user_event_todb(exp_id=self.exp_name, version_alias=self.version_alias,
                                event_type=inspect.currentframe().f_code.co_name,
                                collection="-", operate="insert",
                                params={"label_name": label_name, "symbol": symbol, "label_th1": label_th1,
                                        "probs_up": probs_up, "probs_dw": probs_dw, "label_th2": label_th2})
        return True

    def model_signal_evalatioin_single_label_th_classify(self, label_name, symbol, label_th=1.1,
                                                         pred_th_abs_limits=[1, 6.0],
                                                         start_date=None, end_date=None):
        """
        :param signal_df: 信号标签和预测值的DataFrame，sig_df必须满足标准格式（给出标准格式说明）。
        :param label_name:
        :param label_th:
        :param pred_th_abs_limits:
        :return:
        """
        assert self.is_activated, "要存储数据必须先调用activate_version_to_save方法，指定实验版本号！"
        signal_df = self.model_signal_load(self.version_alias, label_name, symbol)
        Y_test, Y_test_pred, T_test = signal_df["LABEL_VALUE"].values, signal_df[
            "PREDICTED"].values, signal_df.index.values
        if not start_date and not end_date:
            start_date, end_date = str(T_test[0])[:10].replace("-", ""), str(T_test[-1])[:10].replace("-", "")
        print(f"singal_evaluate: start_date {start_date}, end_date {end_date}.")
        df_th1, df_th2 = model_save_and_evaluate.evaluate_signal_auc_table_by_day(Y_test, Y_test_pred, T_test, label_th=label_th,
                                                                    start_date=start_date,
                                                                    end_date=end_date,
                                                                    reg_eval_abs_limits=pred_th_abs_limits)
        # 信号评价数据入mongoDB
        self.db.signal_evaluation_data_todb(exp_id=self.exp_name, version_alias=self.version_alias,
                                            symbol=symbol, evaluation_type="single_label_th_classify",
                                            condition={"label_name": label_name,
                                                       "label_th": label_th},
                                            metrics=df_th1)
        self.db.user_event_todb(exp_id=self.exp_name, version_alias=self.version_alias,
                                event_type=inspect.currentframe().f_code.co_name,
                                collection="signal_evaluation_data", operate="insert",
                                params={"label_name": label_name, "symbol": symbol, "label_th": label_th,
                                        "pred_th_abs_limits": pred_th_abs_limits, "start_date": start_date,
                                        "end_date": end_date})
        return df_th1, df_th2

    def backtest_trade_file_save(self, strategy_name, strategy_config_alias, signal_process_base_dir, trade_records_df):
        assert self.is_activated, "要存储数据必须先调用activate_version_to_save方法，指定实验版本号！"
        trade_save_path = signal_process_base_dir.replace("signal_files_processed",
                                                          f"{strategy_name}-{strategy_config_alias}")
        print("trade_records_save_path:", trade_save_path)
        self.__make_dirs(trade_save_path)
        if not trade_records_df.empty:
            dates = sorted(set(trade_records_df["tradeDate"].tolist()))
            for date in dates:
                trade_records_df[trade_records_df["tradeDate"] == date].to_parquet(
                    os.path.join(trade_save_path, f"{date}_trade_records.parquet"))
            return True

    def backtest_trade_file_load(self, strategy_name, strategy_config_alias, signal_process_base_dir, start_date,
                                 end_date):
        assert self.exp_version_path, "要存储数据必须先调用activate_version_to_save方法，指定实验版本号！"
        trade_save_path = signal_process_base_dir.replace("signal_files_processed",
                                                          f"{strategy_name}-{strategy_config_alias}")
        print("trade_records_save_path:", trade_save_path)
        self.__make_dirs(trade_save_path)
        dates = self.fa.tradingday(str(start_date).replace("-", ""), str(end_date).replace("-", ""))
        result_list = []
        for date in dates:
            date = date[:4] + "-" + date[4:6] + "-" + date[6:]
            trade_records_df = pd.read_parquet(os.path.join(trade_save_path, f"{date}_trade_records.parquet"))
            result_list.append(trade_records_df)
        result_df = pd.concat(result_list)
        self.db.user_event_todb(exp_id=self.exp_name, version_alias=self.version_alias,
                                event_type=inspect.currentframe().f_code.co_name,
                                collection="-", operate="insert",
                                params={"strategy_name": strategy_name,
                                        "signal_process_base_dir": signal_process_base_dir})
        return result_df

    def backtest_trade_evaluation(self, strategy_name, strategy_config_alias, signal_process_base_dir,
                                  trade_records_df):
        assert self.is_activated, "要存储数据必须先调用activate_version_to_save方法，指定实验版本号！"
        trade_save_path = signal_process_base_dir.replace("signal_files_processed",
                                                          f"{strategy_name}-{strategy_config_alias}")
        print("trade_summary_save_path:", trade_save_path)
        self.__make_dirs(trade_save_path)
        self.db.user_event_todb(exp_id=self.exp_name, version_alias=self.version_alias,
                                event_type=inspect.currentframe().f_code.co_name,
                                collection="-", operate="insert",
                                params={"strategy_name": strategy_name,
                                        "signal_process_base_dir": signal_process_base_dir})
        if not trade_records_df.empty:
            dates = sorted(set(trade_records_df["tradeDate"].tolist()))
            result_list = []
            for date in dates:
                trade_summary = backtest_save_and_evaluate.evaluate_trade_summary(
                    trade_records_df[trade_records_df["tradeDate"] == date])
                result_list.append(trade_summary)
            result_df = pd.concat(result_list)
            result_df.rename(columns={"监控日期": "monitor_date", "回测日期": "date",
                                      "标的": "symbol", "敞口数量": "position",
                                      "买成交金额": "buy_amt", "卖成交金额": "sell_amt",
                                      "买成交数量": "buy_qty", "卖成交数量": "sell_qty",
                                      "下单次数": "created_cnt", "成交次数": "filled_cnt",
                                      "撤单次数": "cancelled_cnt", "买成交金额(去除敞口)": "buy_amt_no_pos",
                                      "卖成交金额(去除敞口)": "sell_amt_no_pos", "回转盈亏": "pnl_no_pos",
                                      "税后回转盈亏": "pure_pnl_no_pos", "敞口盈亏": "pnl_only_pos",
                                      "税后收益率": "ret", "年化收益率": "ret_annual"}, inplace=True)
            result_df.to_excel(os.path.join(trade_save_path, f"{date}_trade_summary.xlsx"))
            symbol = result_df.iloc[0]["symbol"]
            # TODO strategy_params生成strategy的版本号！！！
            summary_path_lst = trade_save_path.split("/")
            condition = {}
            condition["signal_name"] = summary_path_lst[8].split("-")[0]
            pattern = r"(\w+)&(\d+\.\d+)"
            signal_params = re.findall(pattern, summary_path_lst[9])
            for k, v in signal_params:
                condition.update({k: v})
            # TODO strategy_params需要赋值策略的参数版本号，怎么获取？
            self.db.backtest_evaluation_data_todb(exp_id=self.exp_name, version_alias=strategy_config_alias,
                                                  symbol=symbol, strategy_name=strategy_name,
                                                  strategy_params="strategy_params",
                                                  backtest_evaluation_type="T0", condition=condition, metrics=result_df)
            return result_df
        else:
            return pd.DataFrame()

    def backtest_plot_signal_only(self, signal_df_day, plot_save_dir="./"):
        """
        :param signal_df_day: 单天的dataframe
        :return:
        """
        fig_signal1 = backtest_save_and_evaluate.plot_signal_fig_only(signal_df_day)
        date = str(signal_df_day["PERIOD_BEGIN"].iloc[0])[:10]
        self.__make_dirs(plot_save_dir)
        with open(os.path.join(plot_save_dir, "plot_signal_{}.html".format(date)), "w") as f:
            f.write(fig_signal1.to_html(full_html=False))
            print("save signal plot file ok! {}".format(os.path.join(plot_save_dir, "plot_{}.html".format(date))))
        self.db.user_event_todb(exp_id=self.exp_name, version_alias=self.version_alias,
                                event_type=inspect.currentframe().f_code.co_name,
                                collection="-", operate="plot",
                                params={"-": "plot"})

    def backtest_plot_signal_trade(self, signal_df_day, trade_records_df_day, ma_df_day=None, plot_save_dir="./"):
        date = str(signal_df_day["PERIOD_BEGIN"].iloc[0])[:10]
        symbol = signal_df_day["SYMBOL"].iloc[0]

        if not isinstance(ma_df_day, pd.DataFrame):
            from MDCDataProvider.MDCDataProvider import MDCDataProvider
            mdc = MDCDataProvider()
            ma_df_day = mdc.get_data_by_date("STOCK", symbol, date.replace("-", ""))
            mdc.dfs.close()
            del mdc
        if ma_df_day.empty:
            raise Exception("ma_df_day为空DataFrame.")
        self.__make_dirs(plot_save_dir)
        fig_signal1, fig_signal2 = backtest_save_and_evaluate.plot_signal_trade_fig(signal_df_day, trade_records_df_day,
                                                                                    ma_df_day, plot=False)

        with open(os.path.join(plot_save_dir, "plot_signal_trade_{}.html".format(date)), "w") as f:
            f.write(fig_signal1.to_html(full_html=False))
        with open(os.path.join(plot_save_dir, "plot_signal_trade_{}.html".format(date)), "a") as f:
            f.write(fig_signal2.to_html(full_html=False))
            print("save signal&trade plot file ok! {}".format(os.path.join(plot_save_dir, "plot_{}.html".format(date))))
        self.db.user_event_todb(exp_id=self.exp_name, version_alias=self.version_alias,
                                event_type=inspect.currentframe().f_code.co_name,
                                collection="-", operate="plot",
                                params={"-": "plot"})

    def load_exp_params(self, version_alias=None, hash256=None):
        df = self.db.load_configs(version_alias, hash256, params_jsonstr=None, params_jsonstr_extra=None)
        return df

    def load_user_event(self, exp_id=None, version_alias=None, operate=None, event_type=None, collection=None):
        df = self.db.load_user_event(exp_id, version_alias, operate, event_type, collection)
        return df

    def load_signal_evaluation_data(self, exp_id=None, symbol=None, version_alias=None, evaluation_type=None):
        df = self.db.load_signal_evaluation_data(exp_id, symbol, version_alias, evaluation_type)
        return df

    def load_backtest_evaluation_data(self, exp_id=None, symbol=None, version_alias=None,
                                      backtest_evaluation_type=None):
        df = self.db.load_backtest_evaluation_data(exp_id, symbol, version_alias, backtest_evaluation_type)
        return df

    def load_formal_factor_evaluation_data(self):
        pass
