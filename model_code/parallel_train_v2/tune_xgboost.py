from xgboost_ray import RayDMatrix, RayParams, train
import torch
import pandas as pd
from sklearn.datasets import load_breast_cancer

num_actors = 8
num_cpus_per_actor = 1

ray_params = RayParams(
    num_actors=num_actors,
    cpus_per_actor=num_cpus_per_actor)

def train_model(config):
    data_params = {"train_date": ["20220418"],
                   "strategy_type_factor": ["factor1"],
                   "num_samples": 2000, "input_size": 10, "output_size":1,
                   "share_factor": "factor_share"}
    data = pd.DataFrame(torch.randn(data_params['num_samples'], data_params['input_size']).numpy())
    label = pd.DataFrame(torch.randint(2, (data_params['num_samples'], data_params['output_size'])).numpy())
    train_set = RayDMatrix(data, label)

    evals_result = {}
    bst = train(
        num_boost_round= 20,
        params=config,
        dtrain=train_set,
        evals_result=evals_result,
        evals=[(train_set, "train")],
        verbose_eval=False,
        ray_params=ray_params)
    bst.save_model("model.xgb")
    print(evals_result)

from ray import tune

# Specify the hyperparameter search space.
config = {
    "tree_method": "approx",
    "objective": "binary:logistic",
    "eval_metric": ["logloss", "error"],
}

if __name__=="__main__":
    train_model(config)