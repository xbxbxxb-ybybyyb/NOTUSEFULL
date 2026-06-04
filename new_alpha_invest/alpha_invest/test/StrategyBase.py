import pandas as pd
from alpha_invest.datasets.dataset import DataSetManager
from alpha_invest.models.xgb import XGB
from alpha_invest.datasets.data_utils import get_n_days_off
import pickle
from xquant.model.tracking import auto_log, parse_params, log_params
from alpha_invest import alpha_logger


class StrategyBase:
    def __init__(self, **kwargs):
        self.project_config = parse_params()
        self.model_config = self.project_config['model']
        self.dataset_config = self.project_config['dataset']
        self.date_range = self.project_config['date_range']
        self.task_config = self.project_config['task_params']

        # 上传参数
        yaml_params = {}
        for outer_key, outer_value in self.project_config.items():
            for inner_key, inner_value in outer_value.items():
                yaml_params[
                    '{}.{}'.format(outer_key, inner_key)] = inner_value
        log_params(yaml_params)

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

            # STEP2: 数据预处理&特征工程
            # outlier_filter = self.para_strategy['outlier_filter']
            # z_score_standardizer = self.para_strategy['z_score_standardizer']
            # neutralize = self.para_strategy['neutralize']
            # fill = self.para_strategy['fill']
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
            pickle.dump(original_datax, open("./original_datax.pkl", "wb"))
            pickle.dump(original_datay, open("./original_datay.pkl", "wb"))
        else:
            alpha_logger.warning("use cache data...")
            original_datax = pd.read_pickle("./original_datax.pkl")
            original_datay = pd.read_pickle("./original_datay.pkl")

        # STEP3: 初始化模型，并整理、分割数据集
        self.model_mgr = XGB(original_datax = original_datax, original_datay = original_datay, model_name="test_model")
        self.datax = self.model_mgr.transform_datax2D()
        self.datay = self.model_mgr.transform_datay()

        #STEP4：训练模型
        auto_log(task_type=self.model_config["name"])
        model_params = self.model_config["model_params"]
        model_params["dataX"] = self.datax
        model_params["dataY"] = self.datay
        self.model_mgr.train(model_params)

        #STEP5: 模型预测
        preds = self.model_mgr.predict(self.datax)
        alpha_logger.info(f"预测值为{preds}")


if __name__=="__main__":
    if True:
        strategy = StrategyBase()
        strategy.run()
        # pickle.dump(strategy, open("./strategy.pkl", "wb"))
    else:
        strategy = pickle.load(open("./strategy.pkl", "rb"))