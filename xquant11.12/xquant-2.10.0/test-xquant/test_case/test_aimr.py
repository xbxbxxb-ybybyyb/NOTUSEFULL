import json
import unittest
import os

from version_control import version_number

if version_number == 0:
    if os.environ.get('ENV_VERSION',False):
        raise Exception("xquant.tensorflow is deprecated!")
    class TestAimr(unittest.TestCase):
        def test_demo(self):
            import xquant.tensorflow as xt
            import json
            param = {
                "parallel_list": ["601688", "000002", "300350"],
                "docker_version": "htsc:latest",
                "type": "cpu"
            }
            xt.run_tensorflow("test.py",json.dumps(param))
            
else:
    from xquant.compute.aimr import AIMR
    class TestAimr(unittest.TestCase):
    
        def test_demo(self):
            pass
            print("start")
            params = {
                "parallel_list": ["1","2","3","4"],   
                "docker_version": "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:prd_gpu_v3.0",
                "tag":"xquant",
                "cpu":1,
                "gpu":0,
                "memory":1200
            }
            AIMR.runTasks('job.py',json.dumps(params))
            print("end")
            # print("start")
            # params = {
            #     "parallel_list": ["000001.SZ"],
            #     "docker_version": "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:prd_gpu_v3.0",
            #     "tag":"xquant",
            #     "cpu":1,
            #     "gpu":1,
            #     "memory":1200
            # }
            # 
            # AIMR.runTasks('sample_gpu.py',json.dumps(params))
            # print("end")
