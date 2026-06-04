import ray

def set_ray_options(num_cpus, object_store_memory, options):
    if ray.is_initialized():
        raise Exception("Ray计算环境启动失败：当前有正在使用的Ray计算环境，请用ps -ef|grep ray查看并停止！")
    if num_cpus is None:
        num_cpus = 4
    if options is None:
        options = {}
    if object_store_memory:
        ray.init(num_cpus=num_cpus, object_store_memory=object_store_memory,
                 **options) if not ray.is_initialized() else None
    else:
        ray.init(num_cpus=num_cpus, **options)
