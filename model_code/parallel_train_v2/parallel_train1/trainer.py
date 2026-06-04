from typing import Iterable
from .train.trainer import *
from .train.callbacks.logging import JsonConsoleCallback
from .backend import DistTrainBackend, LocalTrainBackend
from dataclasses import dataclass
from ray import logger
from .helper import get_total_ray_resources, auto_connect_ray, get_xqconfig, \
    _validate_ray_params, _validate_task_mode, split_task_by_data_param, get_backend_config, \
    _validate_backend_wrapper, TaskMode
import time
import ray

STATUS_FREQUENCY_S = 30


class SplitTaskParam:
    def __init__(self, value):
        # 用于切分任务
        if not isinstance(value, Iterable):
            raise Exception("SplitTaskParam的值必须为可迭代的对象！")
        self.value = value


@dataclass
class RayParams:
    """Parameters to configure Ray-specific behavior.
    Args:
        cpus_per_worker (int): Number of CPUs to be used per Ray actor.
        gpus_per_worker (int): Number of GPUs to be used per Ray actor. -1自动根据xgboost参数检验是否使用GPU.
        num_workers (int): Number of parallel Ray workers.
    """
    # Actor scheduling
    cpus_per_worker: int = -1
    gpus_per_worker: float = -1
    num_workers: int = -1

    def resources_per_worker(self):
        return {'CPU': self.cpus_per_worker, 'GPU': self.gpus_per_worker}

    def __post_init__(self):
        auto_connect_ray()
        total_resources = get_total_ray_resources()
        task_param = get_xqconfig()
        if task_param.get("cpus_per_worker") != -1:
            if self.num_workers == -1 and self.cpus_per_worker == -1 and self.gpus_per_worker == -1:
                logger.debug("未指定RayParams运行资源, 将使用分布式任务的运行参数...")
                num_workers = task_param.get("num_workers")
                self.cpus_per_worker = task_param.get("cpus_per_worker")
                self.gpus_per_worker = task_param.get("gpus_per_worker")
            else:
                # 使用RayParams定义的进程池资源
                num_workers = min(int(total_resources['CPU'] / self.cpus_per_worker),
                                  int(total_resources['GPU'] / self.gpus_per_worker))

        else:
            if self.gpus_per_worker > 0:
                num_workers = min(int(total_resources['CPU'] / self.cpus_per_worker),
                                  int(total_resources.get('GPU', 0) / self.gpus_per_worker))
            else:
                num_workers = int(total_resources['CPU'] / self.cpus_per_worker)
                self.gpus_per_worker = 0
        if num_workers != self.num_workers:
            self.num_workers = num_workers
            logger.warning(f"进程池最大并行度num_workers已自动赋值为{self.num_workers}，以保证资源合理利用！")

        assert type(self.cpus_per_worker) == int, "RayParams的cpus_per_worker参数类型必须为int！"
        assert type(self.gpus_per_worker) == float or type(
            self.gpus_per_worker) == int, "RayParams的gpus_per_worker参数类型必须为float！"
        assert type(self.num_workers) == int, "RayParams的num_workers参数类型必须为int！"

        assert self.cpus_per_worker > 0, "每个计算单元的cpu数cpus_per_worker必须大于0，当前值为{}！当前为普通任务，请为RayParams指定cpus_per_worker！".format(
            self.cpus_per_worker)
        assert self.gpus_per_worker >= 0, "每个计算单元的gpu数gpus_per_worker必须大于等于0，当前值为{}！当前为普通任务，请为RayParams指定gpus_per_worker！".format(
            self.gpus_per_worker)

        logger.info(
            f"Ray计算进程池的资源为: [CPU: {float(self.cpus_per_worker)} * {self.num_workers}, GPU: {float(self.gpus_per_worker)} * {self.num_workers}]。")


def init_task_session(world_rank, local_rank, world_size, checkpoint):
    from .session import init_session
    init_session(
        task_mode='LocalTrain',
        world_rank=world_rank,
        local_rank=local_rank,
        world_size=world_size,
        checkpoint=checkpoint
    )


def train_fun(config):
    backend = config['backend']()
    single_data_param = config['single_data_param']
    actor_mode = config['is_actor_mode']
    initialization_hook = config['initialization_hook']
    model_params = config['model_params']
    if not actor_mode:
        # localTrain任务backend实例添加task_id
        backend.task_id = ray.runtime_context.get_runtime_context().task_id.hex()
        if initialization_hook is not None:
            initialization_hook()
        init_task_session(config['world_rank'], config['local_rank'], config['world_size'], config['checkpoint'])
    backend.prepare_data(single_data_param)
    return backend.train(model_params)


