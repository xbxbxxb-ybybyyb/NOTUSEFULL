import time
from typing import Optional, Dict, List, Tuple, Callable, Sequence
from distutils.version import LooseVersion
import ray
from ray import logger
from ray.util.placement_group import PlacementGroup
from parallel_train.supervisor import _TrainingState, ActorHandle, PrepareActorTask
from parallel_train.helper import RayXGBoostActorAvailable
from parallel_train.api import RayParams
import traceback

# How often to check for new available resources
ELASTIC_RESTART_RESOURCE_CHECK_S: int = 30

# How long to wait before triggering a new start of the training loop
# when new actors become available
ELASTIC_RESTART_GRACE_PERIOD_S: int = 10


def _create_actor(
        remote_actor:ActorHandle,
        num_cpus_per_actor: int,
        num_gpus_per_actor: int,
        resources_per_actor: Optional[Dict] = None,
        placement_group: Optional[PlacementGroup] = None,
) -> ActorHandle:
    """
    1、创建placement_group后，资源如下：
        {
            0.000000 / 4.000000 CPU,
            176250720.068359 GiB / 176250720.068359 GiB memory,
            88125359.960938 GiB / 88125359.960938 GiB object_store_memory,
            0.980000 / 1.000000 node: 168.61 .73 .100,
            4000.000000 / 4000.000000 bundle_group_945cdd89d4a084b25fde51edad3c7f66,
            1000.000000 / 1000.000000 bundle_group_0_945cdd89d4a084b25fde51edad3c7f66,
            1000.000000 / 1000.000000 bundle_group_1_945cdd89d4a084b25fde51edad3c7f66,
            1000.000000 / 1000.000000 bundle_group_2_945cdd89d4a084b25fde51edad3c7f66,
            1000.000000 / 1000.000000 bundle_group_3_945cdd89d4a084b25fde51edad3c7f66,
            4.000000 / 4.000000 CPU_group_945cdd89d4a084b25fde51edad3c7f66,
            1.000000 / 1.000000 CPU_group_0_945cdd89d4a084b25fde51edad3c7f66,
            1.000000 / 1.000000 CPU_group_1_945cdd89d4a084b25fde51edad3c7f66
            1.000000 / 1.000000 CPU_group_2_945cdd89d4a084b25fde51edad3c7f66,
            1.000000 / 1.000000 CPU_group_3_945cdd89d4a084b25fde51edad3c7f66,
        }
    2、此处若指定placement_group为None，则会调度不成功，报没有一个节点满足调度条件。
    """
    # Send DEFAULT_PG here, which changed in Ray >= 1.5.0
    # If we send `None`, this will ignore the parent placement group and
    # lead to errors e.g. when used within Ray Tune
    if LooseVersion(ray.__version__) >= LooseVersion("1.5.0"):
        # https://github.com/ray-project/ray/pull/16437
        DEFAULT_PG = "default"
    else:
        DEFAULT_PG = None

    try:
        actor = remote_actor.options(
            num_cpus=num_cpus_per_actor,
            num_gpus=num_gpus_per_actor,
            resources=resources_per_actor,
            placement_group_capture_child_tasks=True,
            placement_group=placement_group).remote()
    except:
        print(traceback.print_exc())
        raise Exception(f"remote_actor 实例化失败: {remote_actor}！remote_actor不应有__init__参数")
    return actor


