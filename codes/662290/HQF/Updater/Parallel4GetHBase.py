from xquant.compute.aimr import AIMR
import json
import os
import sys
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../"))

print("start")
parallel_list = [str(1*i)+'-'+str(1*(i+1))+'-'+str(i+1) for i in range(25)]


params = {
    "parallel_list": parallel_list,
    "docker_version": "cgcregistry.azurecr.io/cgc/jupyter_hadoop26_spark22:prd_gpu_v3.0",
    "tag":"xquant",
    "cpu":2,
    "gpu":0,
    "memory":12000
}
AIMR.runTasks('HQF/Updater/GetHBase.py',json.dumps(params))
print("end")