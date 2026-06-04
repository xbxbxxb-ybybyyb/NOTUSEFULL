import argparse
import atexit
import hashlib
import importlib
import json
import os
import shutil
import time
import typing
import uuid
import zipfile
import traceback
from os.path import join, getsize

import mlflow
import requests

from .. import tracking
from ..config import config
from ..utils import get_current_run
from sjyy.SjyyAnalytics import SjyyAnalytics
from sjyy.common.EventFactory import EventFactory
from sjyy.entities.SysProject import SysProject
from sjyy.entities.UserInfo import UserInfo
from xquant.model.mapping_metrics import mapping_metrics


DEBUG_MODE = False

config.update({"middleware": {
    "class": "xquant.model.cmo.platform.huatai.HuaTaiTrackingMiddleWare",
    "params": {"xquant_config_path": "/etc/.config/xquant_conf",
        "product_name": "XQuant", "product_id": "000465M", "function_id": 1001,
        "function_title": "Tracking", "tracking_uri": "/tmp/mlruns"}},
    "auto_log": {"log": "xquant.model.cmo.platform.huatai.log"}})
config['metrics_mapping'] = mapping_metrics
config['delete_excess_file_time'] = 10000
exp_start_time = time.time() * 10 ** 3

try:
    mlflow.sklearn.autolog(silent=True)
except Exception:
    pass

try:
    mlflow.tensorflow.autolog(silent=True)
except Exception:
    pass

try:
    mlflow.xgboost.autolog(silent=True)
except Exception:
    pass

try:
    mlflow.lightgbm.autolog(silent=True)
except Exception:
    pass

try:
    mlflow.pytorch.autolog(silent=True)
except Exception:
    pass

try:
    mlflow.statsmodels.autolog(silent=True)
except Exception:
    pass

try:
    mlflow.keras.autolog(silent=True)
except Exception:
    pass

# upload to cap platform or not
cap_tracking = False
tracking_hdfs_path = None
project_id = None
cap_tracking_local_path = None
job_id = None
cap_run_info = []
temp_outer_run_id_file = f"{config['middleware']['params']['tracking_uri']}/temp_outer_run_id"

# delete last experiment's excess file
if os.path.exists(temp_outer_run_id_file):
    with open(temp_outer_run_id_file, "r") as f:
        outer_run_id, last_time = f.read().split("_")
        if time.time() - float(last_time) > float(config["delete_excess_file_time"]):
            os.remove(temp_outer_run_id_file)


def log_cap_metrics(run_id, metrics_dict):
    for run in cap_run_info:
        if run.get("runId") == run_id:
            for key, value in metrics_dict.items():
                run["metrics"].append({"key": key, "value": value})
            break
    else:
        cap_run_info.append({"runId": run_id,
            "metrics": [{"key": key, "value": value} for key, value in
                        metrics_dict.items()], "params": [], "artifacts": []})


def log_cap_params(run_id, param_dict):
    for run in cap_run_info:
        if run.get("runId") == run_id:
            for key, value in param_dict.items():
                run["params"].append({"key": key, "value": value})
            break
    else:
        cap_run_info.append({"runId": run_id, "metrics": [],
            "params": [{"key": key, "value": value} for key, value in
                param_dict.items()], "artifacts": []})


def log_cap_artifacts(run_id, local_file):
    file_name = os.path.basename(local_file)
    for run in cap_run_info:
        if run.get("runId") == run_id:
            run["artifacts"].append({"key": file_name,
                                     "hdfsPath": f"{tracking_hdfs_path}/{file_name}"})
            break
    else:
        cap_run_info.append({"runId": run_id, "metrics": [], "params": [],
            "artifacts": [{"key": file_name,
                           "hdfsPath": f"{tracking_hdfs_path}/{file_name}"}]})
    copy_to_cap_tracking(run_id, local_file)


# Use environment variable CONF_FILE to judge whether to upload to cap or not
cap_config_file = os.environ.get('_CONF_FILE')
if cap_config_file and os.path.exists(cap_config_file):
    cap_tracking = True
    with open(cap_config_file, "r", encoding="utf-8") as f:
        module_info = f.read()
    project_id = module_info.get("module", {}).get("projectId")
    job_id = module_info["runtimeInfo"]["logKey"].split("/")[-2]
    tracking_hdfs_path = module_info['module']['outputs'][-1]['value']
    parser = argparse.ArgumentParser()
    tracker_name = config["cap"].get("tracking_output", "tracking")
    parser.add_argument(f"--{tracker_name}")
    args = parser.parse_args()
    cap_tracking_local_path = getattr(args, tracker_name)
    if "'" in cap_tracking_local_path:
        cap_tracking_local_path = cap_tracking_local_path[1:-1]


