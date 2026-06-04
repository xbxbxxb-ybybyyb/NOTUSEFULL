import importlib
import os
import shutil
import time
from typing import Any, Dict, Optional

import mlflow
from mlflow.tracking.fluent import ActiveRun

from .config import AutoLogStatus, config
from .middleware import BaseLocalTrackingMiddleWare
from .utils import ignore

if not config or not config.get("middleware"):
    middleware = BaseLocalTrackingMiddleWare()
else:
    _package, class_name = config["middleware"]["class"].rsplit('.', 1)
    # get none cmo env and config if huatai package, pass
    if _package.rsplit('.', 1)[1] == 'huatai' and not os.environ.get('use_cmo'):
        pass
    else:
        middleware_package = importlib.import_module(_package)
        middleware_class = getattr(middleware_package, class_name)
        _params = config["middleware"].get("params")
        if not _params:
            middleware = middleware_class()
        else:
            assert isinstance(_params, dict), "params must be object in yaml file"
            middleware = middleware_class(**_params)


class AutoLog:
    def __init__(
            self,
            task_type,
            *args,
            run_id: str = None,
            run_name: Optional[str] = None,
            nested: bool = False,
            tags: Optional[Dict[str, Any]] = None,
            tracking=False,
            keep_raw_file=False,
            **kwargs
    ):
        """
        task_type:
            1.sklearn
            2.tensorflow
            3.xgboost
            4.lightgbm
            5.pytorch
            6.statsmodels
            7.keras
        tracking: 是否使用mlflow记录对应的信息
        """
        self.tracking = tracking
        self.before_tracking_uri = mlflow.get_tracking_uri()
        self.tmp_dir = "./__tmp"
        self.run_data_list = None
        mlflow.set_tracking_uri(self.tmp_dir)
        self.run_id = run_id
        self.run_name = run_name
        self.nested = nested
        self.tags = tags
        self.keep_raw_file = keep_raw_file
        self.start_time = time.time() * 10 ** 3

        if task_type == "sklearn":
            mlflow.sklearn.autolog(*args, silent=True, **kwargs)
        elif task_type == "tensorflow":
            mlflow.tensorflow.autolog(*args, silent=True, **kwargs)
        elif task_type == "xgboost":
            mlflow.xgboost.autolog(*args, silent=True, **kwargs)
        elif task_type == "lightgbm":
            mlflow.lightgbm.autolog(*args, silent=True, **kwargs)
        elif task_type == "pytorch":
            mlflow.pytorch.autolog(*args, silent=True, **kwargs)
        elif task_type == "statsmodels":
            mlflow.statsmodels.autolog(*args, silent=True, **kwargs)
        elif task_type == "keras":
            mlflow.keras.autolog(*args, silent=True, **kwargs)

    def __enter__(self):
        end_run()
        AutoLogStatus.active()
        self.run_obj = start_run(
            run_id=self.run_id,
            run_name=self.run_name,
            nested=self.nested,
            tags=self.tags
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        AutoLogStatus.inactive()
        mlflow.end_run()
        self.run_data_list = [
            mlflow.get_run(run_id=run_info.run_id) for run_info in
            mlflow.list_run_infos(experiment_id="0")
        ]
        self.run_data_list = [
            run for run in self.run_data_list if run.info.start_time > self.start_time
        ]
        mlflow.set_tracking_uri(self.before_tracking_uri)
        package, func_name = config.get("auto_log").get("log").rsplit(".", 1)
        config_package = importlib.import_module(package)
        func = getattr(config_package, func_name)
        func(self.run_data_list, self.tracking)
        if not self.keep_raw_file:
            shutil.rmtree(self.tmp_dir)


class Tracking:
    @ignore
    def log_params(self, param_dict: dict, **kwargs):
        res = middleware.before_log_params(param_dict)
        param_dict = res.pop("param_dict")
        res.update(kwargs)
        if res:
            # noinspection PyArgum
            middleware.after_log_params(param_dict, **res)
        else:
            middleware.after_log_params(param_dict)

    @ignore
    def log_metrics(self, metrics_dict: dict, step: Optional[int] = None, **kwargs):
        res = middleware.before_log_metrics(metrics_dict, step)
        metrics_dict = res.pop("metrics_dict")
        res.update(kwargs)
        if res:
            # noinspection PyArgumentList
            middleware.after_log_metrics(metrics_dict, **res)
        else:
            middleware.after_log_metrics(metrics_dict)

    @ignore
    def log_artifacts(self, local_file):
        res = middleware.before_log_artifacts(local_file)
        local_file = res.pop("local_file")
        if res:
            # noinspection PyArgumentList
            middleware.after_log_artifacts(local_file, **res)
        else:
            middleware.after_log_artifacts(local_file)


is_in_start_run = False


class start_run:
    def __init__(
            self,
            run_id: str = None,
            run_name: Optional[str] = None,
            nested: bool = False,
            tags: Optional[Dict[str, Any]] = None,
            order = None
    ):
        """
        :param run_id: If specified, get the run with the specified UUID and log parameters
                         and metrics under that run. The run's end time is unset and its status
                         is set to running, but the run's other attributes (``source_version``,
                         ``source_type``, etc.) are not changed.
        :param run_name: Name of new run (stored as a ``mlflow.runName`` tag).
                         Used only when ``run_id`` is unspecified.
        :param nested: Controls whether run is nested in parent run. ``True`` creates a nested run.
        :param tags: An optional dictionary of string keys and values to set as tags on the new run.
                     If an existing run is being resumed, this argument is ignored.
        :return: :py:class:`mlflow.ActiveRun` object that acts as a context manager wrapping
                 the run's state.
        """
        mlflow.end_run()
        self.order = order
        self.tags = tags
        self.nested = nested
        self.run_name = run_name
        self.run_id = run_id
        if not self.tags and self.order != None:
            self.tags = {"order": order}
        if self.tags and self.order != None:
            self.tags.update({"order": order})

    def __enter__(self) -> ActiveRun:
        global is_in_start_run
        is_in_start_run = True
        run = mlflow.start_run(
            run_id=self.run_id,
            run_name=self.run_name,
            nested=self.nested,
            tags=self.tags
        )
        return run

    def __exit__(self, exc_type, exc_val, exc_tb):
        global is_in_start_run
        is_in_start_run = False
        mlflow.end_run()


def auto_log(
        task_type,
        *args,
        **kwargs
):
    if os.getenv('RECORD_IGNORE'):
        return
    if task_type == "sklearn":
        mlflow.sklearn.autolog(*args, silent=True, **kwargs)
    elif task_type == "tensorflow":
        mlflow.tensorflow.autolog(*args, silent=True, **kwargs)
    elif task_type == "xgboost":
        mlflow.xgboost.autolog(*args, silent=True, **kwargs)
    elif task_type == "lightgbm":
        mlflow.lightgbm.autolog(*args, silent=True, **kwargs)
    elif task_type == "pytorch":
        mlflow.pytorch.autolog(*args, silent=True, **kwargs)
    elif task_type == "statsmodels":
        mlflow.statsmodels.autolog(*args, silent=True, **kwargs)
    elif task_type == "keras":
        mlflow.keras.autolog(*args, silent=True, **kwargs)


tracker = Tracking()
log_params = tracker.log_params
log_metrics = tracker.log_metrics
log_artifacts = tracker.log_artifacts
end_run = mlflow.end_run
