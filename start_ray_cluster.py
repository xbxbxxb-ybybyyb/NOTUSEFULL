import ray
import time
from xquant.setXquantEnv import xquantEnv

if xquantEnv==0:
    image = "168.61.124.82/000322/xquant/jupyter_hadoop26_spark22:research_uat_v3.0"
else:
    image = "168.11.220.16/000322/xquant/jupyter_hadoop26_spark22:research_prd_v3.0"


def get_docker_cpu():
    with open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us') as f:
        cpu_quota = int(f.read())
    with open('/sys/fs/cgroup/cpu/cpu.cfs_period_us') as f:
        cpu_period = int(f.read())
    return int(cpu_quota / cpu_period)


class RayManager:
    '''
    启动ray集群
    '''
    def start_cluster(self, cpus_per_node=1, gpus_per_node =0 ,mem_per_node=8, maxWorkers=8, minWorkers=8, local_cluster = True):
        if not local_cluster:
            from xquant.compute.ray_cluster import start_ray_cluster

            # 启动分布式ray集群
            redis_address = start_ray_cluster(cpus_per_node=cpus_per_node, gpus_per_node=0,
                                              mem_per_node=mem_per_node, maxWorkers=maxWorkers, minWorkers=minWorkers,
                                              image=image,
                                              startup_command='echo "caowei_20171010"|su root -c "cp /data/user/013150/021368/sit2prd/start_batchTest6.sh /opt/anaconda3/lib/python3.6/site-packages/xquant/strategy/ats_backtest/resource/start_batchTest.sh && cp  /data/user/013150/021368/sit2prd/ats-backtest-4.3.7-SNAPSHOT.jar /opt/lib/ats-backtest-4.3.6-SNAPSHOT.jar &&  cp  /data/user/013150/021368/sit2prd/ats-common-1.1-SNAPSHOT.jar /opt/lib/ats-common-1.1-SNAPSHOT.jar"')
            ray.init(address=redis_address,
                     runtime_env={"env_vars": {"PYTHONPATH": "/data/user/quanttest007/alpha_invest:$PYTHONPATH"}})
        else:
            num_cpus = min(get_docker_cpu(), cpus_per_node)
            ray.init(num_cpus = num_cpus)
            print("INFO：local_cluster为True，正使用本地节点资源并行回测：并发度为{}！".format(int(num_cpus/cpus_per_node)))



    '''
    停止ray集群
    '''

    def close_cluster(self, local_cluster = True):
        if not local_cluster:
            from xquant.compute.ray_cluster import recycle_ray_cluster
            # 回收分布式ray集群
            try:
                recycle_ray_cluster()
            except:
                pass
            time.sleep(60)
        else:
            ray.shutdown()

# RayManager().start_cluster(cpus_per_node = 1, gpus_per_node = 0, mem_per_node = 8, maxWorkers = 8, minWorkers=8)
# while(True):
#    time.sleep(6000)
