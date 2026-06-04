# -*- coding: utf-8 -*-
import os
os.environ["use_cmo"]='True'
import ray

import xgboost as xgb
from xquant.model import auto_log, log_metrics, log_params, log_artifacts, \
    start_run
from sklearn import datasets
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split
from multiprocessing import Pool


@ray.remote(max_calls=1)
def sub_task(start_time, end_time, seed):
    print('==========ssss==========')
    iris = datasets.load_iris()
    X = iris.data
    y = iris.target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2,
                                                        random_state=42)
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)
    with start_run(tag=str(seed) + 'a') as f:
        params = {"objective": "multi:softprob", "num_class": 3,
                  "learning_rate": 0.5, "eval_metric": "mlogloss",
                  "colsample_bytree": 1.0, "subsample": 1.0,
                  "seed": 40 + seed, }
        model = xgb.train(params, dtrain, evals=[(dtrain, "train")])
        # evaluate model
        y_proba = model.predict(dtest)
        y_pred = y_proba.argmax(axis=1)
        loss = log_loss(y_test, y_proba)
        acc = accuracy_score(y_test, y_pred)
        log_params({'alpha': seed, 'beta': seed})
        log_metrics({"log_loss": loss, "accuracy": acc, "OPTIMAL_ALPHA": seed,
                     "MSE": seed, "mae": seed, "IC": seed})
        log_artifacts('model_config.yaml')
        for i in range(start_time, end_time):
            step = i
            m_dict = {'sub_a': i, 'sub_b': i * 10}
            log_metrics(m_dict, step=step)

        print('=====sub=====')


if __name__=="__main__":
    ray.init(num_cpus=2)
    tasks = [(20210901, 20210905, 1), (20210905, 20210909, 2), (20210909, 20210913, 3), (20210913, 20210917, 4)]
    tasks_id = [sub_task.remote(start_time, end_time, seed) for start_time, end_time, seed in tasks]
    ray.get(tasks_id)

    # 父任务metrics
    iris = datasets.load_iris()
    X = iris.data
    y = iris.target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2,
                                                        random_state=42)
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)
    params = {"objective": "multi:softprob", "num_class": 3,
              "learning_rate": 0.5, "eval_metric": "mlogloss",
              "colsample_bytree": 1.0, "subsample": 1.0, "seed": 4, }
    # model = xgb.train(params, dtrain, evals=[(dtrain, "train")])
    log_params({'alpha': 0, 'beta': 0, 'seed': 4, 'num_boost_round': 10})
    log_metrics({"MSE": 1, "mae": 1, 'IC': 0})
    log_artifacts('test_mult_process.py')
    for i in range(1, 5):
        step = i
        m_dict = {'a': i, 'b': i * 10, 'OPTIMAL_ALPHA': i * 100}
        log_metrics(m_dict, step=step)
