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
                                 mock_data_flag=data_params["mock_data_flag"], num_features=data_params["num_features"], tag_name=data_params["tag_name"])
        self.factor_data_train, self.factor_data_test, self.label_data_train, self.label_data_test = dloader.train_test_split(train_split_ratio=0.9)

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
        self.y_train = self.label_data_train.iloc[:, 3].values
        self.X_test = self.factor_data_test.iloc[:, 3:].values
        self.y_test = self.label_data_test.iloc[:, 3].values
        print("prepare_data, X_train:", self.X_train.shape, "y_train:", self.y_train.shape, "X_test:", self.X_test.shape, "y_test:", self.y_test.shape)

    def train_loop(self, model_params):
        import xgboost as xgb

        use_cv = model_params.pop("use_cv")
        early_stopping_rounds = model_params.pop("early_stopping_rounds")
        cv = self.cv
        X_train = self.X_train
        y_train = self.y_train
        X_test = self.X_test
        y_test = self.y_test

        #设置样本权重
        from sklearn.utils import class_weight
        classes_weights = class_weight.compute_sample_weight(
            class_weight='balanced',
            y=y_train
        )

        # setup the pieline
        clf = xgb.XGBClassifier(**model_params)
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
            _ = clf.fit(X, y, sample_weight = classes_weights, eval_metric="mlogloss", eval_set=[(X_test, y_test)], early_stopping_rounds = early_stopping_rounds, verbose = False)#样本赋权
            auc_final, auc_report = self.predict(X_test, y_test)
            auc_final_train, auc_report_train = self.predict(X_train, y_train)
            print('test_auc', auc_report)
            print('train_auc', auc_report_train)
            precition_final = (auc_report['1']['precision'] + auc_report['2']['precision']) / 2

        print("auc:", auc_final, 'accuracy:', precition_final)
        from parallel_train.session import report, world_rank
        #超参数调优需要
        tune.report(auc = auc_final, precition = precition_final)
        # report(auc = auc_final, world_rank = world_rank())
        return {"auc": auc_final, "precition": precition_final, "world_rank":world_rank(), "time":time.time()-t1, "feature_imp": clf.feature_importances_}

    def predict(self, X, y):
        from sklearn.metrics import roc_auc_score, classification_report
        preds_proba = self.clf.predict_proba(X)
        preds = np.argmax(preds_proba, axis=1)
        auc_final = roc_auc_score(y, preds_proba, multi_class='ovo')
        auc_report = pd.DataFrame(classification_report(y, preds, output_dict=True))
        return auc_final, auc_report


if __name__=="__main__":
    data_params = {"factor_path":"/data/user/quanttest007/alpha_invest/merge_data_688599.parquet",
                    "num_features":200,
                   "tag_name": "Tag5minRet",
                   "mock_data_flag":False,
                   'max_train_group_size':450, #训练集包含的天数
                   }
    model_params = {
        'n_estimators': 100,
        'max_depth': 5,
        'learning_rate': 0.0172697,
        'subsample': 0.6424,
        "colsample_bytree": 0.879219,
        'gamma': 10,
        'tree_method': 'hist',#'gpu_hist',
        'objective': 'multi:softprob',
        'num_class': 3,
        "use_cv":False,
        "n_jobs": 4,
        'early_stopping_rounds':50
    }
    XGboostPack.run_single_instance(data_params=data_params, model_params= model_params)
