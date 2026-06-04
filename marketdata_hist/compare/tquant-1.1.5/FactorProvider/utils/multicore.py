# -*- coding: utf-8 -*-
import json
import os
import fcntl
import psutil
import FactorProvider.conf.DubboConf as DubboConf

def multicore_init():
    try:
        prop_file_base_dir = '/etc/.config/octopus'
        user_prop = DubboConf.get_xquantConfig()
        user_prop_str = '__xquant_config_json='+json.dumps(user_prop)
        # write xquantConfig to file
        with open(os.path.join(prop_file_base_dir, '__xquant_config.py'), 'w') as user_prop_writer:
            fcntl.flock(user_prop_writer, fcntl.LOCK_EX)
            user_prop_writer.write(user_prop_str + '\n')
            fcntl.flock(user_prop_writer, fcntl.LOCK_UN)

        factor_prop = DubboConf.get_jurisdictionData()
        factor_prop_str =  'jurisdictionData_dict = '+json.dumps(factor_prop)
        # write factorConfig to file
        with open(os.path.join(prop_file_base_dir, '__jurisdictionData_config.py'), 'w') as factor_prop_writer:
            fcntl.flock(factor_prop_writer, fcntl.LOCK_EX)
            factor_prop_writer.write(factor_prop_str + '\n')
            fcntl.flock(factor_prop_writer, fcntl.LOCK_UN)
        return True
    except Exception as e:
        print("【Warning】multicore_init failed!! ", e)
        return False


