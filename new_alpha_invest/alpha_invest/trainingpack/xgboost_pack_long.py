from parallel_train.backend import LocalTrainBackend
from alpha_invest.datasets.dataset_loader import DatasetLoader
from alpha_invest.datasets.dataset_manager import DataSetManager, PurgedGroupTimeSeriesSplit
import numpy as np
from ray import tune
import time
import pandas as pd

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
        #TODO：
        self.label_data_train.iloc[:, 3] = self.label_data_train.iloc[:, 3].apply(lambda x: 0 if x==2 else x)#把0分类变为不涨分类
        self.label_data_test.iloc[:, 3] = self.label_data_test.iloc[:, 3].apply(lambda x: 0 if x == 2 else x)  # 把0分类变为不涨分类
        train_negative_num = self.label_data_train[self.label_data_train.iloc[:,3]==0].count().iloc[0]
        train_positive_num = self.label_data_train[self.label_data_train.iloc[:,3]==1].count().iloc[0]
        self.scale_pos_weight = round(train_negative_num / train_positive_num, 2)*1.05

        self.X_train = self.factor_data_train.iloc[:, 3:].values
        self.y_train = self.label_data_train.iloc[:, 3].values
        self.X_test = self.factor_data_test.iloc[:, 3:].values
        self.y_test = self.label_data_test.iloc[:, 3].values
        print("prepare_data, X_train:", self.X_train.shape, "y_train:", self.y_train.shape, "X_test:", self.X_test.shape, "y_test:", self.y_test.shape)

    def train_loop(self, model_params):
        import xgboost as xgb
        from sklearn.metrics import roc_auc_score, classification_report

        use_cv = model_params.pop("use_cv")
        early_stopping_rounds = model_params.pop("early_stopping_rounds")
        cv = self.cv
        X_train = self.X_train
        y_train = self.y_train
        X_test = self.X_test
        y_test = self.y_test

        # setup the pieline
        clf = xgb.XGBClassifier(**model_params, scale_pos_weight = self.scale_pos_weight)

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
                _ = clf.fit(X, y)
                preds_proba = clf.predict_proba(X_train[valid_idx])
                preds = np.argmax(preds_proba, axis=1)
                auc = roc_auc_score(y_train[valid_idx], preds_proba)#, multi_class='ovo')
                auc_report = pd.DataFrame(classification_report(y_train[valid_idx], preds, output_dict = True))
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
            _ = clf.fit(X, y, eval_metric="logloss", eval_set=[(X_test, y_test)], early_stopping_rounds = early_stopping_rounds, verbose = True)#样本赋权
            preds_proba = clf.predict_proba(X_test)
            #BUG: 已修复，原始类别为1和2，这边却把类别转成了0和1
            preds = np.argmax(preds_proba, axis=1)
            auc_final = roc_auc_score(y_test, preds)#, multi_class='ovo')
            auc_report = pd.DataFrame(classification_report(y_test, preds, output_dict = True))
            print(auc_report.loc[:, ["0", "1"]])
            precition_final = (auc_report["0"]['precision']+auc_report['1']['precision'])/2

        print("auc:", auc_final, 'accuracy:', precition_final)

        from parallel_train.session import report, world_rank
        #超参数调优需要
        tune.report(auc = auc_final, precition = precition_final)
        # report(auc = auc_final, world_rank = world_rank())
        return {"auc": auc_final, "precition": precition_final, "world_rank":world_rank(), "time":time.time()-t1, "feature_imp": clf.feature_importances_}


if __name__=="__main__":
    data_params = {"factor_path":"/data/user/quanttest007/alpha_invest/merge_data_688599.parquet",
                    "num_features":200,
                   "tag_name": "Tag5minRet",
                   "mock_data_flag":False,
                   'max_train_group_size':450, #训练集包含的天数
                   }
    model_params = {
        'n_estimators': 1,
        'max_depth': 5,
        'learning_rate': 0.0172697,
        'subsample': 0.6424,
        "colsample_bytree": 0.879219,
        'gamma': 10,
        'tree_method': 'hist',#'gpu_hist',
        'objective': 'binary:logistic',#'multi:softprob',
        "use_cv":False,
        "n_jobs":10,
        "early_stopping_rounds": 50
    }
    XGboostPack.run_single_instance(data_params=data_params, model_params= model_params)
