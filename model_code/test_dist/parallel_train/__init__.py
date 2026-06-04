from parallel_train.trainer import XGBoostActor
from parallel_train.trainer import XGBWrapActor

def get_module_actor(module_name):
    if module_name == "XGBoostActor":
        return XGBoostActor.XGBoostActor
    if module_name == "XGBWrapActor":
        return XGBWrapActor.XGBWrapActor
