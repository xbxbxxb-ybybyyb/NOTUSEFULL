import os
os.environ["use_cmo"] = "True"
import xgboost as xgb
from xquant.model import log_metrics, log_params, parse_params, start_run
from sklearn import datasets
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split

iris = datasets.load_iris()
X = iris.data
y = iris.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

class A():

    def train(self):
        # 上传参数
        yaml_params = {}
        params_dict = parse_params()
        for outer_key, outer_value in params_dict.items():
            if type(outer_value) != dict:
                yaml_params[outer_key] = outer_value
                continue
            for inner_key, inner_value in outer_value.items():
                yaml_params[
                    '{}_{}'.format(outer_key, inner_key)] = inner_value
        log_params(yaml_params)

        params = {
                "objective": "multi:softprob",
                "num_class": 3,
                "learning_rate": 0.3,
                "eval_metric": "mlogloss",
                "colsample_bytree": 1.0,
                "subsample": 1.0,
                "seed": 40,
            }
        # model = xgb.train(params, dtrain, evals=[(dtrain, "train")])
        model = xgb.XGBRegressor(**params)
        model.fit(X=X_train, y=y_train, verbose=False, eval_set=[(X_test, y_test)], eval_metric='mlogloss')
        # evaluate model
        y_proba = model.predict(X_test)
        print(y_proba)

a = A()

model_params = {"params": {'n_estimators': 100, 'seed': 1993, 'nthread': 40, 'gamma': 5.0, 'min_child_weight': 0.5,
                               'reg_alpha': 50, 'reg_lambda': 10, 'max_depth': 8, 'learning_rate': 0.05,
                               'subsample': 0.9,
                               'colsample_bytree': 0.9, 'tree_method': 'hist'},
                    "maximize": False,
                    "eval_metric": ["mae"]
                    }
import pandas as pd
train_x = pd.read_pickle("/home/appadmin/trainx.pkl")
train_y = pd.read_pickle("/home/appadmin/trainy.pkl")

model = xgb.XGBRegressor(maximize=model_params["maximize"], **model_params["params"])
model.fit(X=train_x, y=train_y, verbose=False, eval_set=[(train_x, train_y)], eval_metric=model_params["eval_metric"])
