import os
os.environ['ENV_VERSION'] = 'uat'

from xquant.model.tracking import log_params, log_metrics, log_artifacts

log_params({
    "input1": 11,
    "input2": 22
})
log_metrics({
    "mae": 11,
    "mse": 22
})
log_artifacts(
    "configure.yaml"
)