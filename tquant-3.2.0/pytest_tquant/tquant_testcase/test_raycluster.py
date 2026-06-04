from tquant.compute.raycluster import RayCluster
import ray
import os
import pytest

@ray.remote
def add(a, b):
        return a + b

@pytest.mark.skipif(os.environ.get("DSWMAP_envTag") != 'prd', reason="生产环境条件下测试")
class TestRayCluster(object):
        """
        测试RayCluster集群计算
        """
        @classmethod
        def setup_class(cls):
                master = {"num_cpus": 1, "memory": 1, "replicas": 1}
                worker = {"num_cpus": 1, "memory": 1, "replicas": 1}
                cls.rc = RayCluster(master, worker, autoclose=False)

        def test_get_dashboard_ip(self):
                result = self.rc.get_dashboard_ip()
                assert result is not None

        def test_get_redis_address_from_job(self):
                result = self.rc.get_redis_address_from_job()
                assert result is not None

        def test_get(self):
                futures = [add.remote(i, i) for i in range(5)]
                assert ray.get(futures) == [0, 2, 4, 6, 8]

        def teardown_class(self):
                self.rc.close()


if __name__ == "__main__":
    pytest.main(["-v"])
