import os
os.environ["use_cmo"]='True'
import sys

import xgboost as xgb
from xquant.model.tracking import auto_log, log_metrics, log_params, log_artifacts, start_run, log_dataset
from sklearn import datasets
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split

iris = datasets.load_iris()
X = iris.data
y = iris.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

log_dataset('20200807', '20200810')
log_dataset('20200811', '20200815', dataset_type='test')


for i in range(2):
    with start_run() as f:
        params = {
            "objective": "multi:softprob",
            "num_class": 3,
            "learning_rate": 0.3,
            "eval_metric": "mlogloss",
            "colsample_bytree": 1.0,
            "subsample": 1.0,
            "seed": 42,
        }
        model = xgb.train(params, dtrain, evals=[(dtrain, "train")])
        # evaluate model
        y_proba = model.predict(dtest)
        y_pred = y_proba.argmax(axis=1)
        loss = log_loss(y_test, y_proba)
        acc = accuracy_score(y_test, y_pred)
        log_metrics({f"log_loss{i}": loss, f"accuracy{i}": acc, f"OPTIMAL_ALPHA{i}": 3, f"MSE{i}": 3, f"mae{i}": 3})
        log_dataset('20200807', '20200810')
        log_dataset('20200811', '20200815', dataset_type='test')



# 父任务metrics
params = {
        "objective": "multi:softprob",
        "num_class": 3,
        "learning_rate": 0.3,
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
log_metrics({"log_loss0": loss, "accuracy0": acc, "OPTIMAL_ALPHA0": 1, "MSE0": 1, "mae0": 1})
