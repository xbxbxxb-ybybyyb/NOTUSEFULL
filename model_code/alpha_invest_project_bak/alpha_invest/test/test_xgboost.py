import os
os.environ['ENV_VERSION'] = 'uat'
import sys

sys.path.append("../huatai_sdk/sjyy-1.1.0")

import xgboost as xgb
from xquant.model.tracking import auto_log, log_metrics
from sklearn import datasets
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split

iris = datasets.load_iris()
X = iris.data
y = iris.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)
# train model
params = {
    "objective": "multi:softprob",
    "num_class": 3,
    "learning_rate": 0.3,
    "eval_metric": "mlogloss",
    "colsample_bytree": 1.0,
    "subsample": 1.0,
    "seed": 42,
}
# Auto Log Xgboost's Params And Metrics
auto_log(task_type="xgboost")
model = xgb.train(params, dtrain, evals=[(dtrain, "train")])
# evaluate model
y_proba = model.predict(dtest)
y_pred = y_proba.argmax(axis=1)
loss = log_loss(y_test, y_proba)
acc = accuracy_score(y_test, y_pred)

# log metrics
log_metrics({"log_loss": loss, "accuracy": acc})
