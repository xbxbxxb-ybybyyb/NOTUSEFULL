import ray
ray.init("auto")

@ray.remote(num_cpus = 1, memory = 4)
def calc():
    pass

if __name__=="__main__":
    tasks = [calc.remote() for i in range(1000)]
    ray.get(tasks)