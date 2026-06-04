import os
import sys
sys.path.append("../../")
os.environ["use_cmo"]='True'
import numpy as np
import xgboost as xgb
import pickle
import pandas as pd
import gc
import time
from parallel_train.trainer.BaseActor import BaseActor
from DataAPI.DataToolkit import get_n_days_off
from ParallelTrain import update_sample
from xquant.model.tracking import log_metrics, auto_log


class XGBWrapActor(BaseActor):

    def __init__(self):
        """
        成员变量：
        rank_id: int, Actor的唯一标识, 从0开始计数（rank_id可作为data_params或者model_params的key，让各个Actor各自识别自己的参数）;
        data_params: Dict[Any, Any]: 指数据加载、存储的参数，RemoteActor的prepare_data成员函数的唯一入参，可指定SplitTaskParam类型的参数用于切分任务；
        model_params: Dict[Any, Any]: 指模型算法的训练参数，RemoteActor的train成员函数的唯一入参；
        ray_params: RayParams, 指并行任务运行的配置参数，可获取RemoteActor的运行参数，如cpus_per_actor， gpus_per_actor， num_actors等，对应提交任务时的最小资源组和资源组个数; 后续支持容错、回调、超参数寻优等其他配置。
        成员方法：
        put_queue(item: Dict[str, [_Checkpoint, Any]): 用于传递结果到主程序drive端。driver端定时（默认30s）获取queue中的结果，并填入train函数的返回值additional_results。key为additional_results中的key名。
        reset_rank_id(rank_id: int)：重置rank_id的方法，rank_id由框架自动分配，一般不需要手动指定，一些调试场景时可以指定rank_id来分配特定的任务。
        """
        self.random_seed = 1990
        # self._train_date_stock = None
        # self._valid_date_stock = None
        self.model_name = self.__class__.__name__
        self._counts = 1


    def prepare_data(self, data_params):
        """
        （待实现的成员方法）用于train或者predict执行前的准备工作(如加载数据，加载模型等)，由并行训练框架内部调用。
        :param data_params: 数据参数，可结合rank_id识别各个actor的数据；
        :return: None，数据请赋值给成员变量后使用。
        """
        #设置训练集数据
        self.train_date = data_params["train_date"]
        self.strategy_type = data_params["strategy_type_factor"][0]
        self.factor_list = data_params["strategy_type_factor"][1]
        self.label_name = data_params["label_name"]
        self.gap = data_params["gap"]
        train_dates = get_n_days_off(self.train_date, - self.gap - data_params["train_window"])
        self.sample_data = update_sample.load_sample(self.factor_list, train_dates, self.strategy_type, self.label_name, data_params["gap"])

        num = int(len(train_dates) / self._counts)
        np.random.seed(self.random_seed)
        np.random.shuffle(train_dates)

        self.train_set = self.sample_data[self.sample_data['date'].isin([pd.to_datetime(str(date)) for date in train_dates])]
        self.train_x = self.train_set[self.factor_list]
        self.train_y = self.train_set[self.label_name]

        train_x_list = []
        train_y_list = []
        for i in range(1):
            train_x_list.append(self.train_x)
            train_y_list.append(self.train_y)
        self.train_x = pd.concat(train_x_list, axis = 0)
        self.train_y = pd.concat(train_y_list, axis = 0)



        self.train_x.to_pickle("/home/appadmin/trainx.pkl")
        self.train_y.to_pickle("/home/appadmin/trainy.pkl")
        # print(self.train_set.shape, self.train_x.shape, self.train_y.shape)

        #设置测试集数据
        self.predict_date_list = [k for k, v in data_params["train_test_map"].items() if v == self.train_date]

        #设置模型输出路径
        self.model_path = os.path.join(data_params["save_root_path"], '{}/Model_File_{}_{}/ModelSaved'.format(self.strategy_type, self.model_name, self.strategy_type))
        self.prediction_path = os.path.join(data_params["save_root_path"], '{}/Model_File_{}_{}/SignalFile'.format(self.strategy_type, self.model_name, self.strategy_type))
        if not os.path.exists(self.model_path):
            try:
                os.makedirs(self.model_path)
            except:
                #避免并行创建文件夹报错
                pass
        if not os.path.exists(self.prediction_path):
            try:
                os.makedirs(self.prediction_path)
            except:
                #避免并行创建文件夹报错
                pass


    def train(self, model_params: dict):
        """
        （待实现的成员方法）模型训练函数，在Actor的准备步骤都完成后，开始执行，由并行训练框架内部调用。
        :param model_params:
        :return: None，训练结果返回值请通过put_queue函数传递到driver端的parallel_train.train的additional_results返回值。
        """
        from xquant.model.tracking import log_metrics, auto_log
        if False:#os.path.exists('{}/{}_{}_{}.pickle'.format(self.model_path, self.model_name, self.strategy_type, self.train_date)):
            log_metrics({"filename1": 1234})
            print("use_cmo:", os.environ["use_cmo"])
            print('model exist:', '{}/{}_{}_{}.pickle'.format(self.model_path, self.model_name, self.strategy_type, self.train_date))
        else:
            #重新指定并行度
            params = model_params["params"]
            if "nthread" in model_params:
                if ("nthread" in params and params["nthread"] > self.ray_params.cpus_per_actor):
                    raise ValueError(
                        f"Specified number of threads {params['nthread']} greater than number of CPUs {self.ray_params.cpus_per_actor}.")
            else:
                params["nthread"] = int(self.ray_params.cpus_per_actor)

            model = {}
            j = 0
            model.update({j: None})
            model[j] = xgb.XGBRegressor(maximize=model_params["maximize"], **params)
            model[j].fit(X=self.train_x, y=self.train_y, verbose=False, eval_set=[(self.train_x, self.train_y)], eval_metric=model_params["eval_metric"])

            filename = '{}/{}_{}_{}.pickle'.format(self.model_path, self.model_name, self.strategy_type, self.train_date)
            with open(filename, 'wb') as f:
                pickle.dump(obj=model, file=f)
            del model
            gc.collect()
            print("train model success! rank_id: {}".format(self.rank_id))
            time.sleep(5)

        #训练完模型之后直接开始预测
        if False:#len(self.predict_date_list) > 0:
            time_start = time.time()
            print('{}_{}_{} predicting begins at {}'.format(self.model_name, self.strategy_type, self.train_date,
                                                            time.asctime(time.localtime(time_start))))
            for today_date in self.predict_date_list:
                sample_data = update_sample.load_sample(self.factor_list, [today_date], self.strategy_type, self.label_name, self.gap)
                self.label_predict(sample_data, self.train_date, today_date)
            time_end = time.time()
            print('{}_{}_{} predicting ends at {} and lasts {} min'.format(self.model_name, self.strategy_type, self.train_date,
                                                                           time.asctime(time.localtime(time_end)),
                                                                           int((time_end - time_start) / 60)))
        return


    def label_predict(self, sample_daily, train_date, today_date):
        res = []
        filename = '{}/{}_{}_{}.pickle'.format(self.model_path, self.model_name, self.strategy_type, train_date)
        with open(filename, 'rb') as f:
            model_dict = pickle.load(file=f)
        for j in range(self._counts):
            model = model_dict[j]

            model.get_booster().set_param({'predictor': 'cpu_predictor'})
            test_x = sample_daily[self.factor_list]
            y_pred = model.predict(test_x)
            label_pred = pd.Series(data=y_pred, index=sample_daily['stock'].values)
            res.append(label_pred)
        res = pd.concat(res, axis=1)
        y_pred = res.mean(axis=1).values

        infer_result = {}
        date_time = list(sample_daily['date'])[0]
        key = int(date_time.strftime("%Y%m%d%H%M%S"))
        infer_result[key] = {}
        intra_result = {'Code': list(sample_daily['stock']), 'predict': y_pred.flatten()}
        infer_result[key].update({'infer_result': intra_result})
        signal_name = '{}/signal_{}.pickle'.format(self.prediction_path, today_date)
        with open(signal_name, 'wb') as f:
            pickle.dump(obj=infer_result, file=f)
        print("label_predict success {}!".format(today_date))


if __name__=="__main__":
    strategy_types = 'vwap'
    fs = pd.read_pickle("/data/user/013150/model_code/test_dist/parallel_train/data/factor_list.pkl")
    data_params = {"train_date": 20200117,
                   "strategy_type_factor": (strategy_types, fs),
                   "train_test_map": {20200117: 20200117},
                   "label_name": 'vwap_re',
                   'gap': 5,
                   'train_window': 240,
                   "save_root_path": "/tmp/user/012620/own/Apollo/StrategySelectStockDay"
                   }
    model_params = {"params": {'n_estimators': 1000, 'seed': 1993, 'nthread': 100, 'gamma': 5.0, 'min_child_weight': 0.5,
                               'reg_alpha': 50, 'reg_lambda': 10, 'max_depth': 8, 'learning_rate': 0.05,
                               'subsample': 0.9,
                               'colsample_bytree': 0.9, 'tree_method': 'gpu_hist'},
                    "maximize": False,
                    "eval_metric": ["mae"]
                    }

    instance = XGBWrapActor()
    instance.reset_rank_id(rank_id=0)
    instance.prepare_data(data_params)
    instance.train(model_params)