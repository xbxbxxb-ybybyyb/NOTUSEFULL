import pandas as pd
import datetime
update_factor_help_path = '/data/user/013546/AlphaDataCenter/Transit/update_factor/'
def update_hfactor(start_date,end_date):
    print("start")
    from xquant.compute.aimr import AIMR
    import json
    start_end_date = {}
    start_end_date['start_date'] = start_date
    start_end_date['end_date'] = end_date
    pd.to_pickle(start_end_date,update_factor_help_path+'hstart_end_date.pkl')
    factor_dict=pd.read_pickle('/data/group/800020/AlphaDataCenter/Transit/update_factor/hfactor_dict.pkl')
    print(factor_dict.keys())
    params = {
        "parallel_list": list(factor_dict.keys()),   
        "tag":"xquant",
        "cpu":24,
        "gpu":0,
        "memory":60000
   }
    AIMR.runTasks('am_update_port/test_single_factor.py',json.dumps(params))
update_hfactor('20200303','20200303')