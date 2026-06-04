from .train.depends.annotations import PublicAPI
from typing import Optional, Dict, Callable
from .train.utils import RayDataset
import warnings
import ray


class SessionTask:
    """Holds information for training on each worker."""

    def __init__(self,
                 world_rank: int,
                 local_rank: int,
                 world_size: int,
                 checkpoint: Optional[Dict] = None):

        # The Thread object that is running the training function.
        self.world_rank = world_rank
        self.local_rank = local_rank
        self.world_size = world_size
        self.loaded_checkpoint = checkpoint
        self.local_ip = self.get_current_ip()

    def get_current_ip(self):
        self.local_ip = ray.util.get_node_ip_address()
        return self.local_ip

    def checkpoint(self, **kwargs):
        """Adds kwargs to the queue to be consumed by main thread.

        Also stores the checkpoint in ``self.loaded_checkpoint``.
        """

        # Update session checkpoint to latest checkpoint.
        self.loaded_checkpoint = kwargs


_task_session = None
_task_mode = 'DistTrain'


def init_session(*args, **kwargs) -> None:
    global _task_mode
    _task_mode = kwargs.pop('task_mode', 'DistTrain')

    if _task_mode == 'LocalTrain':
        global _task_session
        if _task_session:
            raise ValueError("A Train session is already in use. Do not call "
                             "`init_session()` manually.")
        _task_session = SessionTask(*args, **kwargs)
    elif _task_mode == 'DistTrain':
        from .train.session import init_session
        init_session(args, kwargs)


def get_session():
    global _task_mode
    if _task_mode == 'LocalTrain':
        global _task_session
        if _task_session is None or not isinstance(_task_session, SessionTask):
            raise ValueError("Trying to access a Train session that has not been "
                             "initialized yet. ")
        return _task_session
    elif _task_mode == 'DistTrain':
        from .train.session import get_session
        return get_session()


def shutdown_session():
    """Shuts down the initialized session."""
    global _task_mode
    if _task_mode == 'LocalTrain':
        global _task_session
        _task_session = None
    elif _task_mode == 'DistTrain':
        from .train.session import shutdown_session
        return shutdown_session()


@PublicAPI(stability="beta")
def get_dataset_shard(
        dataset_name: Optional[str] = None) -> Optional[RayDataset]:
    """Returns the Ray Dataset or DatasetPipeline shard for this worker.

    You should call ``to_torch()`` or ``to_tf()`` on this shard to convert
    it to the appropriate framework-specific Dataset.

    .. code-block:: python

        import ray
        from ray import train

        def train_func():
            model = Net()
            for iter in range(100):
                data_shard = train.get_dataset_shard().to_torch()
                model.train(data_shard)
            return model

        dataset = ray.data.read_csv("train.csv")
        dataset.filter(...).repeat().random_shuffle()

        trainer = Trainer(backend="torch")
        trainer.start()
        # Trainer will automatically handle sharding.
        train_model = trainer.run(train_func, dataset=dataset)
        trainer.shutdown()

    Args:
        dataset_name (Optional[str]): If a Dictionary of Datasets was passed to
            ``Trainer``, then specifies which dataset shard to return.


    Returns:
        The ``Dataset`` or ``DatasetPipeline`` shard to use for this worker.
        If no dataset is passed into Trainer, then return None.
    """
    session = get_session()
    shard = session.dataset_shard
    if shard is None:
        warnings.warn("No dataset passed in. Returning None. Make sure to "
                      "pass in a Ray Dataset to Trainer.run to use this "
                      "function.")
    elif isinstance(shard, dict):
        if not dataset_name:
            raise RuntimeError(
                "Multiple datasets were passed into ``Trainer``, "
                "but no ``dataset_name`` is passed into "
                "``get_dataset_shard``. Please specify which "
                "dataset shard to retrieve.")
        return shard[dataset_name]
    return shard


@PublicAPI(stability="beta")
def report(**kwargs) -> None:
    """Reports all keyword arguments to Train as intermediate results.

    .. code-block:: python

        import time
        from ray import train

        def train_func():
            for iter in range(100):
                time.sleep(1)
                train.report(hello="world")

        trainer = Trainer(backend="torch")
        trainer.start()
        trainer.run(train_func)
        trainer.shutdown()

    Args:
        **kwargs: Any key value pair to be reported by Train.
            If callbacks are provided, they are executed on these
            intermediate results.
    """
    session = get_session()
    session.report(**kwargs)


@PublicAPI(stability="beta")
def world_rank() -> int:
    """Get the world rank of this worker.

    .. code-block:: python

        import time
        from ray import train

        def train_func():
            for iter in range(100):
                time.sleep(1)
                if train.world_rank() == 0:
                    print("Worker 0")

        trainer = Trainer(backend="torch")
        trainer.start()
        trainer.run(train_func)
        trainer.shutdown()

    """
    session = get_session()
    return session.world_rank


@PublicAPI(stability="beta")
def local_rank() -> int:
    """Get the local rank of this worker (rank of the worker on its node).

    .. code-block:: python

        import time
        from ray import train

        def train_func():
            if torch.cuda.is_available():
                torch.cuda.set_device(train.local_rank())
            ...

        trainer = Trainer(backend="torch", use_gpu=True)
        trainer.start()
        trainer.run(train_func)
        trainer.shutdown()

    """
    session = get_session()
    return session.local_rank


@PublicAPI(stability="beta")
def load_checkpoint() -> Optional[Dict]:
    """Loads checkpoint data onto the worker.

    .. code-block:: python

        from ray import train

        def train_func():
            checkpoint = train.load_checkpoint()
            for iter in range(checkpoint["epoch"], 5):
                print(iter)

        trainer = Trainer(backend="torch")
        trainer.start()
        trainer.run(train_func, checkpoint={"epoch": 3})
        # 3
        # 4
        trainer.shutdown()

    Args:
        **kwargs: Any key value pair to be checkpointed by Train.
    Returns:
        The most recently saved checkpoint if ``train.save_checkpoint()``
        has been called. Otherwise, the checkpoint that the session was
        originally initialized with. ``None`` if neither exist.
    """
    session = get_session()
    return session.loaded_checkpoint


@PublicAPI(stability="beta")
def save_checkpoint(**kwargs) -> None:
    """Checkpoints all keyword arguments to Train as restorable state.

    .. code-block:: python

        import time
        from ray import train

        def train_func():
            for iter in range(100):
                time.sleep(1)
                train.save_checkpoint(epoch=iter)

        trainer = Trainer(backend="torch")
        trainer.start()
        trainer.run(train_func)
        trainer.shutdown()

    Args:
        **kwargs: Any key value pair to be checkpointed by Train.
    """
    session = get_session()
    session.checkpoint(**kwargs)


@PublicAPI(stability="beta")
def world_size() -> int:
    """Get the current world size (i.e. total number of workers) for this run.

    .. code-block:: python

        import time
        from ray import train

        def train_func():
            assert train.world_size() == 4

        trainer = Trainer(backend="torch", num_workers=4)
        trainer.start()
        trainer.run(train_func)
        trainer.shutdown()
    """
    session = get_session()
    return session.world_size
