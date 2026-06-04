import xgboost as xgb
from xquant.model.tracking import log_metrics, log_params, start_run, parse_params, log_dataset
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
# yaml_params = {}
# params_dict = parse_params()
# for outer_key, outer_value in params_dict.items():
#     if type(outer_value) != dict:
#         yaml_params[outer_key] = outer_value
#         continue
#     for inner_key, inner_value in outer_value.items():
#         yaml_params[
#             '{}_{}'.format(outer_key, inner_key)] = inner_value
# log_params(yaml_params)

# 子任务1
with start_run() as f:
    # params = {
    # "objective": "multi:softprob",
    # "num_class": 3,
    # "learning_rate": 0.5,
    # "eval_metric": "mlogloss",
    # "colsample_bytree": 1.0,
    # "subsample": 1.0,
    # "seed": 45,
    # }
    # model = xgb.train(params, dtrain, evals=[(dtrain, "train")])
    # # evaluate model
    # y_proba = model.predict(dtest)
    # y_pred = y_proba.argmax(axis=1)
    # loss = log_loss(y_test, y_proba)
    # acc = accuracy_score(y_test, y_pred)
    # log_metrics({"log_loss": loss, "accuracy": acc, "OPTIMAL_ALPHA": 2, "MSE": 2, "mae": 2})
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
    log_metrics({"log_loss1": loss, "accuracy1": acc, "OPTIMAL_ALPHA": 2, "MSE1": 2, "mae1": 2})
    log_dataset('20200807', '20200810')
    log_dataset('20200811', '20200815', dataset_type='test')


# # 子任务2
# with start_run() as f:
#     params = {
#         "objective": "multi:softprob",
#         "num_class": 3,
#         "learning_rate": 0.3,
#         "eval_metric": "mlogloss",
#         "colsample_bytree": 1.0,
#         "subsample": 1.0,
#         "seed": 42,
#     }
#     model = xgb.train(params, dtrain, evals=[(dtrain, "train")])
#     # evaluate model
#     y_proba = model.predict(dtest)
#     y_pred = y_proba.argmax(axis=1)
#     loss = log_loss(y_test, y_proba)
#     acc = accuracy_score(y_test, y_pred)
#     log_metrics({"log_loss": loss, "accuracy": acc, "OPTIMAL_ALPHA": 3, "MSE": 3, "mae": 3})

# 父任务metrics
log_metrics({"log_loss": loss, "accuracy": acc, "OPTIMAL_ALPHA": 1, "MSE": 1, "mae": 1})
log_metrics({"test1": 1, "test2": 2})