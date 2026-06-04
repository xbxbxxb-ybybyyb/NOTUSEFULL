import imp
import sys
import os
import site
import traceback
from .trainer.BaseActor import BaseActor

python_path =  site.getsitepackages()

def get_dynamic_module(module_name):
    path = os.path.join(os.path.dirname(__file__), "trainer")
    module = imp.load_module(module_name, *imp.find_module(module_name, sys.path+python_path+[path]))
    return module

def get_actor_from_module(backend_actor_name):
    try:
        module = get_dynamic_module(backend_actor_name)
        local_actor_class = getattr(module, backend_actor_name)
    except:
        print(traceback.print_exc())
        raise Exception(f"backend_actor类加载失败：请确认{backend_actor_name}是否在parallel_train的trainner文件夹下！")
    assert issubclass(local_actor_class, BaseActor), "backend_actor类不合法！{}应该继承自base_actor基类！".format(backend_actor_name)
    assert hasattr(local_actor_class, "train"), "backend_actor类不合法！{}应该继承自base_actor基类, 并实现train方法！".format(backend_actor_name)
    return local_actor_class