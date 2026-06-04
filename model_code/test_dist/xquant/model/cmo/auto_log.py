import importlib
import logging
import os

from .config import config
from .tracking import start_run, log_params, log_metrics, log_artifacts


def auto_log_params(run_data, params):
    logging.info(run_data, params)


def auto_log_metrics(run_data, metrics):
    logging.info(run_data, metrics)


def auto_log_artifacts(run_data, file_path):
    logging.info(run_data, file_path)


auto_log = config.get("auto_log")
for config_name in ["log_params_func", "log_metrics_func", "log_artifacts_func"]:
    package, func_name = auto_log.get(config_name).rsplit(".", 1)
    config_package = importlib.import_module(package)
    func = getattr(config_package, func_name)
    if config_name == "log_params_func":
        auto_log_params = func
    if config_name == "log_metrics_func":
        auto_log_metrics = func
    if config_name == "log_artifacts_func":
        auto_log_artifacts = func


def log(run_data_list, tracking):
    for run_data in run_data_list:
        with start_run(
                nested=True if run_data.data.tags.get('mlflow.parentRunId') else False
        ):
            if tracking:
                log_params(run_data.data.params)
            auto_log_params(run_data, run_data.data.params)
            if tracking:
                log_metrics(run_data.data.metrics)
            auto_log_metrics(run_data, run_data.data.metrics)
            if run_data.info.artifact_uri:
                for artifact in os.listdir(run_data.info.artifact_uri):
                    artifact_path = os.path.join(run_data.info.artifact_uri, artifact)
                    if tracking:
                        log_artifacts(artifact_path)
                    auto_log_artifacts(run_data, artifact_path)
