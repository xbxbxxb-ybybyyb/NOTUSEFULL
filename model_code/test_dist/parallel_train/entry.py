try:
    import ray
    from ray import logger
    from ray.exceptions import RayActorError, RayTaskError
    from ray.actor import ActorHandle
    from ray.util import placement_group
    from ray.util.placement_group import PlacementGroup, \
        remove_placement_group, get_current_placement_group
    from distutils.version import LooseVersion
    RAY_INSTALLED = True
except ImportError:
    raise Exception("RAY_NOT_INSTALLED")

from typing import Tuple, Dict, Any, List, Optional
import os
import copy
import time
import warnings
import pandas as pd
import traceback
import itertools
import xgboost as xgb
from parallel_train.supervisor import Event, Queue, _TrainingState, PrepareActorTask
from parallel_train.api import RayParams, SplitTaskParam, _validate_ray_params
from parallel_train.helper import auto_connect_ray, RayXGBoostActorAvailable, RayActorTrainingError
from parallel_train.elastic import _create_actor, _maybe_schedule_new_actors, _update_scheduled_actor_states, _get_actor_alive_status
from parallel_train.trainer.BaseActor import BaseActor
from parallel_train import get_module_actor

# Status report frequency when waiting for initial actors and during training
STATUS_FREQUENCY_S = 30

def _create_communication_processes(ray_params:RayParams, added_tune_callback: bool = False):
    # from tune import TUNE_USING_PGFalse
    # TODO: tune
    TUNE_USING_PG = False
    # Create Queue and Event actors and make sure to colocate with driver node.
    # from ray.util import get_node_ip_address
    node_ip = ray.worker._global_node.node_ip_address#get_node_ip_address()
    # Have to explicitly set num_cpus to 0.
    placement_option = {"num_cpus": 0}
    if added_tune_callback and TUNE_USING_PG:
        # If Tune is using placement groups, then we force Queue and
        # StopEvent onto same bundle as the Trainable.
        # This forces all 3 to be on the same node.
        current_pg = get_current_placement_group()
        if current_pg is None:
            # This means the user is not using Tune PGs after all -
            # e.g. via setting an environment variable.
            placement_option.update({"resources": {f"node:{node_ip}": 0.01}})
        else:
            placement_option.update({
                "placement_group": current_pg,
                "placement_group_bundle_index": 0
            })
    else:
        placement_option.update({"resources": {f"node:{node_ip}": 0.01}})
    queue = Queue(actor_options=placement_option)  # Queue actor
    stop_event = Event(actor_options=placement_option)  # Stop event actor
    return queue, stop_event


def _create_placement_group(cpus_per_actor, gpus_per_actor,
                            resources_per_actor, num_actors, strategy):
    resources_per_bundle = {"CPU": cpus_per_actor, "GPU": gpus_per_actor}
    extra_resources_per_bundle = {} if resources_per_actor is None else \
        resources_per_actor
    # Create placement group for training worker colocation.
    bundles = [{
        **resources_per_bundle,
        **extra_resources_per_bundle
    } for _ in range(num_actors)]
    pg = placement_group(bundles, strategy=strategy)
    # Wait for placement group to get created.
    logger.debug("Waiting for placement group to start.")
    ready, _ = ray.wait([pg.ready()], timeout=100)
    if ready:
        logger.info(f"Placement group创建成功. 策略为placement_strategy: {strategy}")
    else:
        raise TimeoutError("Placement group creation timed out. Make sure "
                           "your cluster either has enough resources or use "
                           "an autoscaling cluster. Current resources "
                           "available: {}, resources requested by the "
                           "placement group: {}".format(
                               ray.available_resources(), pg.bundle_specs))
    return pg