class ParallelTrainer(Trainer):
    def __init__(
            self,
            backend: Union[str, DistTrainBackend, LocalTrainBackend],
            task_mode: [str],
            ray_params: Union[None, RayParams, dict],
            logdir: Optional[str] = None,
            max_retries: int = 3,
    ):
        """
        Args:
            backend: 指定定并行运行的训练类，可自定义实现各类算法的Backend。
            task_mode:
            ray_params:RayParams提供了进程池的配置参数
            logdir: 用于保存checkpoint
            max_retries: 分布式训练重试次数，-1表示无限次重试
        """
        self._initialization_hook = None
        self._task_mode = _validate_task_mode(task_mode)
        self._ray_params = _validate_ray_params(ray_params)
        _validate_backend_wrapper(backend, self._task_mode)
        self._backend_cfg = get_backend_config(backend)
        self._backend_train_cls = backend
        use_gpu = True if self._ray_params.gpus_per_worker > 0 else False
        super(ParallelTrainer, self).__init__(backend=self._backend_cfg,
                                              num_workers=self._ray_params.num_workers,
                                              use_gpu=use_gpu, logdir=logdir,
                                              resources_per_worker=self._ray_params.resources_per_worker(),
                                              max_retries=max_retries)

    def start(self, initialization_hook: Optional[Callable[[], None]] = None):
        self._initialization_hook = initialization_hook
        if self._task_mode == TaskMode.DistTrain:
            super(ParallelTrainer, self).start(initialization_hook)

    def shutdown(self):
        if self._task_mode == TaskMode.DistTrain:
            super(ParallelTrainer, self).shutdown()

    def parallel_run(self, data_params: Dict, model_params: Dict, callbacks: Optional[List[TrainingCallback]] = None,
                     checkpoint: Optional[Union[Dict, str, Path]] = None, ) -> List[T]:
        """

        Args:
            data_params:  指数据加载、存储的参数，Backend的prepare_data成员函数的唯一入参，可指定SplitTaskParam类型的参数用于切分任务；
            model_params: 指模型算法的训练参数，Backend的train成员函数的唯一入参；
            callbacks:
            checkpoint:

        Returns:
        """

        is_actor_mode = True if self._task_mode == TaskMode.DistTrain else False
        data_params_group = split_task_by_data_param(data_params=data_params,
                                                     num_actors=self._ray_params.num_workers,
                                                     is_mode_actor=is_actor_mode)

        if self._task_mode == TaskMode.DistTrain:

            # TODO(matt): Set default callbacks.
            callbacks = [JsonConsoleCallback()] if callbacks is None else callbacks
            finished_with_errors = False

            for callback in callbacks:
                callback.start_training(
                    logdir=str(self.latest_run_dir), config = {})
            for data_params in data_params_group:
                try:
                    iterator = self.run_iterator(train_func=train_fun,
                                   config={'backend': self._backend_train_cls,
                                           'single_data_param': data_params,
                                           'is_actor_mode': is_actor_mode,
                                           'initialization_hook': self._initialization_hook,
                                           'model_params': model_params
                                           },
                                   checkpoint=checkpoint)
                    for intermediate_result in iterator:
                        for callback in callbacks:
                            yield callback.process_results(intermediate_result)
                    assert iterator.is_finished()
                    # yield iterator.get_final_results()
                finally:
                    for callback in callbacks:
                        callback.finish_training(error=finished_with_errors)
                #重启并进入下一次分布式训练
                self.shutdown()
                super(ParallelTrainer, self).start(self._initialization_hook)
        elif self._task_mode == TaskMode.LocalTrain:
            remote_fun = ray.remote(max_calls=1, max_retries=0)(train_fun)
            training_futures = [
                remote_fun.options(num_cpus=self._ray_params.cpus_per_worker,
                                   num_gpus=self._ray_params.gpus_per_worker).remote(
                    config={'backend': self._backend_train_cls,
                            'single_data_param': data_params,
                            'is_actor_mode': False,
                            'initialization_hook': self._initialization_hook,
                            'model_params': model_params,
                            'world_rank': index,
                            'local_rank': index,
                            'world_size': len(data_params_group),
                            'checkpoint': checkpoint})
                for index, data_params in enumerate(data_params_group)]
            # Failure handling loop. Here we wait until all training tasks finished.
            start_wait = time.time()
            last_status = start_wait
            try:
                yield [ray.get(training_futures[0])]
                not_ready = training_futures[1:]
                while not_ready:
                    if time.time() >= last_status + STATUS_FREQUENCY_S:
                        wait_time = time.time() - start_wait
                        logger.info(f"Task训练进行中，已累计训练 ({wait_time:.0f} s.")
                        last_status = time.time()

                    ready, not_ready = ray.wait(not_ready, num_returns=len(not_ready), timeout=1)
                    yield ray.get(ready)
            except Exception as exc:
                logger.debug(f"Caught exception in training loop: {exc}")
                raise Exception
