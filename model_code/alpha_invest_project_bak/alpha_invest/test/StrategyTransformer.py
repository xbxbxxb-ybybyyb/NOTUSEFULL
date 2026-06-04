import sys
import pandas as pd
from alpha_invest.datasets.dataset import DataSetManager
from alpha_invest.models.modelbase import ModelMananger
from alpha_invest.models.pytorch_transformer import TransformerModel
from alpha_invest.datasets.data_process.normalization import Normalization2
from alpha_invest.datasets.data_utils import get_n_days_off
import pickle
import yaml
import os
# os.environ["use_cmo"] = 'True'
from tqdm import tqdm
from xquant.model.tracking import parse_params, log_params, log_metrics
from alpha_invest.utils.trace import log_yaml_params
from alpha_invest import alpha_logger


class StrategyBase:
    def __init__(self, **kwargs):
        self.project_config = parse_params("alpha_invest/test/model_config_transformer.yaml")
        self.model_config = self.project_config['model']
        self.dataset_config = self.project_config['dataset']
        self.date_range = self.project_config['date_range']
        self.task_config = self.project_config['task_params']

        #上传工程配置参数
        log_yaml_params("alpha_invest/test/model_config_transformer.yaml")


    def run(self):
        # STEP0: 设置运行参数
        start_date = str(self.date_range['start_date'])
        end_date = str(self.date_range['end_date'])

        factor_list = self.dataset_config['factor_name']
        label_name = self.dataset_config['label_name']
        universe = self.dataset_config["data_params"]['universe']
        label_period = self.dataset_config["data_params"]['label_period']
        assert type(factor_list) == list and type(label_name)==list, "dataset.factor_name和dasetset.label_name应为list格式！"
        label_type = label_name[0]
        label_name = f"{label_type}_{label_period}d"

        if not self.task_config["data_cache"]:
            # STEP1: 加载原始因子数据
            start_date = get_n_days_off(start_date, -label_period - 2)[0]
            self.dataset = DataSetManager(start_date=start_date, end_date=end_date,
                                          universe=universe, label_period=label_period,
                                          factor_path = self.dataset_config['factor_path'], label_path = self.dataset_config["label_path"])
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
            original_datay = original_datay.to_frame(name="vwap_excess_300")
            original_datax = original_datax.fillna(0.0)
            original_datay = original_datay.fillna(0.0)

            # STEP2: 数据预处理&特征工程
            # outlier_filter = self.dataset_config["data_params"]['outlier_filter']
            # z_score_standardizer = self.dataset_config["data_params"]['z_score_standardizer']
            # neutralize = self.dataset_config["data_params"]['neutralize']
            # fill = self.dataset_config["data_params"]['fill']
            factor_union_dict = {}
            for factor in tqdm(original_datax.columns):
                factor_df = Normalization2(original_datax[factor].unstack())
                factor_df = factor_df.norm_dataframe()
                factor_union_dict[factor] = factor_df.stack()
            original_datax = pd.DataFrame(factor_union_dict)


            pickle.dump(original_datax, open("./original_datax.pkl", "wb"))
            pickle.dump(original_datay, open("./original_datay.pkl", "wb"))
        else:
            alpha_logger.warning("use cache data...")
            original_datax = pd.read_pickle("./original_datax.pkl")
            original_datay = pd.read_pickle("./original_datay.pkl")

        

        # STEP3: 初始化模型，并整理、分割数据集
        model_params = self.model_config["model_params"]
        #根据实际情况，修改因子数
        original_datax = original_datax.iloc[:, :]
        model_params["d_feat"] = len(original_datax.columns)
        # model_parmas = self.model_config["model_params"]
        self.model_mgr = TransformerModel(original_datax = original_datax, original_datay = original_datay, model_name="TransformerModel", **model_params)
        self.tds_ds_train = self.model_mgr.transforme_torch_dataset()

        if self.task_config["train_mode"]:
            #STEP4：训练模型&存储模型
            # auto_log(task_type=self.model_config["name"])
            self.model_mgr.train(self.tds_ds_train, save_path = "./best_param.pth")
            model_save_path = os.path.join(self.model_config["model_save_path"], "transformer.pkl")
            pickle.dump(self.model_mgr, open(model_save_path, "wb"))


        #STEP5: 模型预测
        from alpha_invest.models.metrics.linear import mean_squared_error
        preds = self.model_mgr.predict(self.tds_ds_train, save_path = "./best_param.pth")
        mse = mean_squared_error(preds, original_datay.values)
        alpha_logger.info(f"预测值为{preds}, 实际值为{original_datay.values}， mse为{mse}.")
        log_metrics({"mse":mse})


if __name__=="__main__":
    strategy = StrategyBase()
    strategy.run()