def _shutdown(actors: List[ActorHandle],
              pending_actors: Optional[Dict[int, Tuple[
                  ActorHandle, PrepareActorTask]]] = None,
              queue: Optional[Queue] = None,
              event: Optional[Event] = None,
              placement_group: Optional[PlacementGroup] = None,
              force: bool = False):
    alive_actors = [a for a in actors if a is not None]
    if pending_actors:
        alive_actors += [a for (a, _) in pending_actors.values()]

    if force:
        for actor in alive_actors:
            ray.kill(actor)
    else:
        done_refs = [a.__ray_terminate__.remote() for a in alive_actors]
        # Wait 5 seconds for actors to die gracefully.
        done, not_done = ray.wait(done_refs, timeout=5)
        if not_done:
            # If all actors are not able to die gracefully, then kill them.
            for actor in alive_actors:
                ray.kill(actor)
    for i in range(len(actors)):
        actors[i] = None
    if queue:
        queue.shutdown()
    if event:
        event.shutdown()
    if placement_group:
        remove_placement_group(placement_group)


def split_task_by_data_param(data_params: Dict[str, Any], num_actors: int, is_mode_actor = True):
    """
    根据data_params切分任务
    :param data_params:
    :return:
    """
    total_task_nums = 0
    single_task_key = []
    share_params = {}
    single_task_params = {}
    for key, value in data_params.items():
        if isinstance(value, SplitTaskParam):
            single_task_params[key] = value.value
            single_task_key.append(key)
        else:
            share_params[key] = value

    if single_task_params:
        total_tasks = []
        for task in itertools.product(*single_task_params.values()):
            total_tasks.append(task)
        total_task_nums = len(total_tasks)

    if total_task_nums < num_actors:
        warnings.warn(f"并发度闲置告警：切分的并行任务数{total_task_nums}小于当前设置并发度{num_actors}！请调小并发度，或者通过SplitTaskParam设置更多任务！")
    elif total_task_nums > num_actors:
        if is_mode_actor:
            raise Exception(f"并发度不够告警：当前Actor计算模式下，任务与Actor一对一绑定运行，请保证任务数{total_task_nums}和并发度{num_actors}一致！")

    data_params_groups = []
    if len(single_task_key) == 0:
        warnings.warn(f"任务data_params一致告警：未通过SplitTaskParam设置并行任务参数，每个任务的data_params一致可能导致重复任务运行！")
        # 若没有并行参数，则返回
        for i in range(num_actors):
            data_params_groups.append(data_params)

    for value in total_tasks:
        #按并行参数切分出任务
        params = copy.copy(share_params)
        for idx, sub_v in enumerate(value):
            params[single_task_key[idx]] = sub_v
        logger.debug("split_task_by_data_param: 切分的单个任务参数为{}。".format(params))
        data_params_groups.append(params)
    return data_params_groups



