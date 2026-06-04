import os
os.environ["use_cmo"]='True'

from sklearn import datasets
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, log_loss
import lightgbm as lgb

import mlflow
import mlflow.lightgbm
from xquant.model import log_metrics

def main():
    # prepare train and test data
    iris = datasets.load_iris()
    X = iris.data
    y = iris.target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # enable auto logging
    mlflow.lightgbm.autolog()

    train_set = lgb.Dataset(X_train, label=y_train)

    # train model
    params = {
        "objective": "multiclass",
        "num_class": 3,
        "learning_rate": 0.1,
        "metric": "multi_logloss",
        "colsample_bytree": 1.0,
        "subsample": 1.0,
        "seed": 42,
    }
    # auto_log('lightgbm')
    model = lgb.train(
        params, train_set, num_boost_round=10, valid_sets=[train_set], valid_names=["train"]
    )

    # evaluate model
    y_proba = model.predict(X_test)
    y_pred = y_proba.argmax(axis=1)
    loss = log_loss(y_test, y_proba)
    acc = accuracy_score(y_test, y_pred)

    # log metrics
    log_metrics({"log_loss": loss, "accuracy": acc, 'IC':0.1})


if __name__ == "__main__":
    main()