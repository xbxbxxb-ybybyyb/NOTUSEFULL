import xfactor.Runner.BasicRunner as Runner
#import xfactor.Runner.Runner as Runner
import time

start = time.time()
res = Runner.run(["SampleMinuteFactor"], 20181201, 20190101, options={"ray.num_cpus": 8})

# Runner.run(["SampleFactor"], 20180101, 20190101, options={"ray.num_cpus": 8}, output_factor_lib="zero_alpha")
#res = Runner.run(["SampleDependFactor"], 20180601, 20190101, options={"ray.num_cpus": 8}, input_factor_lib="zero_alpha")

print(res)
print("total cost time:", time.time() - start)


