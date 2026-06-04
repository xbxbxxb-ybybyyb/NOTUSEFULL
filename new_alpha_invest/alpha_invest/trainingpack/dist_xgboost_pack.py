from parallel_train.backend import XGBoostBackend, get_rabit_centext
from alpha_invest.datasets.dataset_loader import DatasetLoader
from alpha_invest.datasets.dataset_manager import DataSetManager, PurgedGroupTimeSeriesSplit
import numpy as np
from ray import tune
import xgboost as xgb

class DistXGboostPack(XGBoostBackend):
    def __init__(self):
        pass

    def prepare_data(self, data_params):
        dloader = DatasetLoader()
        dloader.load_factor_data()
        self.factor_data_train, self.factor_data_test, self.label_data_train, self.label_data_test = dloader.train_test_split(train_split_ratio=0.9)

        n_groups = len(set(self.factor_data_train['mddate']))
        n_samples = len(self.factor_data_train)

        self.groups = self.factor_data_train['mddate'].astype(int).rank(method='dense').values

        self.cv = PurgedGroupTimeSeriesSplit(
            n_splits=4,
            max_train_group_size=50,
            group_gap=0,
            max_test_group_size=5
        )
        self.X_train = self.factor_data_train.iloc[:, 3:].values
        self.y_train = self.label_data_train.iloc[:, 3].values

        print("prepare_data, X_train:", self.X_train.shape, "y_train:", self.y_train.shape)

    def train_loop(self, model_params):
        import xgboost as xgb
        from sklearn.metrics import roc_auc_score

        cv = self.cv
        X_train = self.X_train
        y_train = self.y_train
        cv_fold_func = np.average

        # fit for all folds and return composite AUC score
        aucs = []
        for i, (train_idx, valid_idx) in enumerate(cv.split(
                X_train,
                y_train,
                groups=self.groups)):
            X = X_train[train_idx[:], :]
            y = y_train[train_idx[:]]
            print("X shape:", X.shape, "y shape:", y.shape)
            #分布式训练
            with get_rabit_centext():
                # evals_result = {}
                # bst = xgb.train(
                #     model_params,
                #     xgb.DMatrix(**{"data": X, "label": y}),
                #     num_boost_round  = 10,
                #     evals=[(xgb.DMatrix(**{"data": X, "label": y}), "eval_data")],
                #     evals_result=evals_result,
                #     **model_params
                # )
                # setup the pieline
                clf = xgb.XGBClassifier(**model_params)
                _ = clf.fit(X, y)
                preds_proba = clf.predict_proba(X_train[valid_idx])
                print("preds_proba:", preds_proba)
            auc = roc_auc_score(y_train[valid_idx], preds_proba, multi_class='ovo')
            aucs.append(auc)

        auc_final = cv_fold_func(aucs)

        from parallel_train.session import report, world_rank
        # tune.report(auc=auc_final)
        # report(auc = auc_final, world_rank = world_rank())
        print(f'Trial done: AUC values on folds: {aucs}')
        return {"auc": auc_final, "world_rank":world_rank()}


if __name__=="__main__":
    model_params = {
        'n_estimators': 350,
        'max_depth': 3,
        'learning_rate': 0.01,
        'subsample': 0.50,
        'colsample_bytree': 0.50,
        'gamma': 2,
        'missing': -999,
        'tree_method': 'hist',
        'objective': 'multi:softprob',
        'num_class': 3
    }
    DistXGboostPack.run_single_instance(data_params={}, model_params= model_params)
