import sys
import pandas as pd
import numpy as np
import torch
import pickle
import yaml
import os
from tqdm import tqdm

from alpha_invest.datasets.dataset import DataSetManager
from alpha_invest.models.pytorch_transformer import TransformerModel
from alpha_invest.datasets.data_process.normalization import Normalization2
from alpha_invest.datasets.data_utils import get_n_days_off
from xquant.model.tracking import parse_params, log_params, log_metrics
from alpha_invest.utils.trace import log_yaml_params
from alpha_invest import alpha_logger
from xquant.model.tracking import parse_params, log_params, log_metrics
from parallel_train.backend import LocalTrainBackend
from parallel_train.trainer import ParallelTrainer, SplitTaskParam, RayParams
from parallel_train.session import world_size, world_rank, local_rank, report

class StrategyTransformer(LocalTrainBackend):
    def __init__(self, **kwargs):
        self.project_config = parse_params("alpha_invest/test/model_config_transformer.yaml")
        self.model_config = self.project_config['model']
        self.dataset_config = self.project_config['dataset']
        self.date_range = self.project_config['date_range']
        self.task_config = self.project_config['task_params']

    def prepare_data(self, data_params):
        start_date = data_params["date_range"][0]
        self.start_date = start_date
        end_date = data_params["date_range"][1]
        #选择部分因子，减少计算量
        factor_list = data_params['factor_name'][:data_params["data_params"]['d_feat']]
        label_name = data_params['label_name']
        universe = data_params["data_params"]['universe']
        label_period = data_params["data_params"]['label_period']
        assert type(factor_list) == list and type(
            label_name) == list, "dataset.factor_name和dasetset.label_name应为list格式！"
        label_type = label_name[0]
        label_name = f"{label_type}_{label_period}d"

        if not data_params["data_cache"]:
            # STEP: 加载原始因子数据
            start_date = get_n_days_off(start_date, -label_period - 2)[0]
            self.dataset = DataSetManager(start_date=start_date, end_date=end_date,
                                          universe=universe, label_period=label_period,
                                          factor_path=self.dataset_config['factor_path'],
                                          label_path=self.dataset_config["label_path"])
            self.stock_list = self.dataset.stock_list
            self.original_day_factor_data_df = self.dataset.get_factor_data(factor_list)
            self.original_label_data_df = self.dataset.get_label_data(label_type=label_type)

            stocks = self.original_label_data_df.columns
            date = self.original_label_data_df.index
            factor_names = self.original_day_factor_data_df.keys()
            original_datax = []
            for fac in self.original_day_factor_data_df:
                temp_factor = self.original_day_factor_data_df[fac].reindex(columns=stocks, index=date).stack(
                    dropna=False)
                temp_factor.columns = [fac]
                original_datax.append(temp_factor)
            original_datax = pd.concat(original_datax, axis=1)
            original_datax.columns = factor_names
            original_datay = self.original_label_data_df.stack(dropna=False)
            original_datay = original_datay.to_frame(name=label_name)
            original_datax = original_datax.fillna(0.0)
            self.original_datay = original_datay.fillna(0.0)

            # STEP: 数据预处理&特征工程
            # outlier_filter = self.dataset_config["data_params"]['outlier_filter']
            # z_score_standardizer = self.dataset_config["data_params"]['z_score_standardizer']
            # neutralize = self.dataset_config["data_params"]['neutralize']
            # fill = self.dataset_config["data_params"]['fill']
            factor_union_dict = {}
            for factor in tqdm(original_datax.columns):
                factor_df = Normalization2(original_datax[factor].unstack())
                factor_df = factor_df.norm_dataframe()
                factor_union_dict[factor] = factor_df.stack()
            self.original_datax = pd.DataFrame(factor_union_dict)

            pickle.dump(self.original_datax, open(os.path.join(data_params["data_params"]["save_root_path"], "./original_datax_{}.pkl".format(self.start_date)), "wb"))
            pickle.dump(self.original_datay, open(os.path.join(data_params["data_params"]["save_root_path"],"./original_datay_{}.pkl".format(self.start_date)), "wb"))
            print("finish prepare data!")
        else:
            alpha_logger.warning("use cache data...")
            self.original_datax = pd.read_pickle(os.path.join(data_params["data_params"]["save_root_path"], "./original_datax_{}.pkl".format(self.start_date)))
            self.original_datay = pd.read_pickle(os.path.join(data_params["data_params"]["save_root_path"], "./original_datay_{}.pkl".format(self.start_date)))


    def train_loop(self, model_params):
        # 根据实际情况，修改因子数
        original_datax = self.original_datax.iloc[:, :model_params["d_feat"]]
        original_datay = self.original_datay
        # model_parmas = self.model_config["model_params"]
        self.model_mgr = TransformerModel(original_datax=original_datax, original_datay=original_datay,
                                          model_name="TransformerModel", **model_params)

        if model_params["train_mode"]:
            #STEP: 初始化模型，整理、分割数据集
            self.tds_ds_train = self.model_mgr.transform_torch_dataset()
            #按时间划分训练验证集
            self.train_dataset, self.test_dataset = self.model_mgr.split_torch_dataset(
                                                        self.tds_ds_train, model_params["train_split_ratio"], random_split = False)

            # STEP：训练模型&存储模型
            # auto_log(task_type=self.model_config["name"])
            self.model_mgr.train(self.train_dataset, self.test_dataset, save_path="./best_param.pth")
            model_save_path = os.path.join(self.model_config["model_save_path"], "transformer_{}.pkl".format(self.start_date))
            pickle.dump(self.model_mgr, open(model_save_path, "wb"))

        # STEP: 模型预测
        from alpha_invest.models.metrics.linear import mean_squared_error
        preds,labels = self.model_mgr.predict(self.test_dataset, save_path="./best_param.pth")

        mse = mean_squared_error(preds, labels)
        result_df = pd.concat([preds, labels], axis = 1).rename(columns = {0:"preds", 1:"labels"})
        print(result_df)
        alpha_logger.info(f"mse: {mse}.")
        log_metrics({"mse": mse})
        return {"mse":mse, "start_date": self.start_date}

if __name__=="__main__":
    # STEP1: 设置运行参数
    project_config = parse_params("alpha_invest/test/model_config_transformer.yaml")
    model_config = project_config['model']
    dataset_config = project_config['dataset']
    date_range = project_config['date_range']
    task_config = project_config['task_params']

    dataset_config["date_range"] = (str(date_range['start_date']), str(date_range['end_date']))
    dataset_config["data_cache"] = task_config["data_cache"]

    model_config["model_params"]["train_mode"] = task_config["train_mode"]
    model_config["model_params"]["d_feat"] = 10
    model_config["model_params"]["n_epochs"] = 1
    dataset_config["data_params"]['d_feat'] = model_config["model_params"]["d_feat"]


    XGboostPack.run_single_instance(data_params={}, model_params=model_params)
