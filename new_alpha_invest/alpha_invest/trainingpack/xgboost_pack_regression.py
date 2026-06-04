from parallel_train.backend import LocalTrainBackend
from alpha_invest.datasets.dataset_loader import DatasetLoader
from alpha_invest.datasets.dataset_manager import DataSetManager, PurgedGroupTimeSeriesSplit
import numpy as np
from ray import tune
import time
import pandas as pd
pd.set_option('display.max_columns', 10)

class XGboostPack(LocalTrainBackend):
    def __init__(self):
        pass

    def prepare_data(self, data_params):
        dloader = DatasetLoader()
        dloader.load_factor_data(factor_path = data_params["factor_path"],
                                 mock_data_flag=data_params["mock_data_flag"], classify_or_not = False,
                                 num_features=data_params["num_features"], tag_name=data_params["tag_name"])
        #TODO: 验证集天数的确认
        self.factor_data_train, self.factor_data_test, self.label_data_train, self.label_data_test = dloader.train_test_split(
            train_test_split_date = "20220601")
        self.factor_data_train, self.factor_data_valid, self.label_data_train, self.label_data_valid = dloader.train_test_split(
            train_test_split_date="20220401", factor_data = self.factor_data_train, label_data=self.label_data_train)

        n_groups = len(set(self.factor_data_train['mddate']))
        n_samples = len(self.factor_data_train)

        self.groups = self.factor_data_train['mddate'].astype(int).rank(method='dense').values

        self.cv = PurgedGroupTimeSeriesSplit(
            n_splits=3,
            max_train_group_size=data_params['max_train_group_size'],
            group_gap=0,
            max_test_group_size=20
        )
        self.X_train = self.factor_data_train.iloc[:, 3:].values
        self.y_train = self.label_data_train.iloc[:, 3].values*100
        self.X_test = self.factor_data_test.iloc[:, 3:].values
        self.y_test = self.label_data_test.iloc[:, 3].values*100
        self.X_valid = self.factor_data_valid.iloc[:, 3:].values
        self.y_valid = self.label_data_valid.iloc[:, 3].values * 100
        print("prepare_data, X_train:", self.X_train.shape, "y_train:", self.y_train.shape,  "X_valid:", self.X_valid.shape, "y_valid:", self.y_valid.shape, "X_test:", self.X_test.shape, "y_test:", self.y_test.shape)

    def train_loop(self, model_params):
        import xgboost as xgb

        use_cv = model_params.pop("use_cv")
        early_stopping_rounds = model_params.pop("early_stopping_rounds")
        cv = self.cv
        X_train = self.X_train
        y_train = self.y_train
        X_test = self.X_test
        y_test = self.y_test
        X_valid = self.X_valid
        y_valid = self.y_valid

        from sklearn.utils import class_weight
        f1 = np.frompyfunc(lambda x: self.classic(x), 1, 1)  # y_class = np.apply_along_axis(classic, 0, y)
        y_train_class = f1(y_train).astype('int64')
        sample_weights = class_weight.compute_sample_weight(
            class_weight='balanced',
            y=y_train_class
        )

        # setup the pieline
        clf = xgb.XGBRegressor(**model_params)
        self.clf = clf

        t1 = time.time()
        if use_cv:
            # fit for all folds and return composite AUC score
            aucs = []
            precitions = []
            for i, (train_idx, valid_idx) in enumerate(cv.split(
                    X_train,
                    y_train,
                    groups=self.groups)):
                X = X_train[train_idx[:], :]
                # np.random.shuffle(X)#打乱数据
                y = y_train[train_idx[:]]
                print(i, "X shape:", X.shape, "y shape:", y.shape)
                _ = clf.fit(X, y)#, sample_weight = classes_weights)#样本赋权
                auc, auc_report = self.predict(X_test, y_test)
                print(auc_report)
                aucs.append(auc)
                precitions.append((auc_report['1']['precision']+auc_report['2']['precision'])/2)#涨和跌类的准确率
            print(f'Trial done: AUC values on folds: {aucs}')
            auc_final = np.average(aucs)
            precition_final = np.average(precitions)
        else:
            X = X_train
            # np.random.shuffle(X)#打乱数据
            y = y_train
            print("X shape:", X.shape, "y shape:", y.shape)
            _ = clf.fit(X, y,  sample_weight = sample_weights, eval_metric="rmse", eval_set=[(X_valid, y_valid)], early_stopping_rounds = early_stopping_rounds, verbose = True)#样本赋权
            auc_final, auc_report = self.predict(X_test, y_test)
            auc_final_valid, auc_report_valid = self.predict(X_valid, y_valid)
            auc_final_train, auc_report_train = self.predict(X_train, y_train)
            print('test_auc', auc_report)
            print('valid_auc', auc_report_valid)
            print('train_auc', auc_report_train)
            precition_final = (auc_report['1']['precision'] + auc_report['2']['precision']) / 2

        print("auc:", auc_final, 'accuracy:', precition_final)
        from parallel_train.session import report, world_rank
        #超参数调优需要
        tune.report(auc = auc_final, precition = precition_final)
        # report(auc = auc_final, world_rank = world_rank())
        return {"auc": auc_final, "precition": precition_final, "world_rank":world_rank(), "time":time.time()-t1, "feature_imp": clf.feature_importances_}

    def classic(self, label, is_tag_percent = False):
        th = 0.0012 * 1000
        if is_tag_percent:
            th = th * 100
        if -th < label < th:
            return 0
        elif label >= th:
            return 1
        else:
            return 2

    def predict(self, X, y):
        from sklearn.metrics import roc_auc_score, classification_report
        preds = self.clf.predict(X)
        f1 = np.frompyfunc(lambda x: self.classic(x), 1, 1) # y_class = np.apply_along_axis(classic, 0, y)
        y_class = f1(y).astype('int64')
        preds_class = f1(preds).astype('int64')
        auc_report = pd.DataFrame(classification_report(y_class, preds_class, output_dict=True))
        return auc_report.loc['f1-score', 'accuracy'], auc_report


if __name__=="__main__":
    data_params = {"factor_path":"/data/user/quanttest007/alpha_invest/merge_data_688599_200.parquet",
                    "num_features":100,
                   "tag_name": "tag5minLong",
                   "mock_data_flag":False,
                   'max_train_group_size':450, #训练集包含的天数
                   "train_test_split_date":"20220401"
                   }
    model_params = {
        'n_estimators': 666,
        'max_depth': 7,
        'learning_rate': 0.0116894,
        'subsample': 0.584566,
        "colsample_bytree": 0.713497,
        'tree_method': 'hist',#'gpu_hist',
        'objective':'reg:squarederror',
        "use_cv":False,
        "n_jobs": 10,
        'early_stopping_rounds':50,
        'random_state':123
    }

    XGboostPack.run_single_instance(data_params=data_params, model_params= model_params)