def _train_by_actor(backend_actor: str,
           data_params: Dict,
           model_params: Dict,
           ray_params: RayParams,
           cpus_per_actor: int,
           gpus_per_actor: int,
           _training_state: _TrainingState,
           ) -> Tuple[xgb.Booster, Dict, Dict]:
    """
    通过Ray的Actor并行，任务数和并行度一致，每个Actor负责一个任务。
    This is the local train function wrapped by :func:`train() <train>`.

    This function can be thought of one invocation of a multi-actor xgboost
    training run. It starts the required number of actors, triggers data
    loading, collects the results, and handles (i.e. registers) actor failures
    - but it does not handle fault tolerance or general training setup.

    Generally, this function is called one or multiple times by the
    :func:`train() <train>` function. It is called exactly once if no
    errors occur. It is called more than once if errors occurred (e.g. an
    actor died) and failure handling is enabled.
    """
    # Un-schedule possible scheduled restarts
    _training_state.restart_training_at = None

    # This is a callback that handles actor failures.
    # We identify the rank of the failed actor, add this to a set of
    # failed actors (which we might want to restart later), and set its
    # entry in the actor list to None.
    def handle_actor_failure(actor_id):
        rank = _training_state.actors.index(actor_id)
        _training_state.failed_actor_ranks.add(rank)
        _training_state.actors[rank] = None

    try:
        local_actor = get_module_actor(backend_actor)
        assert issubclass(local_actor, BaseActor), "backend_actor应该继承自base_actor基类！"
        assert hasattr(local_actor, "train"), "backend_actor应该继承自base_actor基类, 并实现train方法！"
        remote_actor = ray.remote(local_actor)
    except:
        print(traceback.print_exc())
        raise Exception(f"backend_actor {local_actor}注册成远程类失败：请确认backend_actor继承自base_actor基类, 并重载相应方法！")

    data_params_groups = split_task_by_data_param(data_params, ray_params.num_actors, is_mode_actor=True)
    # Here we create new actors. In the first invocation of _train(), this
    # will be all actors. In future invocations, this may be less than
    # the num_actors setting, depending on the failure mode.
    newly_created = 0
    for i in list(_training_state.failed_actor_ranks):
        if i >= len(data_params_groups):
            #并发数大于任务数，不用启动Actor
            continue
        if _training_state.actors[i] is not None:
            raise RuntimeError(
                f"Trying to create actor with rank {i}, but it already "
                f"exists.")
        #TODO; 增加对distributed_callbacks的支持
        actor = _create_actor(
            remote_actor = remote_actor,
            num_cpus_per_actor=cpus_per_actor,
            num_gpus_per_actor=gpus_per_actor,
            resources_per_actor=ray_params.resources_per_actor,
            placement_group=_training_state.placement_group,
           )
        # Set actor entry in our list
        _training_state.actors[i] = actor
        # Remove from this set so it is not created again
        _training_state.failed_actor_ranks.remove(i)
        newly_created += 1

    alive_actors = sum(1 for a in _training_state.actors if a is not None)
    logger.info(f"[paralleltrain] Created {newly_created} new actors "
                f"({alive_actors} total actors). Waiting until actors "
                f"are ready for training.")

    prepare_actor_tasks = [
        PrepareActorTask(
            rank,
            actor,
            # Maybe we got a new Queue actor, so send it to all actors.
            queue=_training_state.queue,
            # Maybe we got a new Event actor, so send it to all actors.
            stop_event=_training_state.stop_event,
            check_point=_training_state.checkpoint,
            ray_params = ray_params,
            data_params = data_params_groups[rank]
            ) for rank, actor in enumerate(_training_state.actors)
        if actor is not None
    ]

    start_wait = time.time()
    last_status = start_wait
    try:
        # Construct list before calling any() to force evaluation
        ready_states = [task.is_ready() for task in prepare_actor_tasks]
        logger.debug("ready_states:", ready_states)
        while not all(ready_states):
            #每隔一段时间报告actors的执行情况
            if time.time() >= last_status + STATUS_FREQUENCY_S:
                wait_time = time.time() - start_wait
                logger.info(f"Acotr初始化及数据准备中，已累计耗时({wait_time:.0f} s.")
                last_status = time.time()
            time.sleep(0.1)
            ready_states = [task.is_ready() for task in prepare_actor_tasks]

    except Exception as exc:
        _training_state.stop_event.set()
        _get_actor_alive_status(_training_state.actors, handle_actor_failure)
        raise RayActorError from exc

    logger.info("Actor已全部就绪, 准备开始模型训练...")

    # The callback_returns dict contains actor-rank indexed lists of
    # results obtained through the `put_queue` function, usually
    # sent via callbacks.
    callback_returns = _training_state.additional_results.get("callback_returns")
    if callback_returns is None:
        callback_returns = [list() for _ in range(len(_training_state.actors))]
        _training_state.additional_results["callback_returns"] = callback_returns

    _training_state.training_started_at = time.time()

    # Trigger the train function
    live_actors = [
        actor for actor in _training_state.actors if actor is not None
    ]
    training_futures = [
        actor.train.remote(
            model_params.copy(),
            ) for i, actor in enumerate(live_actors)
    ]

    # Failure handling loop. Here we wait until all training tasks finished.
    # If a training task fails, we stop training on the remaining actors,
    # check which ones are still alive, and raise the error.
    # The train() wrapper function will then handle the error.
    start_wait = time.time()
    last_status = start_wait
    try:
        not_ready = training_futures
        while not_ready:
            if _training_state.queue:
                _training_state._handle_queue(
                    queue=_training_state.queue,
                    checkpoint=_training_state.checkpoint,
                    callback_returns=callback_returns)

            if ray_params.elastic_training:
                _maybe_schedule_new_actors(
                    remote_actor = remote_actor,
                    data_params = data_params_groups,
                    training_state=_training_state,
                    num_cpus_per_actor=cpus_per_actor,
                    num_gpus_per_actor=gpus_per_actor,
                    resources_per_actor=ray_params.resources_per_actor,
                    ray_params=ray_params)

                # This may raise RayXGBoostActorAvailable
                _update_scheduled_actor_states(_training_state)

            if time.time() >= last_status + STATUS_FREQUENCY_S:
                wait_time = time.time() - start_wait
                logger.info(f"Actor训练进行中，已累计训练 ({wait_time:.0f} s.")
                last_status = time.time()

            ready, not_ready = ray.wait(
                not_ready, num_returns=len(not_ready), timeout=1)
            ray.get(ready)

        # Get items from queue one last time
        if _training_state.queue:
            _training_state._handle_queue(
                queue=_training_state.queue,
                checkpoint=_training_state.checkpoint,
                callback_returns=callback_returns)

    # The inner loop should catch all exceptions
    except Exception as exc:
        logger.debug(f"Caught exception in training loop: {exc}")

        # Stop all other actors from training
        _training_state.stop_event.set()

        # Check which actors are still alive
        _get_actor_alive_status(_training_state.actors, handle_actor_failure)

        # Todo(官方TODO): Try to fetch newer checkpoint, store in `_checkpoint`
        raise RayActorError from exc

    # Training is now complete.

    # Get all results from all actors.
    ray.get(training_futures)

    # All results should be the same because of Rabit tracking. But only
    # the first one actually returns its bst object.

    if callback_returns:
        _training_state.additional_results[
            "callback_returns"] = callback_returns
        _training_state.additional_results.pop("callback_returns")

    return _training_state.additional_results