def copy_to_cap_tracking(run_id, path):
    if not os.path.exists(f"{cap_tracking_local_path}/{run_id}"):
        os.mkdir(f"{cap_tracking_local_path}/{run_id}")
    if os.path.isfile(path):
        shutil.copyfile(path,
                        f"{cap_tracking_local_path}/{run_id}/{os.path.basename(path)}")
    else:
        try:
            shutil.copytree(path,
                            f"{cap_tracking_local_path}/{run_id}/{os.path.basename(path)}")
        except Exception:
            pass


def upload_to_cap(patch_data):
    """
    Support both 30014 port and 30016 port
    """
    headers = {'Content-Type': 'application/json', 'charset': 'UTF-8',
               'Authorization': 'Basic YWRtaW4='}
    port = config["cap"].get("port", "30014")
    if port == "30014":
        patch_url = f'http://{config["cap"]["host"]}:{port}/api' \
            f'/v1/jobs/{job_id}/modelResults'
    elif port == "30016":
        patch_url = f'http://{config["cap"]["host"]}:{port}/api' \
            f'/v1/projects/{project_id}/jobs/{job_id}/modelResults'
    else:
        raise ValueError("Port must be one of:30014,30016")
    requests.put(patch_url, headers=headers, json=patch_data)


def get_dir_size(dir):
    size = 0
    for root, dirs, files in os.walk(dir):
        size += sum([getsize(join(root, name)) for name in files])
    return size


def get_file_md5(file_name=None, file_obj=None):
    m = hashlib.md5()
    if file_name:
        f = open(file_name, 'rb')
    else:
        f = file_obj
    while True:
        data = f.read(4096)
        if not data:
            break
        m.update(data)

    return m.hexdigest()


def zip_file(dir_path, output_path):
    z = zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED)
    for base_path, folder_list, file_list in os.walk(dir_path):
        relative_path = base_path.replace(dir_path, '')
        for file_name in file_list:
            z.write(os.path.join(base_path, file_name),
                    os.path.join(relative_path, file_name))
    z.close()


def get_file_info(filename):
    if os.path.isfile(filename):
        file_size = os.path.getsize(filename)
        file_md5 = get_file_md5(filename)
    else:
        file_size = get_dir_size(filename)
        zip_file(filename, "tmp.zip")
        file_md5 = get_file_md5("tmp.zip")
        os.remove("tmp.zip")
    return {"file_size": file_size, "file_md5": file_md5}


class HuaTaiTracker:
    def _init_user_info(self):
        """
        初始化用户信息:
            1.配置文件获取userId
            2.用户状态为登录状态即可
        """
        user_info = UserInfo()
        user_info.setDistinct_id(self.xquant_config.get("userId"))
        user_info.setIs_login_id(1)
        return user_info

    @staticmethod
    def _init_product(product_name, product_id, channel_env):
        """
        初始化系统信息:
            1.project名字
            2.project id
            3.对应的频道channel
        """
        sys_project = SysProject()
        sys_project.setProduct_name(product_name)
        sys_project.setProduct_id(product_id)
        sys_project.setChannel_env(channel_env)
        return sys_project

    def _init_exp(self, function_id, function_title):
        """
        初始化方法事件:
            1.function id
            2.function title
        """
        event = EventFactory.creatEvents("function")
        event.setUserInfo(self.user_info)
        event.setSysProject(self.sys_project)
        event.setEvent("function")
        event.setTime(int(time.time() * 1000))
        event.setFunction_id(function_id)
        event.setFunction_title(function_title)
        return event

    def set_param(self, param: typing.Union[dict, list]):
        """
        追踪数据
        """
        self.event.setParam(str(json.dumps(param)).replace("\"", "'"))
        if DEBUG_MODE:
            print('======param======')
            print(param)
        sa = SjyyAnalytics(self.event_trace_env, bulk_size=1, use_thread=False)
        sa.addEvents(self.event)

    def __init__(self, xquant_config, product_name, product_id, function_id,
            function_title, channel_env, event_trace_env):
        self.xquant_config = xquant_config
        self.user_info = self._init_user_info()
        self.sys_project = self._init_product(product_name, product_id,
                                              channel_env)
        self.event = self._init_exp(function_id, function_title)
        self.event_trace_env = event_trace_env


tracker: typing.Optional[HuaTaiTracker] = None
exp_id = str(uuid.uuid1())
outer_run_id = None
xquant_config = {}
is_parent_process = False


