from typing import Optional, Any
from ray.util.queue import Queue
import gc
import warnings


class RaySession:
    def __init__(self, rank: int, queue: Optional[Queue]):
        self._rank = rank
        # self._queue = queue

    def get_actor_rank(self):
        #在local_mode下不准确
        return self._rank

    def set_queue(self, queue):
        self._queue = queue

    def put_queue(self, item, rank_id):
        if self._queue is None:
            raise ValueError(
                "Trying to put something into session queue, but queue "
                "was not initialized. ")
        self._queue.put((rank_id, item))


_session = None


def init_session(*args, **kwargs):
    #Actor仍在原进程中重启，不需再init_session。
    global _session
    if _session:
        # raise ValueError(
        # warnings.warn(
        #     "Trying to initialize RaySession twice. FIX THIS by not calling `init_session()` manually.")
        return
    _session = RaySession(*args, **kwargs)


def get_session() -> RaySession:
    global _session
    if not _session or not isinstance(_session, RaySession):
        raise ValueError(
            "Trying to access RayXGBoostSession from outside an XGBoost run."
            "\nFIX THIS by calling function in `session.py` like "
            "`get_actor_rank()` only from within an XGBoost actor session.")
    return _session


def shutdown_session() -> RaySession:
    global _session
    if not _session or not isinstance(_session, RaySession):
        raise ValueError(
            "Trying to access RayXGBoostSession from outside an XGBoost run."
            "\nFIX THIS by calling function in `session.py` like "
            "`get_actor_rank()` only from within an XGBoost actor session.")
    _session = None
    gc.collect()


def set_session_queue(queue: Queue):
    session = get_session()
    session.set_queue(queue)


def get_actor_rank() -> int:
    session = get_session()
    return session.get_actor_rank()


def put_queue(item: Any, rank_id: int):
    session = get_session()
    session.put_queue(item, rank_id)
