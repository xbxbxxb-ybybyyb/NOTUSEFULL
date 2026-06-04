import yaml
from alpha_invest.models.pytorch_tcn_ts import TCN

def get_tcn_task():
    config = yaml.load(open("./qlib_examples/benchmarks/TCN/workflow_config_tcn_Alpha158.yaml", "rb"))
    return config
config = get_tcn_task()
model_params = config['task']["model"]["kwargs"]
model = TCN(**model_params)
print(model)