class HuaTaiTrackingMiddleWare:
    def _parse_xquant_config(self, xquant_config_path):
        with open(xquant_config_path, "r", encoding="utf8") as f:
            for line in f:
                if not line.strip():
                    continue
                res = line.strip().split("=", maxsplit=1)
                if len(res) == 2:
                    self.xquant_config[res[0]] = res[1]

    def __init__(self, xquant_config_path, product_name, product_id,
            function_id, function_title, tracking_uri,
            channel_env=os.environ.get('ENV_VERSION', 'uat'),
            event_trace_env=os.environ.get('ENV_VERSION', 'sit'),
            keep_raw_file=True):
        mlflow.set_tracking_uri(tracking_uri)
        global outer_run_id
        global is_parent_process
        # chile process
        if os.path.exists(temp_outer_run_id_file):
            with open(temp_outer_run_id_file, "r") as f:
                outer_run_id, _ = f.read().split("_")
        else:
            # parent process
            is_parent_process = True
            out_run = mlflow.start_run()
            outer_run_id = out_run.info.run_id
            mlflow.set_tag("pid", os.getpid())
            with open(temp_outer_run_id_file, "w") as f:
                f.write(f"{outer_run_id}_{time.time()}")
        global xquant_config
        self.xquant_config = {}
        self._parse_xquant_config(xquant_config_path)
        xquant_config = self.xquant_config
        global tracker
        tracker = HuaTaiTracker(self.xquant_config, product_name, product_id,
            function_id, function_title, channel_env, event_trace_env, )

        @atexit.register
        def auto_log_upload():
            """
            进程结束上传AutoLog产生的结果
            """
            run = mlflow.get_run(run_id=outer_run_id)
            parent_pid = int(run.data.tags.get("pid"))
            if parent_pid != os.getpid():
                exit()
            if os.path.exists(temp_outer_run_id_file):
                os.remove(temp_outer_run_id_file)
            if os.getenv('RECORD_IGNORE'):
                exit()
            try:
                run_data_list = [mlflow.get_run(run_id=run_info.run_id) for
                    run_info in mlflow.list_run_infos(experiment_id="0")]
                run_data_list = [run for run in run_data_list if
                    run.info.start_time > exp_start_time]
                package, func_name = config.get("auto_log").get("log").rsplit(
                    ".", 1)
                config_package = importlib.import_module(package)
                # upload to huatai's kafka
                func = getattr(config_package, func_name)
                tracking.end_run()
                func(run_data_list, False)
                # Upload To Cap Or Not
                if cap_tracking:
                    upload_to_cap(patch_data={"modelResults": cap_run_info})
            except Exception as e:
                print(traceback.print_exc())
                raise e
            finally:
                if not keep_raw_file:
                    shutil.rmtree(
                        config['middleware']['params']['tracking_uri'])

    @staticmethod
    def before_log_params(param_dict: dict):
        return {"param_dict": param_dict, "type": "log_params"}

    def after_log_params(self, param_dict: dict, **kwargs):
        for param in param_dict.keys():
            assert "." not in param, f"{param} must no have a value ."
        # is_in_start_run param to solve the problem of removing end_run without context env
        run_id = get_current_run().info.run_id if tracking.is_in_start_run else outer_run_id

        run = mlflow.get_run(run_id=run_id)
        get_parent_run_id = True if run.data.tags.get(
            'parent_run_id') else False
        # load params tags from disk
        user_params = run.data.tags.get("user_params", [])
        if user_params:
            user_params = eval(user_params)
        params = run.data.tags.get("params", [])
        if params:
            params = eval(params)
        # different logic from parent run and inner run
        if get_parent_run_id:
            mlflow.set_tag("parent_run_id", outer_run_id)
        else:
            mlflow.end_run()
            mlflow.start_run(run_id=outer_run_id)
        # record params to disk
        mlflow.log_params(param_dict)
        if kwargs.get("user_params"):
            user_params.extend(list(param_dict.keys()))
            mlflow.set_tag("user_params", list(set(user_params)))
        else:
            params.extend(list(param_dict.keys()))
            mlflow.set_tag("params", list(set(params)))
        # record to cap platform or not
        if cap_tracking:
            log_cap_params(run_id, param_dict)

    @staticmethod
    def before_log_metrics(metrics_dict: dict, step=None):
        return {"metrics_dict": metrics_dict, "step": step}

    def after_log_metrics(self, metrics_dict: dict, **kwargs):
        for metric in metrics_dict.keys():
            assert "." not in metric, f"{metric} must no have a value ."
        run_id = get_current_run().info.run_id if tracking.is_in_start_run else outer_run_id
        run = mlflow.get_run(run_id=run_id)
        get_parent_run_id = True if run.data.tags.get(
            'parent_run_id') else False
        # load metrics tags from disk
        user_metrics = run.data.tags.get("user_metrics", [])
        if user_metrics:
            user_metrics = eval(user_metrics)
        metrics = run.data.tags.get("metrics", [])
        if metrics:
            metrics = eval(metrics)
        # different logic from parent run and inner run
        if get_parent_run_id:
            mlflow.set_tag("parent_run_id", outer_run_id)
        else:
            mlflow.end_run()
            mlflow.start_run(run_id=outer_run_id)
        # record metrics to disk
        mlflow.log_metrics(metrics_dict, step=kwargs.get("step"))
        if kwargs.get("user_metrics") or kwargs.get("step"):
            user_metrics.extend(list(metrics_dict.keys()))
            mlflow.set_tag("user_metrics", list(set(user_metrics)))
        else:
            metrics.extend(list(metrics_dict.keys()))
            mlflow.set_tag("metrics", list(set(metrics)))
        if cap_tracking:
            log_cap_metrics(run_id, metrics_dict)

    @staticmethod
    def before_log_artifacts(local_file):
        return {"local_file": local_file}

    def after_log_artifacts(self, local_file):
        run_id = get_current_run().info.run_id if tracking.is_in_start_run else outer_run_id
        run = mlflow.get_run(run_id=run_id)
        get_parent_run_id = True if run.data.tags.get(
            'parent_run_id') else False
        # load metrics tags from disk
        artifacts = run.data.tags.get("artifacts", [])
        if artifacts:
            artifacts = eval(artifacts)
        # different logic from parent run and inner run
        if get_parent_run_id:
            mlflow.set_tag("parent_run_id", outer_run_id)
        else:
            mlflow.end_run()
            mlflow.start_run(run_id=outer_run_id)
        mlflow.log_artifact(local_file)
        artifacts.append(os.path.basename(local_file))
        mlflow.set_tag("artifacts", list(set(artifacts)))
        if cap_tracking:
            log_cap_artifacts(run_id, local_file)


