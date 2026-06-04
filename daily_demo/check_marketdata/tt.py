from MDCDataProvider.DataProvider import DataProvider
import ray
ray.init(num_cpus=1)
mdp = DataProvider()

print(1)

@ray.remote
def a():
    mdp = DataProvider()
    df = mdp.get_data_by_year_month('Stock', '000632.SZ', '202103')
    print(1)
ray.get(a.remote())
import time
time.sleep(20)

