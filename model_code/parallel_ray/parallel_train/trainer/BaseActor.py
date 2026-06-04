from typing import Tuple, Dict, Any, List, Optional, Callable, Union, Sequence
import os
from ray import logger

from parallel_train.supervisor import Event, Queue, _Checkpoint
from parallel_train.session import init_session, set_session_queue, put_queue
from parallel_train.api import RayParams, LocalRayParams



class BaseActor:
    """
        成员变量：
        rank_id: int, Actor的唯一标识, 从0开始计数（rank_id可作为data_params或者model_params的key，让各个Actor各自识别自己的参数）;
        data_params: Dict[Any, Any]: 指数据加载、存储的参数，RemoteActor的prepare_data成员函数的入参，可结合rank_id识别各个actor的数据；
        model_params: Dict[Any, Any]: 指模型算法的训练参数，RemoteActor的train成员函数的入参，可结合rank_id识别各个actor的训练参数；
        ray_params: RayParams, 指并行任务运行的配置参数，可获取RemoteActor的运行参数，如cpus_per_actor， gpus_per_actor， num_actors等，对应提交任务时的最小资源组和资源组个数; 后续支持容错、回调、超参数寻优等其他配置。
        成员方法：
        reset_rank_id(rank_id: int)：重置rank_id的方法，rank_id由框架自动分配，一般不需要手动指定，一些调试场景时可以指定rank_id来分配特定的任务。
        put_queue(item: Dict[str, [_Checkpoint, Any]): 用于传递结果到drive端。driver端定时（默认30s）获取queue中的结果，并填入train函数的返回值additional_results。key为additional_results中的key名。
    """
    ray_params = LocalRayParams(num_actors=1, cpus_per_actor=1, gpus_per_actor=0)

    def __init__(self):
        pass

    def _set_omp_num_threads(self, cpus_per_actor):
        """
         为Actor设置底层的并发度
        """
        os.environ["OMP_NUM_THREADS"] = str(int(cpus_per_actor))
        return int(float(os.environ.get("OMP_NUM_THREADS", "0.0")))

    def set_ray_params(self, ray_params: RayParams):
        """
        为Actor传递RayParams参数
        :param ray_params:
        :return:
        """
        self._cpus_per_actor = ray_params.cpus_per_actor
        self._gpus_per_actor = ray_params.gpus_per_actor
        #隔多少次迭代，设置checkpoint
        self._checkpoint_frequency = ray_params.checkpoint_frequency
        self._set_omp_num_threads(self._cpus_per_actor)
        self.ray_params = ray_params
        logger.debug(f"Initialized remote XGBoost actor with rank {self.rank_id}")


    def set_checkpoint(self, checkpoint: _Checkpoint):
        """
        为Actor传递checkpoint参数, 便于从异常恢复
        :param checkpoint:
        :return:
        """
        self._checkpoint = checkpoint

    def set_queue(self, rank:int, queue: Queue):
        """
         为Actor传递queue参数, 便于与Driver端通信
        :param queue:
        :return:
        """
        self.rank_id = rank
        self._queue = queue
        init_session(self.rank_id, self._queue)
        set_session_queue(self._queue)


    def set_stop_event(self, stop_event: Event):
        """
         为Actor传递全局事件, 暂无用
        :param stop_event:
        :return:
        """
        self._stop_event = stop_event

    def reset_rank_id(self, rank_id: int):
        #重置rank_id的方法，rank_id由框架自动分配，一般不需要指定，调试时可以指定rank_id外
        self.rank_id = rank_id

    def _get_stop_event(self):
        return self._stop_event

    def pid(self):
        """Get process PID. Used for checking if still alive"""
        return os.getpid()

    def ip(self):
        """Get node IP address."""
        from ray.util import get_node_ip_address
        return get_node_ip_address()

    def put_queue(self, item: Dict[str, Any]):
        put_queue(item, self.rank_id)

    # def _save_checkpoint_callback(self):
    #     """Send checkpoints to driver"""
    #     this = self
    #
    #     class _SaveInternalCheckpointCallback(TrainingCallback):
    #         def after_iteration(self, model, epoch, evals_log):
    #             if xgb.rabit.get_rank() == 0 and \
    #                     epoch % this.checkpoint_frequency == 0:
    #                 put_queue(_Checkpoint(epoch, pickle.dumps(model)))
    #
    #         def after_training(self, model):
    #             if xgb.rabit.get_rank() == 0:
    #                 put_queue(_Checkpoint(-1, pickle.dumps(model)))
    #             return model
    #
    #     return _SaveInternalCheckpointCallback()
    #
    # def _stop_callback(self):
    #     """Stop if event is set"""
    #     this = self
    #     # Keep track of initial stop event. Since we're training in a thread,
    #     # the stop event might be overwritten, which should he handled
    #     # as if the previous stop event was set.
    #     initial_stop_event = self._stop_event
    #
    #     class _StopCallback(TrainingCallback):
    #         def after_iteration(self, model, epoch, evals_log):
    #             try:
    #                 if this._stop_event.is_set() or \
    #                         this._get_stop_event() is not initial_stop_event:
    #                     if LEGACY_CALLBACK:
    #                         raise EarlyStopException(epoch)
    #                     # Returning True stops training
    #                     return True
    #             except RayActorError:
    #                 if LEGACY_CALLBACK:
    #                     raise EarlyStopException(epoch)
    #                 return True
    #
    #     return _StopCallback()

    def prepare_data(self, data_params:Dict) -> None:
        """
        （待实现的成员方法）用于train或者predict执行前的准备工作(如加载数据，加载模型等)，由并行训练框架内部调用。
        :param data_params: 数据参数，可结合rank_id识别各个actor的数据；
        :return: None，数据请赋值给成员变量后使用。
        """
        raise NotImplemented


    def train(self, model_params: Dict)  -> None:
        """
        （待实现的成员方法）模型训练函数，在Actor的准备步骤都完成后，开始执行，由并行训练框架内部调用。
        :param model_params:
        :return: None，训练结果返回值请通过put_queue函数传递到driver端的parallel_train.train的additional_results返回值。
        """
        raise NotImplemented

