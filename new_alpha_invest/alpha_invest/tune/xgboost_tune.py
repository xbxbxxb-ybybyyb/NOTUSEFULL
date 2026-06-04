import sys
sys.path.append("/tmp/pycharm_project_96/parallel_train")
sys.path.append("/tmp/pycharm_project_96")
import pandas as pd
# import torch
from ray import tune
import ray
import time

# device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
# print(device)
def parallel_train():
    from parallel_train.trainer import ParallelTrainer, SplitTaskParam, RayParams
    from alpha_invest.trainingpack.xgboost_pack import XGboostPack
    # step2: 实例化Trainer，设置Trainer入参，已继承并实现的Backend类，任务类型，以及ray_params参数类型
    trainer = ParallelTrainer(backend=XGboostPack, task_mode='LocalTrain', ray_params=RayParams(cpus_per_worker=1, gpus_per_worker=1))
    # step3: 框架根据data_params配置的字典参数自动进行任务切分，SplitTaskParam类型的参数多个任务笛卡儿积切分，非SplitTaskParam参数多个任务共享
    # 如下参数被切分为四组参数：
    # {'share_factor': 'factor_share', 'train_date': '20220418', 'strategy_type_factor': 'factor1'}
    # {'share_factor': 'factor_share', 'train_date': '20220418', 'strategy_type_factor': 'factor2'}
    # {'share_factor': 'factor_share', 'train_date': '20220419', 'strategy_type_factor': 'factor1'}
    # {'share_factor': 'factor_share', 'train_date': '20220419', 'strategy_type_factor': 'factor2'}
    data_params = { "train_date": SplitTaskParam(["20220418"]*10),
                    "num_features": 40,
                   "tag_name": "Tag5minRet",
                   "mock_data_flag": False,
                    'max_train_group_size': 180,  # 训练集包含的天数
                    }
    # 设置模型所需参数，透传给Backend类中train方法中的model_params所使用
    model_params = {
        'n_estimators': 659,
        'max_depth': 5,
        'learning_rate': 0.0372697,
        'subsample': 0.6424,
        "colsample_bytree": 0.879219,
        'gamma': 10,
        'tree_method': 'gpu_hist',
        'objective': 'multi:softprob',
        'num_class': 3,
        'random_state': 123,  # 保证结果可复现
        "use_cv": False
    }
    # 并行训练开始
    t1 = time.time()
    return_iterator = trainer.parallel_run(model_params=model_params, data_params=data_params)

    # step4: 获取训练结果迭代器，并打印train方法中的返回值
    result_list = []
    for result in return_iterator:
        result_list.extend(result)
    print("LocalTrain模式汇总的训练结果为：", time.time()-t1)
    print(pd.DataFrame(result_list).to_pickle("/data/user/quanttest007/result1.pkl"))

def dist_train():
    from parallel_train.trainer import ParallelTrainer, SplitTaskParam, RayParams
    from alpha_invest.trainingpack.dist_xgboost_pack import DistXGboostPack
    # step2: 实例化Trainer，设置Trainer入参，已继承并实现的Backend类，任务类型，以及ray_params参数类型
    trainer = ParallelTrainer(backend=DistXGboostPack, task_mode='DistTrain', ray_params=RayParams(cpus_per_worker=1,gpus_per_worker=0.5))

    # step3: 设置运行参数
    data_params = {"num_features": 40,
                   "tag_name": "Tag5minRet",
                   "mock_data_flag": False,
                   'max_train_group_size': 180,  # 训练集包含的天数
                   }
    # 设置模型所需参数，透传给Backend类中train方法中的model_params所使用
    model_params = {
        'n_estimators': 350,
        'max_depth': 3,
        'learning_rate': 0.01,
        'subsample': 0.50,
        'colsample_bytree': 0.50,
        'gamma':  2,
        'tree_method': 'hist',
        'objective': 'multi:softprob',
        'num_class': 3,
        'random_state': 123,  # 保证结果可复现
        "use_cv": False
    }
    # 并行训练开始
    t1 = time.time()
    return_iterator = trainer.parallel_run(model_params=model_params, data_params=data_params)

    # step4: 获取训练结果迭代器，并打印train方法中的返回值
    result_list = []
    for result in return_iterator:
        result_list.extend(result)
    print("DistTrain模式汇总的训练结果为：", time.time()-t1)
    print(pd.DataFrame(result_list))


