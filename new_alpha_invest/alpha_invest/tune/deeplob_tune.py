# load packages
import sys
sys.path.append("..")
sys.path.append("/data/user/013150")
import ray
from ray.tune.suggest.optuna import OptunaSearch
from ray import tune
import pandas as pd
import time

# device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
# print(device)

def parallel_train():
    from parallel_train.trainer import ParallelTrainer, SplitTaskParam, RayParams
    from alpha_invest.trainingpack.deeplob_pack import DeepLOBPack
    # step2: 实例化Trainer，设置Trainer入参，已继承并实现的Backend类，任务类型，以及ray_params参数类型
    trainer = ParallelTrainer(backend=DeepLOBPack, task_mode='LocalTrain', ray_params=RayParams(cpus_per_worker=1,))

    data_params = {"window": SplitTaskParam([20, 30])}
    model_params = {'lr': 0.001,
                    'batch_size': 64,
                    'epochs': 1}

    # 并行训练开始
    t1 = time.time()
    return_iterator = trainer.parallel_run(model_params=model_params, data_params=data_params)

    # step4: 获取训练结果迭代器，并打印train方法中的返回值
    result_list = []
    for result in return_iterator:
        result_list.extend(result)
    print("LocalTrain模式汇总的训练结果为：")
    print(pd.DataFrame(result_list). time.time()-t1)

def dist_train():
    from parallel_train.trainer import ParallelTrainer, SplitTaskParam, RayParams
    from alpha_invest.trainingpack.dist_deeplob_pack import DistDeepLOBPack
    # step2: 实例化Trainer，设置Trainer入参，已继承并实现的Backend类，任务类型，以及ray_params参数类型
    trainer = ParallelTrainer(backend = DistDeepLOBPack, task_mode = 'DistTrain', ray_params = RayParams(cpus_per_worker=1,))


    # step3: 设置运行参数
    data_params = {"window": SplitTaskParam([20, 30])}
    model_params = {'lr': 0.001,
                    'batch_size': 64,
                    'epochs': 1}
    # 并行训练开始
    return_iterator = trainer.parallel_run(model_params=model_params, data_params=data_params)

    # step4: 获取训练结果迭代器，并打印train方法中的返回值
    result_list = []
    for result in return_iterator:
        result_list.extend(result)
    print("DistTrain模式汇总的训练结果为：")
    print(pd.DataFrame(result_list))


def parallel_tune():
    def objective(params):
        data_params = {"window": params.pop("window"), "mock_data_flag": False,
                       "tag_name": params.pop("tag_name"), "num_features": params.pop("num_features")}
        model_params = params
        from alpha_invest.trainingpack import deeplob_pack
        deeplob_pack.DeepLOBPack.run_single_instance(data_params=data_params, model_params=model_params)

    # Optuna suggest params
    config = {
        "num_features": tune.choice([10]),
        "tag_name": tune.choice(['tag2minShort', 'tag2minShort', 'tag1minShort', 'tag5minLong', 'tag2minLong', 'tag1minLong']), #tune.choice(["Tag1minRet", "Tag2minRet", "Tag5minRet"]),
        'lr': tune.uniform(0.0001, 0.005),
        'window': tune.choice([20, 30, 50,100]),
        'batch_size': tune.choice([64, 128]),#, 128, 256
        'epochs': 1,
    }
    optuna_search = OptunaSearch(metric='test_losses', mode='max')
    tune.run(objective, config=config, search_alg=optuna_search, num_samples=50,
             resources_per_trial={'gpu': 0}, name='DeepLOB_T0_1',  local_dir = '/data/user/quanttest007/alpha_invest/ray_results')


if __name__=="__main__":
    #Torch 1.9版本以上
    if False:
        from xquant.compute.ray_cluster import start_ray_cluster, recycle_ray_cluster
        # try:
        #     recycle_ray_cluster()
        # except:
        #     pass
        # time.sleep(60)
        #启动分布式ray集群
        redis_address = start_ray_cluster(cpus_per_node=2, gpus_per_node=1, mem_per_node=24, maxWorkers=8, minWorkers=8,
                                          image="168.61.124.82/000322/xquant/jupyter_hadoop26_spark22:research_uat_v3.0",
                                          startup_command="pip uninstall -y parallel_train && pip install /data/user/quanttest007/alpha_invest/torch-1.9.0+cu111-cp36-cp36m-linux_x86_64.whl && sh /data/user/quanttest007/alpha_invest/alpha_invest/install.sh")
        print("redis_address:", redis_address)
        ray.init(address=redis_address,
                 runtime_env={"env_vars": {"PYTHONPATH": "/data/user/quanttest007/alpha_invest:$PYTHONPATH"}})
        print("redis_address:", redis_address)
        print("=====")
        # ray.init(address = redis_address, runtime_env = {"env_vars": {"PYTHONPATH": "/data/user/quanttest007/alpha_invest:$PYTHONPATH" }})
        print(ray.is_initialized())
    else:
        ray.init(num_cpus = 1)

    parallel_tune()
    # parallel_train()
    # dist_train()


