import os
import sys
import ray

import xgboost as xgb
from xquant.model.tracking import auto_log, log_metrics, log_params, log_artifacts, start_run, log_dataset
from sklearn import datasets
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split
from multiprocessing import Pool
from sklearn.externals.joblib import Parallel, delayed
# from joblib import Parallel, delayed

iris = datasets.load_iris()
X = iris.data
y = iris.target
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
dtrain = xgb.DMatrix(X_train, label=y_train)
dtest = xgb.DMatrix(X_test, label=y_test)

def single_task(i):
    from xquant.model.tracking import auto_log, log_metrics, log_params, log_artifacts, start_run, log_dataset
    with start_run() as f:
        params = {
            "objective": "multi:softprob",
            "num_class": 3,
            "learning_rate": 0.3,
            "eval_metric": "mlogloss",
            "colsample_bytree": 1.0,
            "subsample": 1.0,
            "seed": i,
        }
        model = xgb.train(params, dtrain, evals=[(dtrain, "train")])
        # evaluate model
        y_proba = model.predict(dtest)
        y_pred = y_proba.argmax(axis=1)
        loss = 1#log_loss(y_test, y_proba)
        acc = 2#accuracy_score(y_test, y_pred)
        log_metrics({f"log_loss{i}": loss, f"accuracy{i}": acc, "OPTIMAL_ALPHA": 3, "MSE": 3, "mae": 3})
        print(f"{i}*****************************")

        for i in range(20210909, 20210913):
            step = i
            m_dict = {'sub_a': i, 'sub_b': i * 10}
            log_metrics(m_dict, step=step)
        


Parallel(n_jobs=3)(delayed(single_task)(i) for i in range(10))

# for i in [1,2,3,4]:
#     single_task(i)

# ray.init(num_cpus = 1)
# tasks = [ray.remote(single_task).remote() for i in range(4)]
# ray.get(tasks)


