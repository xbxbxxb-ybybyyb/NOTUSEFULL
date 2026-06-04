from xquant.model.tracking import start_run, log_metrics
import xgboost as xgb
from sklearn import datasets
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split

iris = datasets.load_iris()
X = iris.data
y = iris.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

with start_run(tag='a') as f:
    params = {
    "objective": "multi:softprob",
    "num_class": 3,
    "learning_rate": 0.5,
    "eval_metric": "mlogloss",
    "colsample_bytree": 1.0,
    "subsample": 1.0,
    "seed": 45,
    }
    model = xgb.train(params, dtrain, evals=[(dtrain, "train")])
    # evaluate model
    y_proba = model.predict(dtest)
    y_pred = y_proba.argmax(axis=1)
    loss = log_loss(y_test, y_proba)
    acc = accuracy_score(y_test, y_pred)
    log_metrics({"log_loss": loss, "accuracy": acc, "OPTIMAL_ALPHA": 2, "MSE": 2, "mae": 2})

with start_run(tag='b') as f:
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
    log_metrics({"log_loss": loss, "accuracy": acc, "OPTIMAL_ALPHA": 3, "MSE": 3, "mae": 3})

# 父任务metrics
log_metrics({"log_loss": loss, "accuracy": acc, "OPTIMAL_ALPHA": 1, "MSE": 1, "mae": 1})