def auto_log_params(run_data, run_id, order, get_parent_run_id):
    """
    进程结束后自动上报params指标
    """
    # params split
    user_params_set = run_data.data.tags.get("user_params", [])
    if user_params_set:
        user_params_set = eval(user_params_set)
    user_params = {param: value for param, value in run_data.data.params.items() if param in user_params_set}
    params = {param: value.replace('\'', '') for param, value in run_data.data.params.items() if param not in user_params_set}
    if user_params:
        base_info = {
            "exp_id": exp_id,
            "run_id": run_id,
            "user_params": user_params,
            "xquant_id": int(xquant_config["xquantId"]),
            "tags": {"run_start_time": str(run_data.info.start_time)}
        }
        if get_parent_run_id:
            base_info["tags"]["parent_run_id"] = outer_run_id
        if order:
            base_info["tags"]["sub_id"] = order
        else:
            base_info["tags"]["sub_id"] = str(run_data.info.start_time)
        tracker.set_param(base_info)
    if params:
        base_info = {
            "exp_id": exp_id,
            "run_id": run_id,
            "params": params,
            "xquant_id": int(xquant_config["xquantId"]),
            "tags": {"run_start_time": str(run_data.info.start_time)}
        }
        if get_parent_run_id:
            base_info["tags"]["parent_run_id"] = outer_run_id
        if order:
            base_info["tags"]["sub_id"] = order
        else:
            base_info["tags"]["sub_id"] = str(run_data.info.start_time)
        tracker.set_param(base_info)
        if cap_tracking:
            log_cap_params(run_id=run_id, param_dict=run_data.data.params)


