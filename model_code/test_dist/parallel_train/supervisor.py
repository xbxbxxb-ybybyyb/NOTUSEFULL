from typing import Tuple, Dict, Any, List, Optional, Callable, Union, Sequence, DefaultDict
from dataclasses import dataclass, field
import asyncio
from collections import defaultdict
import warnings
import queue
from parallel_train.helper import _ray_get_cluster_resource, _get_min_node_cpus, _is_local_mode
from parallel_train.api import RayParams

import ray
from ray.util.queue import Queue as RayQueue, Empty, Full
from ray.actor import ActorHandle
from ray.util.placement_group import PlacementGroup
RAY_INSTALLED = True




@dataclass
class _Checkpoint:
    iteration: int = 0
    value: Optional[bytes] = None


class _EventActor:
    def __init__(self, is_local_mode = False):
        if not is_local_mode:
            self._event = asyncio.Event()
        else:
            self._event = None

    def set(self):
        self._event.set()

    def clear(self):
        self._event.clear()

    def is_set(self):
        return self._event.is_set()


class Event:
    def __init__(self, actor_options: Optional[Dict] = None):
        actor_options = {} if not actor_options else actor_options
        self.actor = ray.remote(_EventActor).options(**actor_options).remote(_is_local_mode())

    def set(self):
        self.actor.set.remote()

    def clear(self):
        self.actor.clear.remote()

    def is_set(self):
        return ray.get(self.actor.is_set.remote())

    def shutdown(self):
        if self.actor:
            ray.kill(self.actor)
        self.actor = None


# Have to copy the class here so that we can subclass this for mocking.
# If we have the @ray.remote decorator, then we can't subclass it.
class _AsycQueueActor:
    def __init__(self, maxsize):
        self.maxsize = maxsize
        self.queue = asyncio.Queue(self.maxsize)

    def qsize(self):
        return self.queue.qsize()

    def empty(self):
        return self.queue.empty()

    def full(self):
        return self.queue.full()

    async def put(self, item, timeout=None):
        try:
            await asyncio.wait_for(self.queue.put(item), timeout)
        except asyncio.TimeoutError:
            raise Full

    async def get(self, timeout=None):
        try:
            return await asyncio.wait_for(self.queue.get(), timeout)
        except asyncio.TimeoutError:
            raise Empty

    def put_nowait(self, item):
        #如果有空槽，立即插入，如果没有槽位，引发QueueFull异常，区别于put方法等待槽位为空
        self.queue.put_nowait(item)

    def put_nowait_batch(self, items):
        # If maxsize is 0, queue is unbounded, so no need to check size.
        if self.maxsize > 0 and len(items) + self.qsize() > self.maxsize:
            raise Full(f"Cannot add {len(items)} items to queue of size "
                       f"{self.qsize()} and maxsize {self.maxsize}.")
        for item in items:
            self.queue.put_nowait(item)

    def get_nowait(self):
        #如果队列内有值立即返回队列中的一个元素，否则引发一场QueueEmpty
        return self.queue.get_nowait()


    def get_nowait_batch(self, num_items):
        if num_items > self.qsize():
            raise Empty(f"Cannot get {num_items} items from queue of size "
                        f"{self.qsize()}.")
        return [self.queue.get_nowait() for _ in range(num_items)]


class _QueueActor:
    def __init__(self, maxsize):
        self.maxsize = maxsize
        self.queue = queue.Queue(self.maxsize)

    def qsize(self):
        return self.queue.qsize()

    def empty(self):
        return self.queue.empty()

    def full(self):
        return self.queue.full()

    def put(self, item, timeout=None):
        try:
            return self.queue.put(item, timeout)
        except queue.Full:
            raise Full

    def get(self, timeout=None):
        try:
            return self.queue.get(timeout=timeout)
        except:
            raise Empty

    def put_nowait(self, item):
        self.queue.put(item, timeout=0.5)

    def put_nowait_batch(self, items):
        # If maxsize is 0, queue is unbounded, so no need to check size.
        if self.maxsize > 0 and len(items) + self.qsize() > self.maxsize:
            raise Full(f"Cannot add {len(items)} items to queue of size "
                       f"{self.qsize()} and maxsize {self.maxsize}.")
        for item in items:
            self.queue.put(item, timeout=0.5)

    def get_nowait(self):
        return self.queue.get(timeout=0.5)

    def get_nowait_batch(self, num_items):
        if num_items > self.qsize():
            raise Empty(f"Cannot get {num_items} items from queue of size "
                        f"{self.qsize()}.")
        return [self.queue.get(timeout=0.5) for _ in range(num_items)]