def parallel_tune():
    def objective(params):
        import os
        import sys
        data_params = {"factor_path": "/data/user/quanttest007/alpha_invest/merge_data_688599.parquet",
                        "num_features": params.pop("num_features"),
                       "tag_name": params.pop("tag_name"),
                       "mock_data_flag": True,
                       'max_train_group_size': 450,  # 训练集包含的天数
                       }
        sys.path.append("/data/user/quanttest007/alpha_invest")
        # os.system(
        #     "sh /data/user/quanttest007/alpha_invest/alpha_invest/install.sh")
        from alpha_invest.trainingpack import xgboost_pack
        xgboost_pack.XGboostPack.run_single_instance(data_params=data_params, model_params=params)

    # Optuna suggest params
    config = {
        # "num_features": tune.choice([40, 80, 120, 200]),
        "num_features": tune.choice([100, 50, 200]),
        "tag_name": tune.choice(["Tag1minRet", "Tag2minRet", "Tag5minRet"]),#tune.choice(['tag2minShort', 'tag2minShort', 'tag1minShort', 'tag5minLong', 'tag2minLong', 'tag1minLong'])
        'n_estimators': tune.randint(100, 200),
        'max_depth': tune.randint(3, 10),
        'learning_rate': tune.uniform(0.001, 0.02),
        'subsample': tune.uniform(0.50, 0.90),
        'colsample_bytree': tune.uniform(0.50, 0.90),
        'gamma': tune.uniform(0, 1),
        'tree_method': 'hist',
        'objective': 'multi:softprob',
        'num_class':3,
        'random_state':123,#保证结果可复现
        "use_cv": False, #是否交叉验证,
        'early_stopping_rounds': 50,
        "n_jobs": 2

    }

    from ray.tune.suggest.optuna import OptunaSearch
    # from ray.tune.suggest import grid_search
    optuna_search = OptunaSearch(metric='auc', mode='max')
    # optuna_search = grid_search(metric='auc', mode='max')
    tune.run(objective, config=config, search_alg=optuna_search,
             num_samples=4, #resources_per_trial={'gpu': 0},
             name = 'xgboost_T0_688599', local_dir = '/data/user/quanttest007/alpha_invest/ray_results')


if __name__=="__main__":
    if False:
        from xquant.compute.ray_cluster import start_ray_cluster, recycle_ray_cluster
        # try:
        #     recycle_ray_cluster()
        # except:
        #     pass
        # time.sleep(60)
        #启动分布式ray集群
        redis_address = start_ray_cluster(cpus_per_node = 2, gpus_per_node = 0, mem_per_node = 24, maxWorkers = 10, minWorkers=10,
                          image="168.61.124.82/000322/xquant/jupyter_hadoop26_spark22:research_uat_v3.0",
                          startup_command="pip uninstall -y parallel_train && pip install /data/user/quanttest007/alpha_invest/torch-1.9.0+cu111-cp36-cp36m-linux_x86_64.whl && sh /data/user/quanttest007/alpha_invest/alpha_invest/install.sh")
        print("redis_address:", redis_address)
        ray.init(address = redis_address, runtime_env = {"env_vars": {"PYTHONPATH": "/data/user/quanttest007/alpha_invest:$PYTHONPATH" }})
    else:
        ray.init(num_cpus = 4)

    # parallel_train()
    parallel_tune()
    # dist_train()


