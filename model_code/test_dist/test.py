import xgboost as xgb
from xquant.model.tracking import log_metrics, log_params, start_run, parse_params, log_dataset, log_artifacts
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


dataset = {0: ('20200101', '20200301'), 
            1: ('20200301', '20200601'),
            2: ('20200601', '20200901')}

dataset_test = {0: ('20200301', '20200305'), 
            1: ('20200601', '20200605'),
            2: ('20200901', '20200905')}

import random

for i in range(3):
    #子任务在前端界面上按时间顺序倒序展示
    with start_run() as f:
        params = {
            "objective": "multi:softprob",
            "num_class": 3,
            "learning_rate": round(random.random(),2) ,
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
        log_dataset(dataset[i][0], dataset[i][1], dataset_type='train')
        log_dataset(dataset_test[i][0], dataset_test[i][1], dataset_type='test')
        
        for j in range(i*3, (i+1) *3):
            step = j
            m_dict = {'sub_a': random.random(), 'sub_b': random.random() * 10}
            log_metrics(m_dict, step=step)
        log_metrics({"log_loss": loss, "accuracy": acc, "OPTIMAL_ALPHA": random.random(), "MSE": random.random(), "MAE": random.random(),  "IC": random.random()})

log_artifacts('/data/user/012620/model')

# 父任务数据时间范围
log_dataset('20200101', '20201231', dataset_type='train')
log_dataset('20210101', '20211001', dataset_type='test')

# 父任务metrics
log_metrics({"log_loss": loss, "accuracy": acc, "OPTIMAL_ALPHA": random.random(), "MSE": random.random(), "MAE": random.random(), "IC": random.random()})
log_metrics({"test1": 1, "test2": 2})