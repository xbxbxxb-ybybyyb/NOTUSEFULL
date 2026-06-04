import json
import logging
import os
from dataclasses import dataclass
from typing import List

import ray
import xgboost as xgb
from .tracker import RabitTracker
import multiprocessing

from .backend import DistTrainBackend, DistBackendConfig
from .session import shutdown_session
from .utils import get_address_and_port
from .worker_group import WorkerGroup
from .depends.annotations import PublicAPI

logger = logging.getLogger(__name__)


class _RabitTracker(RabitTracker):
    def __init__(self, num_workers):
        """
        The Rabit tracker is the main process that all local workers connect to to share their weights.
        """
        host = get_address_and_port()[0]
        self.env = {"DMLC_NUM_WORKER": num_workers}
        super().__init__(host, num_workers)
        self.env.update(self.slave_envs())# Get tracker Host + IP
        self.start(num_workers)

    def start(self, nworker):
        """
        This method overwrites the xgboost-provided RabitTracker to switch
        from a daemon thread to a multiprocessing Process. This is so that
        we are able to terminate/kill the tracking process at will.

        In python 3.8, spawn is used as default process creation on macOS.
        But spawn doesn't work because `run` is not pickleable.
        For now we force the start method to use fork.
        """
        if getattr(self, "thread"):
            """
            When one or more actors die, we want to restart the Rabit tracker, too, for two reasons: 
            First we don't want to be potentially stuck with stale connections from old training processes.
            Second, we might restart training with a different number of actors, and for that we would have to restart the tracker anyway.
            """
            self.stop()
        multiprocessing.set_start_method("fork", force=True)

        def run():
            self.accept_slaves(nworker)

        self.thread = multiprocessing.Process(target=run, args=())
        self.thread.start()


    def stop(self):
        self.thread.join(timeout=5)
        self.thread.terminate()


class _RabitContext:
    """This context is used by local training actors to connect to the Rabit tracker.
    Args:
        actor_id (str): Unique actor ID
        args (list): Arguments for Rabit initialisation. These are
            environment variables to configure Rabit clients.
    """
    def __init__(self, actor_id, args):
        self.args = args
        self.args.append(("DMLC_TASK_ID=[distxgboost]:" + actor_id).encode())

    def __enter__(self):
        xgb.rabit.init(self.args)

    def __exit__(self, *args):
        xgb.rabit.finalize()


@PublicAPI(stability="beta")
@dataclass
class XGBoostConfig(DistBackendConfig):
    @property
    def backend_cls(self):
        return XGBoostBackend


def setup_xgboost_environment(rabit_args: List[str], index: int):
    """Set up distributed Tensorflow training information.

    This function should be called on each worker.

    Args:
        worker_addresses (list): Addresses of all the workers.
        index (int): Index (i.e. world rank) of the current worker.
    """
    os.environ["xgboost_rabit_args"] = json.dumps({"rabit_args":rabit_args})
    os.environ["xgboost_world_index"] = str(index)

def get_rabit_centext():
    actor_id = os.environ["xgboost_world_index"]
    rabit_args = json.loads(os.environ["xgboost_rabit_args"])["rabit_args"]
    rabit_args = [arg.encode() for arg in rabit_args]
    return _RabitContext(str(actor_id), rabit_args)


class XGBoostBackend(DistTrainBackend):
    def on_start(self, worker_group: WorkerGroup,
                 backend_config: XGBoostConfig):

        num_workers = len(worker_group)
        self.rabit = _RabitTracker(num_workers)
        self.rabit_args = [("%s=%s" % item) for item in self.rabit.env.items()]

        # Get setup tasks in order to throw errors on failure.
        setup_futures = []
        for i in range(len(worker_group)):
            setup_futures.append(
                worker_group.execute_single_async(
                    i,
                    setup_xgboost_environment,
                    rabit_args=self.rabit_args,
                    index = i))
        ray.get(setup_futures)

    def handle_failure(self, worker_group: WorkerGroup,
                       failed_worker_indexes: List[int],
                       backend_config: DistBackendConfig):
        """Failure handling for Tensorflow.

        Instead of restarting all workers, the failed workers are
        removed from the ``WorkerGroup``. The backend and session are
        shutdown on the remaining workers. Then new workers are added back in.
        """
        worker_group.remove_workers(failed_worker_indexes)
        if len(worker_group) > 0:
            self.on_shutdown(worker_group, backend_config)
            worker_group.execute(shutdown_session)
        worker_group.add_workers(len(failed_worker_indexes))
        self.on_start(worker_group, backend_config)

    def on_shutdown(self, worker_group: WorkerGroup,
                    backend_config: DistBackendConfig):
        self.rabit.stop()