# Remove after Ray 1.2 release.
class Queue(RayQueue):
    def __init__(self, maxsize: int = 0,
                 actor_options: Optional[Dict] = None) -> None:
        actor_options = actor_options or {}
        self.maxsize = maxsize
        if _is_local_mode():
            self.actor = ray.remote(_QueueActor).options(**actor_options).remote(
                self.maxsize)
        else:
            self.actor = ray.remote(_AsycQueueActor).options(**actor_options).remote(
                self.maxsize)


    def shutdown(self):
        if getattr(RayQueue, "shutdown", None) is not None:
            super(Queue, self).shutdown()
        else:
            if self.actor:
                ray.kill(self.actor)
            self.actor = None


class PrepareActorTask:
    """Utility class to hold multiple futures.

    The `is_ready()` method will return True once all futures are ready.

    Args:
        pending_futures (list): List of object references (futures)
            that should be tracked.
    """

    def __init__(self, rank: int, actor: ActorHandle, queue: Queue, stop_event: Event,
                 check_point: _Checkpoint, data_params:Dict, ray_params: RayParams, remote_mode = True):
        if remote_mode:
            pending_futures = []
            pending_futures.append(actor.set_queue.remote(rank, queue))
            pending_futures.append(actor.set_stop_event.remote(stop_event))
            pending_futures.append(actor.set_checkpoint.remote(check_point))
            pending_futures.append(actor.set_ray_params.remote(ray_params))
            pending_futures.append(actor.prepare_data.remote(data_params))
            self._pending_futures = pending_futures or []
            self._ready_futures = []
        else:
            pending_futures = []
            pending_futures.append(actor.set_queue(rank, queue))
            pending_futures.append(actor.set_ray_params(ray_params))
            pending_futures.append(actor.prepare_data(data_params))


    def is_ready(self):
        # #ray.wait不会抛异常
        # if not self._pending_futures:
        #     return True
        # ready = True
        # while ready:
        #     ready, not_ready = ray.wait(self._pending_futures, timeout=0)
        #     if ready:
        #         for obj in ready:
        #             self._pending_futures.remove(obj)
        #             self._ready_futures.append(obj)
        #
        # return not bool(self._pending_futures)
        ray.get(self._pending_futures)
        return True



@dataclass
class _TrainingState:
    actors: List[Optional[ActorHandle]]
    queue: Queue
    stop_event: Event
    checkpoint: Dict[int, _Checkpoint]
    # additional_results包含的主要key为callback_returns,
    # The callback_returns dict contains actor-rank indexed lists of
    # results obtained through the `put_queue` function, usually
    # sent via callbacks.
    additional_results: DefaultDict[str, Dict]

    training_started_at: float = 0

    placement_group: Optional[PlacementGroup] = None

    failed_actor_ranks: set = field(default_factory=set)

    # Last time we checked resources to schedule new actors
    last_resource_check_at: float = 0
    #TODO： 在训练前，允许添加一些预处理任务
    pending_actors: Dict[int, Tuple[ActorHandle, PrepareActorTask]] = field(
        default_factory=dict)
    restart_training_at: Optional[float] = None

    def __post_init__(self):
        self.additional_results = defaultdict(dict)


    def _handle_queue(self, queue: Queue, checkpoint: _Checkpoint,
                      callback_returns: Dict):
        """Handle results obtained from workers through the remote Queue object.

        Remote actors supply these results via the
        ``session.put_queue()`` function. These can be:

        - Callables. These will be called immediately with no arguments.
        - ``_Checkpoint`` objects. These will update the latest checkpoint
          object on the driver.
        - Any other type. These will be appended to an actor rank-specific
          ``callback_returns`` dict that will be written to the
          ``additional_returns`` dict of the :func:`train() <train>` method.
        """
        while not queue.empty():
            (actor_rank, item_dict) = queue.get()
            for result_name, item in item_dict.items():
                if isinstance(item, Callable):
                    item()
                elif isinstance(item, _Checkpoint):
                    self.checkpoint[actor_rank] = item
                else:
                    self.additional_results[result_name][actor_rank] = item
                    # callback_returns[actor_rank].append(item)



def _autodetect_resources(ray_params: RayParams,
                          use_tree_method: bool = False) -> Tuple[int, int]:
    #use_tree_method：xgboost是否使用gpu训练
    gpus_per_actor = ray_params.gpus_per_actor
    cpus_per_actor = ray_params.cpus_per_actor

    # Automatically set gpus_per_actor if left at the default value
    if gpus_per_actor == -1:
        gpus_per_actor = 0
        if use_tree_method:
            gpus_per_actor = 1

    # Automatically set cpus_per_actor if left at the default value
    # Will be set to the number of cluster CPUs divided by the number of
    # actors, bounded by the minimum number of CPUs across actors nodes.
    if cpus_per_actor <= 0:
        cluster_cpus = _ray_get_cluster_resource() or 1
        cpus_per_actor = max(1,
            min(int(_get_min_node_cpus() or 1),
                int(cluster_cpus // ray_params.num_actors)))
    return cpus_per_actor, gpus_per_actor
