import pandas as pd
import numpy as np
from alpha_invest.datasets.dataset import DataSetManager
from alpha_invest.models.modelbase import ModelMananger
from alpha_invest.models.lr import LR
from alpha_invest.datasets.data_utils import get_n_days_off
import pickle


class StrategyBase:
    def __init__(self, **kwargs):
        model_management = "research"
        start_date, end_date = ['20180119', '20190110']#训练日期，而非数据日期
        universe = "ALLA"
        factor_list = ["open", "close", "high", "low"]
        tag = 'vwap_excess_300'

        outlier_filter = False
        z_score_standardizer = False
        neutralize = False
        fill = False
        # update_model_period = 10  # 训练模型的周期，单位是多少个持仓周期(待补充模型周期更新的逻辑)
        # train_lag = 90#训练样本的个数，如90
        test_pred_period = 5 #标签的计算周期，如5，表示拿5天后的值计算标签。

        self.para_strategy = {'universe': universe,
                        'start_date': start_date,
                        'end_date': end_date,
                        'factor_list': factor_list,
                        'test_tag': tag,
                        'test_pred_period': test_pred_period,
                        'outlier_filter': outlier_filter,
                        'z_score_standardizer': z_score_standardizer,
                        'neutralize': neutralize,
                        'fill': fill,
                        }

    def run(self):
        # STEP0: 设置运行参数
        universe = self.para_strategy['universe']
        start_date = self.para_strategy['start_date']
        end_date = self.para_strategy['end_date']
        factor_list = self.para_strategy['factor_list']
        tag = self.para_strategy['test_tag']
        test_pred_period = self.para_strategy['test_pred_period']
        outlier_filter = self.para_strategy['outlier_filter']
        z_score_standardizer = self.para_strategy['z_score_standardizer']
        neutralize = self.para_strategy['neutralize']
        fill = self.para_strategy['fill']

        # STEP1: 加载原始因子数据
        start_date = get_n_days_off(start_date, -test_pred_period - 2)[0]
        self.dataset = DataSetManager(start_date=start_date, end_date=end_date, universe=universe,
                                      test_pred_period=test_pred_period)
        self.stock_list = self.dataset.stock_list
        self.original_day_factor_data_df = self.dataset.get_factor_data(factor_list)
        self.original_label_data_df = self.dataset.get_label_data(label_type=tag)

        # STEP2: 数据预处理&特征工程

        # STEP3: 初始化模型，并整理、分割数据集
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

        self.model_mgr = LR(original_datax = original_datax, original_datay = original_datay, model_name="test_model")
        self.datax = self.model_mgr.transform_datax2D()
        self.datay = self.model_mgr.transform_datay()

        #STEP4：训练模型
        self.model_mgr.train(self.datax, self.datay)

        #STEP5: 模型预测
        preds = self.model_mgr.infer(self.datax)
        print(preds)


if __name__=="__main__":
    if True:
        strategy = StrategyBase()
        strategy.run()
        # pickle.dump(strategy, open("./strategy.pkl", "wb"))
    else:
        strategy = pickle.load(open("./strategy.pkl", "rb"))