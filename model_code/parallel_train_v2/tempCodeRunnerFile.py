
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