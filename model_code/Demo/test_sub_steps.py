
import xgboost as xgb
from xquant.model import auto_log, log_metrics, log_params, log_artifacts, start_run
from sklearn import datasets
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split

iris = datasets.load_iris()
X = iris.data
y = iris.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

with start_run() as f:
    params = {
    "objective": "multi:softprob",
    "num_class": 3,
    "learning_rate": 0.5,
    "eval_metric": "mlogloss",
    "colsample_bytree": 1.0,
    "subsample": 1.0,
    "seed": 41,
    }
    model = xgb.train(params, dtrain, evals=[(dtrain, "train")])
    # evaluate model
    y_proba = model.predict(dtest)
    y_pred = y_proba.argmax(axis=1)
    loss = log_loss(y_test, y_proba)
    acc = accuracy_score(y_test, y_pred)
    log_params({'alpha': 1, 'beta': 1})
    log_metrics({"log_loss": loss, "accuracy": acc, "OPTIMAL_ALPHA": 2, "MSE": 2, "mae": 2, "IC": 1})
    log_artifacts('model_config.yaml')
    for i in range(20210901, 20210905):
        step = i
        m_dict = {'sub_a': i, 'sub_b': i*10}
        log_metrics(m_dict, step=step)

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
    log_params({'alpha': 2, 'beta': 2})
    log_metrics({"log_loss": loss, "accuracy": acc, "OPTIMAL_ALPHA": 3, "MSE": 3, "mae": 3, "IC": 2})
    log_artifacts('model_config.yaml')
    for i in range(20210905, 20210909):
        step = i
        m_dict = {'sub_a': i, 'sub_b': i*10}
        log_metrics(m_dict, step=step)

with start_run() as f:
    params = {
        "objective": "multi:softprob",
        "num_class": 3,
        "learning_rate": 0.3,
        "eval_metric": "mlogloss",
        "colsample_bytree": 1.0,
        "subsample": 1.0,
        "seed": 43,
    }
    model = xgb.train(params, dtrain, evals=[(dtrain, "train")])
    # evaluate model
    y_proba = model.predict(dtest)
    y_pred = y_proba.argmax(axis=1)
    loss = log_loss(y_test, y_proba)
    acc = accuracy_score(y_test, y_pred)
    log_params({'alpha': 3, 'beta': 3})
    log_metrics({"log_loss": loss, "accuracy": acc, "OPTIMAL_ALPHA": 3, "MSE": 3, "mae": 3, "IC": 3})
    log_artifacts('model_config.yaml')
    for i in range(20210909, 20210913):
        step = i
        m_dict = {'sub_a': i, 'sub_b': i * 10}
        log_metrics(m_dict, step=step)

# 父任务metrics

log_params({'alpha': 0, 'beta': 0, 'seed': 40, 'num_boost_round': 10})
log_metrics({"log_loss": loss, "accuracy": acc, "MSE": 1, "mae": 1, 'IC': 0})
log_artifacts('test_sub_steps.py')
for i in range(1, 5):
    step = i
    m_dict = {'a': i, 'b': i*10, 'OPTIMAL_ALPHA': i*100}
    log_metrics(m_dict, step=step)