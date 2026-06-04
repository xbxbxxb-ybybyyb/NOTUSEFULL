import mlflow


class BaseLocalTrackingMiddleWare:
    def __init__(self, local_path=None):
        if not local_path:
            local_path = ""
        mlflow.set_tracking_uri(local_path)

    @staticmethod
    def before_log_params(param_dict: dict):
        return {
            "param_dict": param_dict
        }

    @staticmethod
    def after_log_params(param_dict: dict):
        mlflow.log_params(params=param_dict)

    @staticmethod
    def before_log_metrics(metrics_dict: dict, step=None):
        return {
            "metrics_dict": metrics_dict,
            "step": step
        }

    @staticmethod
    def after_log_metrics(metrics_dict: dict, **kwargs):
        mlflow.log_metrics(metrics=metrics_dict, step=kwargs.get("step"))

    @staticmethod
    def before_log_artifacts(local_file):
        return {
            "local_file": local_file
        }

    @staticmethod
    def after_log_artifacts(local_file):
        mlflow.log_artifact(local_path=local_file)


class MLflowServiceTrackingMiddleWare(BaseLocalTrackingMiddleWare):
    def __init__(self, address):
        super(BaseLocalTrackingMiddleWare).__init__()
        mlflow.set_tracking_uri(address)
