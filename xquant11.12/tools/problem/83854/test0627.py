import xquant.tensorflow as xt
import json


param =  {
    "docker_version": "htsc:latest",
    "type": "cpu"
}

print("sss")
xt.run_tensorflow("test.py", json.dumps(param))
print("eee")