def _maybe_schedule_new_actors(
        remote_actor: ActorHandle,
        data_params_groups: List[Dict],
        training_state: _TrainingState, num_cpus_per_actor: int,
        num_gpus_per_actor: int, resources_per_actor: Optional[Dict],
        ray_params: RayParams) -> bool:
    """Schedule new actors for elastic training if resources are available.

    Potentially starts new actors and triggers data loading."""

    # This is only enabled for elastic training.
    if not ray_params.elastic_training:
        return False

    missing_actor_ranks = [
        rank for rank, actor in enumerate(training_state.actors)
        if actor is None and rank not in training_state.pending_actors
    ]

    # If all actors are alive, there is nothing to do.
    if not missing_actor_ranks:
        return False

    now = time.time()

    # Check periodically every n seconds.
    if now < training_state.last_resource_check_at + \
            ELASTIC_RESTART_RESOURCE_CHECK_S:
        return False

    training_state.last_resource_check_at = now

    new_pending_actors: Dict[int, Tuple[ActorHandle, PrepareActorTask]] = {}
    logger.info(f"{missing_actor_ranks} actors are failed, elastic re-scheduling  for training...")
    for rank in missing_actor_ranks:
        # Actor rank should not be already pending
        if rank in training_state.pending_actors \
                or rank in new_pending_actors:
            continue

        # Try to schedule this actor
        actor = _create_actor(
            remote_actor = remote_actor,
            num_cpus_per_actor=num_cpus_per_actor,
            num_gpus_per_actor=num_gpus_per_actor,
            resources_per_actor=resources_per_actor,
            placement_group=training_state.placement_group)

        task = PrepareActorTask(
            rank,
            actor,
            queue=training_state.queue,
            stop_event=training_state.stop_event,
            check_point=training_state.checkpoint,
            ray_params = ray_params,
            data_params = data_params_groups[rank]
        )

        new_pending_actors[rank] = (actor, task)
        logger.debug(f"Re-scheduled actor with rank {rank}. Waiting for "
                     f"placement and data loading before promoting it "
                     f"to training.")
    if new_pending_actors:
        training_state.pending_actors.update(new_pending_actors)
        logger.info(f"Re-scheduled {len(new_pending_actors)} actors for "
                    f"training. Once data loading finished, they will be "
                    f"integrated into training again.")
    return bool(new_pending_actors)


def _update_scheduled_actor_states(training_state: _TrainingState):
    """Update status of scheduled actors in elastic training.

    If actors finished their preparation tasks, promote them to
    proper training actors (set the `training_state.actors` entry).

    Also schedule a `RayXGBoostActorAvailable` exception so that training
    is restarted with the new actors.

    """
    now = time.time()
    actor_became_ready = False

    # Wrap in list so we can alter the `training_state.pending_actors` dict
    for rank in list(training_state.pending_actors.keys()):
        actor, task = training_state.pending_actors[rank]
        if task.is_ready():
            # Promote to proper actor
            training_state.actors[rank] = actor
            del training_state.pending_actors[rank]
            actor_became_ready = True

    if actor_became_ready:
        if not training_state.pending_actors:
            # No other actors are pending, so let's restart right away.
            training_state.restart_training_at = now - 1.

        # If an actor became ready but other actors are pending, we wait
        # for n seconds before restarting, as chances are that they become
        # ready as well (e.g. if a large node came up).
        grace_period = ELASTIC_RESTART_GRACE_PERIOD_S
        if training_state.restart_training_at is None:
            logger.debug(
                f"A RayXGBoostActor became ready for training. Waiting "
                f"{grace_period} seconds before triggering training restart.")
            training_state.restart_training_at = now + grace_period

    if training_state.restart_training_at is not None:
        if now > training_state.restart_training_at:
            training_state.restart_training_at = None
            raise RayXGBoostActorAvailable(
                "A new RayXGBoostActor became available for training. "
                "Triggering restart.")


def _get_actor_alive_status(actors: List[ActorHandle],
                            callback: Callable[[ActorHandle], None]):
    """Loop through all actors. Invoke a callback on dead actors. """
    obj_to_rank = {}

    alive = 0
    dead = 0

    for rank, actor in enumerate(actors):
        if actor is None:
            dead += 1
            continue
        obj = actor.pid.remote()
        obj_to_rank[obj] = rank

    not_ready = list(obj_to_rank.keys())
    while not_ready:
        ready, not_ready = ray.wait(not_ready, timeout=0)

        for obj in ready:
            try:
                pid = ray.get(obj)
                rank = obj_to_rank[obj]
                logger.debug(f"Actor {actors[rank]} with PID {pid} is alive.")
                alive += 1
            except Exception:
                rank = obj_to_rank[obj]
                logger.debug(f"Actor {actors[rank]} is _not_ alive.")
                dead += 1
                callback(actors[rank])
    logger.info(f"Actor status: {alive} alive, {dead} dead "
                f"({alive+dead} total)")

    return alive, dead