@ray.remote(max_retries=0)
def train_func(local_actor, rank_id, ray_params, data_params, model_params, _training_state):
    actor = local_actor()
    PrepareActorTask(
        rank_id,
        actor,
        # Maybe we got a new Queue actor, so send it to all actors.
        queue=_training_state.queue,
        stop_event=None,
        check_point= None,
        ray_params = ray_params,
        data_params = data_params,
        remote_mode = False
        )
    actor.train(model_params)
    return

def _train_by_task(backend_actor: str,
           data_params: Dict,
           model_params: Dict,
           ray_params: RayParams,
           cpus_per_actor: int,
           gpus_per_actor: int,
           _training_state: _TrainingState,
           ) -> Tuple[xgb.Booster, Dict, Dict]:
    """
    通过Ray的Task并行，允许任务数大于并行度，所有任务排队运行。
    """
    _training_state.restart_training_at = None

    try:
        local_actor = get_module_actor(backend_actor)
        assert issubclass(local_actor, BaseActor), "backend_actor应该继承自base_actor基类！"
        assert hasattr(local_actor, "train"), "backend_actor应该继承自base_actor基类, 并实现train方法！"
    except:
        print(traceback.print_exc())
        raise Exception(f"backend_actor {local_actor}加载失败：请确认backend_actor继承自base_actor基类, 并重载相应方法！")


    _training_state.training_started_at = time.time()
    # Trigger the train function
    training_futures = [
        train_func.options(
            num_cpus = ray_params.cpus_per_actor,
            num_gpus = ray_params.gpus_per_actor,
            resources = ray_params.resources_per_actor,
            placement_group_capture_child_tasks = True,
            placement_group = _training_state.placement_group).remote(
                local_actor,
                rank_id,
                ray_params,
                single_task_param,
                model_params,
                _training_state,
            ) for rank_id, single_task_param in enumerate(split_task_by_data_param(data_params, ray_params.num_actors, is_mode_actor=False))
    ]

    # Failure handling loop. Here we wait until all training tasks finished.
    start_wait = time.time()
    last_status = start_wait
    try:
        ray.get(training_futures[0])
        not_ready = training_futures[1:]
        while not_ready:
            if _training_state.queue:
                _training_state._handle_queue(
                    queue=_training_state.queue,
                    checkpoint=_training_state.checkpoint,
                    callback_returns=None)

            if time.time() >= last_status + STATUS_FREQUENCY_S:
                wait_time = time.time() - start_wait
                logger.info(f"Actor训练进行中，已累计训练 ({wait_time:.0f} s.")
                last_status = time.time()

            ready, not_ready = ray.wait(
                not_ready, num_returns=len(not_ready), timeout=1)
            ray.get(ready)

        # Get items from queue one last time
        if _training_state.queue:
            _training_state._handle_queue(
                queue=_training_state.queue,
                checkpoint=_training_state.checkpoint,
                callback_returns=None)

    # The inner loop should catch all exceptions
    except Exception as exc:
        logger.debug(f"Caught exception in training loop: {exc}")
        # Todo(官方TODO): Try to fetch newer checkpoint, store in `_checkpoint`
        raise RayActorError from exc

    return _training_state.additional_results