def auto_log_metrics(run_data, run_id, order, get_parent_run_id):
    """
    进程结束后自动上报metrics指标
    """
    metrics_mapping = config.get("metrics_mapping", {})
    user_metrics_set = run_data.data.tags.get("user_metrics", [])
    if user_metrics_set:
        user_metrics_set = eval(user_metrics_set)
    user_metrics = {metrics_mapping.get(metric, metric): value for metric, value in run_data.data.metrics.items() if
                    metric in user_metrics_set}
    metrics = {metrics_mapping.get(metric, metric): value.replace('\'', '')  for metric, value in run_data.data.metrics.items() if
               metric not in user_metrics_set}
    if user_metrics:
        base_info = {
            "exp_id": exp_id,
            "run_id": run_id,
            "user_metrics": user_metrics,
            "xquant_id": int(xquant_config["xquantId"]),
            "tags": {"run_start_time": str(run_data.info.start_time)}
        }
        if get_parent_run_id:
            base_info["tags"]["parent_run_id"] = outer_run_id
        if order:
            base_info["tags"]["sub_id"] = order
        else:
            base_info["tags"]["sub_id"] = str(run_data.info.start_time)
        tracker.set_param(base_info)
    if metrics:
        base_info = {
            "exp_id": exp_id,
            "run_id": run_id,
            "metrics": metrics,
            "xquant_id": int(xquant_config["xquantId"]),
            "tags": {"run_start_time": str(run_data.info.start_time)}
        }
        if get_parent_run_id:
            base_info["tags"]["parent_run_id"] = outer_run_id
        if order:
            base_info["tags"]["sub_id"] = order
        else:
            base_info["tags"]["sub_id"] = str(run_data.info.start_time)
        tracker.set_param(base_info)
        if cap_tracking:
            log_cap_metrics(run_id=run_id, metrics_dict=run_data.data.metrics)


def auto_log_artifacts(run_data, run_id, order, get_parent_run_id):
    """
    进程结束后自动上报artifacts指标
    """
    manual_artifacts = run_data.data.tags.get("artifacts", [])
    path = run_data.info.artifact_uri.replace("file:///", "")
    if not os.path.exists(path):
        path = run_data.info.artifact_uri.replace("file://", "")
    for artifact in os.listdir(path):
        if artifact not in manual_artifacts:
            continue
        artifact_path = os.path.join(path, artifact)
        file_info = get_file_info(artifact_path)
        base_info = {
            "exp_id": exp_id,
            "run_id": run_id,
            "xquant_id": int(xquant_config["xquantId"]),
            "file_path": artifact_path,
            "size": file_info.get("file_size"),
            "md5": file_info.get("file_md5"),
            "tags": {"run_start_time": str(run_data.info.start_time)}
        }
        if get_parent_run_id:
            base_info["tags"]["parent_run_id"] = outer_run_id
        if order:
            base_info["tags"]["sub_id"] = order
        else:
            base_info["tags"]["sub_id"] = str(run_data.info.start_time)
        tracker.set_param(base_info)
        if cap_tracking:
            log_cap_artifacts(run_id=run_id, local_file=artifact_path)


def auto_log_user_step_metrics(run_data, run_id, order, get_parent_run_id):
    """
    进程结束后自动上报时间序列指标
    """
    base_path = f'{config["middleware"]["params"]["tracking_uri"]}/0/{run_id}/metrics'
    user_step_metrics = {}
    for metric_name in os.listdir(base_path):
        steps = []
        values = []
        timestamps = []
        if os.path.isdir(f"{base_path}{os.sep}{metric_name}"):
            continue
        with open(f"{base_path}{os.sep}{metric_name}", "r") as f:
            lines = f.read().strip().split("\n")
            if len(lines) == 1:
                continue
            for line in lines:
                timestamp, value, step = line.split()
                steps.append(str(step))
                values.append(str(value))
                timestamps.append(str(timestamp))
        user_step_metrics[metric_name] = {
            "step": ','.join(steps),
            "value": ','.join(values),
            "timestamp": ','.join(timestamps)
        }
    if not user_step_metrics:
        return
    base_info = {
        "exp_id": exp_id,
        "run_id": run_id,
        "xquant_id": int(xquant_config["xquantId"]),
        "tags": {"run_start_time": str(run_data.info.start_time)},
        "user_step_metrics": user_step_metrics
    }
    if get_parent_run_id:
        base_info["tags"]["parent_run_id"] = outer_run_id
    if order:
        base_info["tags"]["sub_id"] = order
    else:
        base_info["tags"]["sub_id"] = str(run_data.info.start_time)
    tracker.set_param(base_info)


def log(run_data_list, track):
    for run_data in run_data_list:
        run_id = run_data.info.run_id
        order = run_data.data.tags.get("order")
        get_parent_run_id = True if run_data.data.tags.get(
            'parent_run_id') else False
        # params split
        auto_log_params(run_data, run_id, order, get_parent_run_id)
        # metrics split
        auto_log_metrics(run_data, run_id, order, get_parent_run_id)
        # log manual log_artifact's artifact instead of auto-logging
        if run_data.info.artifact_uri:
            auto_log_artifacts(run_data, run_id, order, get_parent_run_id)
        # log user step metrics
        auto_log_user_step_metrics(run_data, run_id, order, get_parent_run_id)
