
import ray
import os
os.environ["use_cmo"] = "True"
from xquant.factordata import FactorData
s = FactorData()
result13 = s.hset('INDEX', '20110412', 'AMAC.H11030')
print(result13)
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
        "learning_rate": 0.1,
        "eval_metric": "mlogloss",
        "colsample_bytree": 1.0,
        "subsample": 1.0,
        "seed": 40,
    }
model = xgb.train(params, dtrain, evals=[(dtrain, "train")])
# evaluate model
y_proba = model.predict(dtest)
y_pred = y_proba.argmax(axis=1)
loss = log_loss(y_test, y_proba)
acc = accuracy_score(y_test, y_pred)
log_metrics({"log_loss": loss, "accuracy": acc, "OPTIMAL_ALPHA": 1, "MSE": 1, "mae": 1})
log_metrics({"test1": 1, "test2": 2})
