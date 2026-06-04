from tquant.compute.raycluster import *
import json
import ray
import pytest


# TODO 需要丰富异常场景集成用例
@pytest.mark.skip
class TestRaycluster(object):
        def test_raycluster(self):
                params = {
                        "master": {"num_cpus": 2, "memory": 2, "replicas": 1},
                        "worker": {"num_cpus": 2, "memory": 2, "replicas": 1},
                        "image": "168.61.13.178:5000/htzq/tquant_jupyter:uat_v2.0",
                        "dashboard": True,
                        "local_object_store_memory": 1,
                        "env_var": {"ccc": 333, "ddd": 444}
                    }
                try:
                        # 实例化对象
                        rc = RayCluster(json.dumps(params))
                        # 获取ray集群dashboard地址
                        print(rc.get_dashboard_ip())
                        # 获取ray集群master端的redis地址
                        print(rc.get_reids_address_from_job())
                        # 连接Ray集群
                        ray.init("auto", ignore_reinit_error=True)
                        assert ray.is_initialized() == 1
                        print(rc.get_dashboard_ip())
                        print(rc.get_reids_address_from_job())
                        # 取消初始化
                        ray.shutdown()
                        assert ray.is_initialized() == 0
                        # 关闭ray集群计算
                finally:
                        rc.close()


if __name__ == "__main__":
    pytest.main(["-v"])
