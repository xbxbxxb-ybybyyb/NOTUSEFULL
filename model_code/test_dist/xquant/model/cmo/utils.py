import os

from mlflow.entities import Run


def ignore(func):
    def wrapper(*args, **kwargs):
        if os.getenv('RECORD_IGNORE'):
            pass
        else:
            return func(*args, **kwargs)

    return wrapper


def get_current_run() -> Run:
    """
    得到当前上下文中的run信息
    """
    import mlflow
    from mlflow.tracking.fluent import _get_or_start_run
    run_id = _get_or_start_run().info.run_id
    run_obj = mlflow.get_run(run_id=run_id)
    return run_obj
