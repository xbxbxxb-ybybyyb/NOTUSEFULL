from L3FactorFrame.FactorManager import FactorManager
from L3FactorFrame.MarketDataManager import MarketDataManager
import time
import os
import ray
import json
from datetime import datetime


# FULL全量计算模式
@ray.remote(max_calls=5)
def UpdateFlyingFactorFull(symbol, date, source_factor_config, factor_path, event_path, nonfactor_path = None, save_base_dir = "/dfs/group/800657/library/l3_factor"):
    try:
        marketDataManager = MarketDataManager(symbol, date)
        runner = FactorManager(marketDataManager)
        runner.register_factor(source_factor_config, factor_path=factor_path, event_path = event_path, nonfactor_path = nonfactor_path)
        t1 = time.time()
        # 全量计算模式
        runner.calc_loop(mode="FULL")
        value_df = runner.get_all_factor_values(save_base_dir = save_base_dir, save_mode=True)
        # print(value_df)
        print("calculate time: {} {} {}".format(symbol, date, time.time()-t1))
    except Exception as e:
        print("ERROR: UpdateFlyingFactorFull, ", e, symbol, date)

if __name__=="__main__":
    ######################注意设置标的和日期####################
    from xquant.factordata import FactorData
    fa = FactorData()
    symbols_all = fa.hset("INDEX", "20240130", "000688.SH")["stock"].tolist()
    symbols = symbols_all
    dates = fa.tradingday("20240301", "20240408")
    now_date = datetime.now().strftime("%Y%m%d")
    dates = [date for date in dates if now_date>=date]
    # dates = ["20231207"]#,"20240129", "20240130"]
    print(symbols)
    print(dates)
    ######################注意修改存储路径####################
    save_base_dir = "/dfs/group/800657/library/l3_event/event_data/"
    factor_path = "./FactorsTest"  # 事件触发计算因子目录
    event_path = "./Events" # 事件触发计算事件目录
    nonfactor_path = "./NonFactors"  # 依赖因子触发目录
    source_factor_config = json.load(open(os.path.join(factor_path, "./factor_config_all.json"), "r"))
    source_factor_config.update(json.load(open(os.path.join(event_path, "./factor_config_all.json"), "r")))
    source_factor_config.update(json.load(open(os.path.join(nonfactor_path, "./factor_config_all.json"), "r")))
    print(json.dumps(source_factor_config, indent=4))
    time.sleep(5)
    ray.init(num_cpus=25, local_mode=True)
    ##########################################################
    t1 = time.time()
    tasks = []
    remote_func = ray.remote(UpdateFlyingFactorFull)
    for symbol in symbols:
        for date in dates[::-1]:
            tasks.append(remote_func.remote(symbol, date, source_factor_config, factor_path, event_path, save_base_dir = save_base_dir))
    ray.get(tasks)
    print("耗时：", time.time()-t1)
