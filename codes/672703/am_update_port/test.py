import pandas as pd
import datetime
def update_hfactor(start_date,end_date):
    print("start")
    from xquant.compute.aimr import AIMR
    import json
    start_end_date = {}
    start_end_date['start_date'] = start_date
    start_end_date['end_date'] = end_date
    pd.to_pickle(start_end_date,'/data/group/800020/AlphaDataCenter/Transit/update_factor/hstart_end_date.pkl')
    factor_dict=pd.read_pickle('/data/group/800020/AlphaDataCenter/Transit/update_factor/hfactor_dict_new.pkl')
    print(factor_dict.keys())
    params = {
        "parallel_list": list(factor_dict.keys()),   
        "tag":"xquant",
        "cpu":8,
        "gpu":0,
        "memory":20000
   }
    AIMR.runTasks('am_update_port/test1.py',json.dumps(params))
update_hfactor('20200703','20200703')