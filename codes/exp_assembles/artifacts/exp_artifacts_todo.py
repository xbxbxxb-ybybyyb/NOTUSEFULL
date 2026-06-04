import json
import hashlib
import os
import pandas as pd
import time
from artifacts.save_to_mongo import MongoDB
from FactorProvider.conf.DubboConf import get_userid
from xquant.setXquantEnv import xquantEnv
from artifacts import model_save_and_evaluate
from artifacts import backtest_save_and_evaluate
from artifacts import online_model
from copy import deepcopy

def is_folder_empty(folder_path):
    # ?
    with os.scandir(folder_path) as entries:
        for entry in entries:
            if entry.is_file() or entry.is_dir():
                return False
    return True


class ExpArtifacts:
    """
    管理一次实验中，模型训练和策略回测相关的数据和成果。
    """

    __instance = None

    # def __new__(cls, *args, **kwargs):
    #     # 单例，同一个exp_name，只能有一个实例, 按版本号来控制单例
    #     if cls.__instance:
    #         return cls.__instance
    #     else:
    #         obj = super(ExpArtifacts, cls).__new__(cls)
    #         cls.__instance = obj
    #         return cls.__instance

    def __init__(self, exp_name):
        """
        :param exp_name:
        """
        self.exp_name = exp_name
        if xquantEnv == 0:
            self.exp_path = os.path.join("/data/user/quanttest007/013150/exp_result/", self.exp_name)
        else:
            self.exp_path = os.path.join("/data/user/016869/exp_result/", self.exp_name)
        self.exp_base_path = os.path.join(self.exp_path)
        self.exp_version_path = None
        self.version_alias = None
        self.db = MongoDB()
        self.__make_dirs()
        self.user_id = get_userid()


    def regist_config(self, config, config_alias, type = "strategy"):
        assert type in ["strategy", "model"], "参数类型必须为strategy或model"
        config = deepcopy(config)
        self.__check_and_save_config_version(config, config_alias)

    def get_regist_config(self, config_alias, type = "strategy"):
        pass



    def activate_version_to_save(self, model_config, version_alias):
        # TODO: 测试用例覆盖, 在notebook中运行，多次实例化ExpArtifacts时
        # TODO: 给出最佳实践，最好不要把时间、标的字段作为参数一部分计算
        # 带存储功能的接口，包扩文件存储和评价数据存储，需确保都是同一版本号
        model_config = deepcopy(model_config)
        self.__check_and_save_config_version(model_config, version_alias)
        if not self.version_alias:
            self.version_alias = version_alias
        if self.version_alias != version_alias:
            raise Exception(f"version_alias只能初始化一次，当前的version_alais为{self.version_alias}")
        self.exp_version_path = os.path.join(self.exp_path, self.version_alias)
        self.model_save_path = os.path.join(self.exp_version_path, "saved_models")
        self.signal_save_path = os.path.join(self.exp_version_path, "signal_files")
        self.signal_process_save_path_single_label_th_classify = os.path.join(self.exp_version_path, "signal_files_process/{label_name}-{symbol}", "label_th{'%.1f'%label_th1}-probs_up{'%.2f'%probs_up}-probs_dw{'%.2f'%probs_dw}/")


    def __make_dirs(self, model_path=None):
        if not os.path.exists(self.exp_path):
            os.makedirs(self.exp_path)
        if not os.path.exists(self.exp_base_path):
            os.makedirs(self.exp_base_path)
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

    # def sort_list(self, list_data):
    #     # 列表排序
    #     if not isinstance(list_data, list):
    #         raise Exception("只接受list类型传参！")
    #     list_data = self.__list_format(list_data)
    #     # TODO 暂时只把list的前两层转为str并排序
    #     list_new = [str(i) for i in list_data]
    #     return list_new

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

    def __get_version_by_config(self, config_dict):
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

    def __check_and_save_config_version(self, config_dict, version_alias):
        """
        :param config_dict:
        :return:
        """
        # 校验value，如果value过长，择出来，不参与version计算, 单独存到save_model目录下以及数据库里存。如factors.csv
        # with open(os.path.join(savepath, "factors.csv"), "w") as f:
        #     for v in factor_name_list:
        #         f.write(json.dumps(v))
        #         f.write(",\n")
        # print("Save factor list successed")

        version_alias_new = version_alias
        config_dict_v, long_value_d = self.__check_long_value(config_dict, 10)

        version_new = self.__get_version_by_config(config_dict_v.copy())
        json_df = self.db.load_configs()
        # 版本号别名
        version_alias_list = json_df["version_alias"].tolist()
        # 版本号-hash256值
        version_list = json_df["hash256"].tolist()
        if version_alias_new in version_alias_list:
            # 若版本号别名已存在，要求新旧参数版本号必须一致
            version_old = json_df[json_df["version_alias"] == version_alias_new].iloc[0]["hash256"]
            assert version_new == version_old, "历史已存在同名version_alias，但本参数和历史参数不一致！请为当前新实验参数，设置一个不同的version_alias！"
        elif version_new in version_list:
            # 若版本号已存在，要求新旧版本号别名必须一致，让用户用以前的版本号别名
            version_alias_old = json_df[json_df["hash256"] == version_new].iloc[0]["version_alias"]
            assert version_alias_new == version_alias_old, f"历史已存在相同的参数，对应参数别名为{version_alias_old}, 请设置version_alias为相同值{version_alias_old}！"
        else:
            # 保存一条数据到mongoDB表结构
            config_dict_json = json.dumps(config_dict_v, sort_keys=True, separators=(",", ":"))
            if long_value_d:
                params_jsonstr_extra = json.dumps(long_value_d, sort_keys=True, separators=(",", ":"))
            else:
                params_jsonstr_extra = None

            create_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.db.exp_params_todb(version_alias=version_alias_new, hash256=version_new, exp_type="model_config",
                                    params_jsonstr=config_dict_json, user_id=self.user_id, create_time=create_time,
                                    params_jsonstr_extra=params_jsonstr_extra)

            # 保存参数文件，分为两部分，一部分是value特别长的参数，一部分是剩下的
            save_path = os.path.join(self.exp_base_path, version_alias_new)
            self.__make_dirs(save_path)
            # 全参数json文件
            with open(os.path.join(save_path, "params_jsonstr.json"), "w") as fp:
                json.dump(config_dict, fp)
            # 未参与参数版本号计算的key的参数json文件
            if params_jsonstr_extra:
                with open(os.path.join(save_path, "params_jsonstr_extra.json"), "w") as fp:
                    json.dump(params_jsonstr_extra, fp)


    def model_file_save(self, model_obj, mode, overwrite=False):
        """
        :param model_config: 模型参数，根据hash256生成版本号
        :param model_obj:
        :param mode:
        :param overwrite:
        :return:
        """
        assert self.exp_version_path, "要存储数据必须先调用activate_version_to_save方法，指定实验版本号！"
        model_save_path = self.model_save_path
        self.__make_dirs(model_save_path)
        print("model_save_path:", model_save_path)

        # 如果存储目录不为空，根据overwirte参数控制是否覆盖
        if is_folder_empty(model_save_path):
            model_save_and_evaluate.save_model_and_factor_list(model_obj, mode, model_save_path)
        else:
            if overwrite:
                # 如，将原本的self.exp_path备份为self.exp_path_20231023093030，再创建一个新的self.exp_path
                date = time.strftime("%Y%m%d%H%M%S")
                backup_path = self.exp_version_path + "_" + date
                os.system("mv {} {}".format(self.exp_version_path, self.exp_version_path + "_" + date))
                self.__make_dirs(model_save_path)
                model_save_and_evaluate.save_model_and_factor_list(model_obj, mode, model_save_path)
                print(f"模型文件已按版本号重新保存，原版本号文件备份至{backup_path}")
            else:
                # raise Exception("模型文件已存储过，overwrite为False，无法覆盖存储！")
                print("模型文件已存储过，overwrite为False，无法覆盖存储！")
        return True

    def model_file_load(self, version_alias, mode = "pickle"):
        model_save_path = os.path.join(self.exp_base_path, version_alias, "saved_models")
        model_obj = model_save_and_evaluate.load_model(mode, model_save_path)
        return model_obj


    def model_signal_save(self, label_name, symbol, tm_values, yhat_values, y_values,
                          target_values, period=120, target_type="mid"):
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
        # TODO 增量存储模式
        assert self.exp_version_path, "要存储数据必须先调用activate_version_to_save方法，指定实验版本号！"
        signal_save_path = self.signal_save_path
        self.__make_dirs(signal_save_path)
        sig_df = model_save_and_evaluate.generate_signal_without_class(t_values=tm_values, yhat_values=yhat_values,
                                               y_values=y_values,
                                               target_values=target_values, period=period, target_type=target_type)
        sig_df.to_parquet(os.path.join(signal_save_path, f"{label_name}-{symbol}.parquet"))
        return sig_df


    def model_signal_load(self, version_alias, label_name, symbol):
        """
        加载信号数据
        :param version_alias:
        :param label_name:
        :param symbol:
        :return:
        """
        signal_save_path = os.path.join(self.exp_base_path, version_alias, "signal_files")
        sig_df = pd.read_parquet(os.path.join(signal_save_path, f"{label_name}-{symbol}.parquet"))
        return sig_df


    def model_signal_process_single_label_th_classify(self, label_name, symbol, label_th1, probs_up, probs_dw, label_th2 = 2):
        assert self.exp_version_path, "要存储数据必须先调用activate_version_to_save方法，指定实验版本号！"
        signal_df = self.model_signal_load(self.version_alias, label_name, symbol)
        signal_df = signal_df.head(1000)

        t1 = time.time()
        print("########### label_th1:{}  probs_up:{}  probs_dw:{} ###############".format(label_th1, probs_up,probs_dw))
        table1_json, table2_json, sig_df = model_save_and_evaluate.generate_probs_single_label_th_classify(signal_df, label_th1, label_th2, probs_up, probs_dw, amp = 6)
        print("五分类转换耗时：", time.time() - t1)

        signal_txt_save_path = os.path.join(self.exp_version_path, f"signal_files_process/{label_name}-{symbol}")
        self.__make_dirs(signal_txt_save_path)
        with open(os.path.join(signal_txt_save_path, f"th{'%.1f'%label_th1}_table1.json"), "w") as f:
            json.dump(table1_json, f, indent=4)

        with open(os.path.join(signal_txt_save_path, f"th{'%.1f'%label_th2}_table2.json"), "w") as f:
            json.dump(table2_json, f, indent=4)

        sig_path = os.path.join(signal_txt_save_path, f"label_th{'%.1f'%label_th1}-probs_up{'%.2f'%probs_up}-probs_dw{'%.2f'%probs_dw}/")
        self.__make_dirs(sig_path)
        t1 = time.time()
        online_model.pk2txt(sig_df, sig_path, symbol)
        print("五分类存储txt耗时：", time.time() - t1)

        # datapath = os.path.join(config["path_config"]["signal_saved_path"], "th{}_probs{}/test/".format(th1, probs))
        # stats_df, pnl_stats_df = evaluate_singal_plot_eval_stats(datapath, 32)
        # plot_results(stats_df, pnl_stats_df)
        # plt.savefig(os.path.join(config["path_config"]["plot_saved_path"], 'local_th{}_probs{}.png'.format(th1, probs)),
        #             dpi=300)
        return True


    def model_signal_evalatioin_single_label_th_classify(self, label_name, symbol,
                                                         label_th=1.1, pred_th_abs_limits=[1, 6.0], start_date = None, end_date = None):
        """
        :param signal_df: 信号标签和预测值的DataFrame，sig_df必须满足标准格式（给出标准格式说明）。
        :param label_name:
        :param label_th:
        :param pred_th_abs_limits:
        :return:
        """
        assert self.exp_version_path, "要存储数据必须先调用activate_version_to_save方法，指定实验版本号！"
        signal_df = self.model_signal_load(self.version_alias, label_name, symbol)
        Y_test, Y_test_pred, T_test = signal_df["LABEL_VALUE"].values, signal_df[
            "PREDICTED"].values, signal_df.index.values
        if not start_date and not end_date:
            start_date, end_date = str(T_test[0])[:10].replace("-", ""), str(T_test[1])[:10].replace("-", "")
        df_th1, df_th2 = model_save_and_evaluate.evaluate_signal_auc_table_by_day(Y_test, Y_test_pred, T_test, label_th=label_th,
                                                           start_date=start_date,
                                                           end_date=end_date, reg_eval_abs_limits=pred_th_abs_limits)

        # self.db.signal_evaluation_data_todb(evaluation_type = "single_label_th_classify", condition = {
        #     label_name:"label_name", "label_th":label_th}, metrics = df_th1)
        return df_th1, df_th2


    def backtest_evaluate_plot_signal_only(self, signal_df_day, plot_save_dir = "./"):
        """
        :param signal_df_day: 单天的dataframe
        :return:
        """
        fig_signal1 = backtest_save_and_evaluate.plot_signal_fig_only(signal_df_day)
        date = signal_df_day["PERIOD_BEGIN"].iloc[0][:11]
        with open(os.path.join(plot_save_dir, "plot_{}.html".format(date)), "w") as f:
            f.write(fig_signal1.to_html(full_html=False))


    def backtest_evaluate_plot_signal_trade(self, signal_df_day, trade_records_df_day, ma_df_day, plot_save_dir = "./"):
        date = signal_df_day["PERIOD_BEGIN"].iloc[0][:11]
        fig_signal1, fig_signal2 = backtest_save_and_evaluate.plot_signal_trade_fig(signal_df_day, trade_records_df_day, ma_df_day, plot=False)

        with open("/home/appadmin/plot_{}.html".format(date), "w") as f:
            f.write(fig_signal1.to_html(full_html=False))


    def backtest_trade_file_save(self, strategy_name, strategy_config_alias, symbol, signal_process_path, trade_df):
        assert self.exp_version_path, "要存储数据必须先调用activate_version_to_save方法，指定实验版本号！"
        trade_save_path = signal_process_path.replace("signal_files_processed", f"backtest/{strategy_name}/{strategy_config_alias}")
        self.__make_dirs(trade_save_path)
        trade_df.to_parquet(os.path.join(trade_save_path, f"{symbol}_trade_records.parquet"))


    def backtest_trade_evaluate(self):
        pass