def train(backend_actor, data_params:Optional[Dict[str, Any]], model_params:Optional[Dict[str, Any]], ray_params: RayParams = None, parallel_mode = "TASK"):
    """
    :param backend_actor:
    :param data_params:
    :param model_params:
    :param ray_params:
    :param parallel_mode: TASK执行_train_by_task，ACTOR执行_train_by_actor(容错能力)
    :return:
    """
    ##% 参数
    if ray_params == None:
        ray_params = RayParams()

    start_time = time.time()
    ray_params = _validate_ray_params(ray_params)

    # TODO: 此处可添加_try_add_tune_callback
    train_evals_result = {}
    train_additional_results = {}

    tries = 0
    current_results = {}  # Keep track of additional results
    actors = [None] * ray_params.num_actors  # All active actors
    pending_actors = {}

    # Create the Queue and Event actors.
    queue, stop_event = _create_communication_processes(ray_params)

    # All provided bundles are packed onto a single node on a best-effort basis. If strict packing is not feasible (i.e., some bundles do not fit on the node), bundles can be placed onto other nodes nodes.
    placement_strategy = ray_params.placement_strategy
    if placement_strategy:
        # shen，设置资源组后，资源名为
        pg = _create_placement_group(ray_params.cpus_per_actor, ray_params.gpus_per_actor,
                                     ray_params.resources_per_actor,
                                     ray_params.num_actors, placement_strategy)
    else:
        pg = None

    #确认入口运行函数
    if backend_actor[:4].upper() == "DIST" or parallel_mode=="ACTOR":
        TRAIN_ENTRY_FUNC = _train_by_actor
    else:
        TRAIN_ENTRY_FUNC = _train_by_task

    start_actor_ranks = set(range(ray_params.num_actors))  # Start these
    total_training_time = 0.
    while tries <= ray_params.max_actor_restarts:
        # Only update number of iterations if the checkpoint changed
        # If it didn't change, we already subtracted the iterations.
        training_state = _TrainingState(
            actors=actors,
            queue=queue,
            stop_event=stop_event,
            checkpoint={},
            additional_results=current_results,
            training_started_at=0.,
            placement_group=pg,
            failed_actor_ranks=start_actor_ranks,
            pending_actors=pending_actors)


        try:
            train_additional_results = TRAIN_ENTRY_FUNC(
                backend_actor,
                data_params,
                model_params,
                ray_params=ray_params,
                cpus_per_actor=ray_params.cpus_per_actor,
                gpus_per_actor=ray_params.gpus_per_actor,
                _training_state=training_state,
                )
            if training_state.training_started_at > 0.:
                total_training_time += time.time(
                ) - training_state.training_started_at
            break
        except (RayActorError, RayTaskError) as exc:
            if training_state.training_started_at > 0.:
                total_training_time += time.time(
                ) - training_state.training_started_at
            alive_actors = sum(1 for a in actors if a is not None)
            start_again = False
            if ray_params.elastic_training:
                if alive_actors < ray_params.num_actors - \
                        ray_params.max_failed_actors:
                    raise RuntimeError(
                        "A Ray actor died during training and the maximum "
                        "number of dead actors in elastic training was "
                        "reached. Shutting down training.") from exc

                # Do not start new actors before resuming training
                # (this might still restart actors during training)
                start_actor_ranks.clear()

                if exc.__cause__ and isinstance(exc.__cause__,
                                                RayXGBoostActorAvailable):
                    # New actor available, integrate into training loop
                    logger.info(
                        f"A new actor became available. Re-starting training "
                        f"from latest checkpoint with new actor. "
                        f"This will use {alive_actors} existing actors and "
                        f"start {len(start_actor_ranks)} new actors. "
                        f"Sleeping for 10 seconds for cleanup.")
                    tries -= 1  # This is deliberate so shouldn't count
                    start_again = True

                elif tries + 1 <= ray_params.max_actor_restarts:
                    if exc.__cause__ and isinstance(exc.__cause__,
                                                    RayActorTrainingError):
                        logger.warning(f"Caught exception: {exc.__cause__}")
                    logger.warning(
                        f"A Ray actor died during training. Trying to "
                        f"continue training on the remaining actors. "
                        f"This will use {alive_actors} existing actors and "
                        f"start {len(start_actor_ranks)} new actors. "
                        f"Sleeping for 10 seconds for cleanup.")
                    start_again = True

            elif tries + 1 <= ray_params.max_actor_restarts:
                if exc.__cause__ and isinstance(exc.__cause__,
                                                RayActorTrainingError):
                    logger.warning(f"Caught exception: {exc.__cause__}")
                logger.warning(
                    f"A Ray actor died during training. Trying to restart "
                    f"and continue training from last checkpoint "
                    f"(restart {tries + 1} of {ray_params.max_actor_restarts}). "
                    f"This will use {alive_actors} existing actors and start "
                    f"{len(start_actor_ranks)} new actors. "
                    f"Sleeping for 10 seconds for cleanup.")
                start_again = True

            if start_again:
                time.sleep(5)
                queue.shutdown()
                stop_event.shutdown()
                time.sleep(5)
                queue, stop_event = _create_communication_processes(ray_params)
            else:
                raise RuntimeError(
                    f"A Ray actor died during training and the maximum number "
                    f"of retries ({ray_params.max_actor_restarts}) is exhausted."
                ) from exc
            tries += 1

    total_time = time.time() - start_time

    train_additional_results["training_time_s"] = total_training_time
    train_additional_results["total_time_s"] = total_time

    logger.info("[paralleltrain] Finished training on training data "
                "in {total_time_s:.2f} seconds "
                "({training_time_s:.2f} pure XGBoost training time).".format(
        **train_additional_results))

    _shutdown(
        actors=actors,
        pending_actors=pending_actors,
        queue=queue,
        event=stop_event,
        placement_group=pg,
        force=False)

    return train_additional_results


if __name__=="__main__":
    # XGBoostActor.train入参
    model_params = {"num_boost_round": 100, "params": {'tree_method': 'approx', 'objective': 'binary:logistic',
                                                       'eval_metric': ['logloss', 'error']}}
    # XGBoostActor.prepare_data入参,SplitTaskParam表示将任务切分成4块
    data_params = {
        "train": SplitTaskParam([[pd.read_pickle("data/features.pkl"), pd.read_pickle("data/label.pkl")],
                                 [pd.read_pickle("data/features.pkl"), pd.read_pickle("data/label.pkl")],
                                 [pd.read_pickle("data/features.pkl"), pd.read_pickle("data/label.pkl")],
                                 [pd.read_pickle("data/features.pkl"), pd.read_pickle("data/label.pkl")],
                                 [pd.read_pickle("data/features.pkl"), pd.read_pickle("data/label.pkl")],
                                 [pd.read_pickle("data/features.pkl"), pd.read_pickle("data/label.pkl")],
                                 [pd.read_pickle("data/features.pkl"), pd.read_pickle("data/label.pkl")],
                                 ]),
        "eval": ["data/features.pkl", "data/label.pkl"]}

    # 如果是普通任务，需指定计算单元配置，如果是分布式任务则无需指定。
    ray_params = RayParams(cpus_per_actor=1, gpus_per_actor=0, mems_per_actor=1024, num_actors=4)
    train_additional_results = train(backend_actor="XGBoostActor", data_params=data_params, model_params=model_params,
                                     ray_params=ray_params)
    print("train_additional_results:", train_additional_results)


