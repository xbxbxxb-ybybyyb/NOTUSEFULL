import xquant.tensorflow as xt
import xquant
import time
import json
param1 = {
            "parallel_list": [     
                             
                    "0-200",
                    "200-400",
                    '400-600',
                    '600-800',
                    '800-1000',
                    '1000-1200',
                    '1200-1400',
                    '1400-1600',
                    '1600-1800',
                    '1800-2000',
                    '2000-2200'
                    ]
                                                                                                 
}  

param2 = {
            "parallel_list": [     
                             
                    "0-300",
                    "300-600",
                    '600-900',
                    '900-1200',
                    '1200-1500',
                    '1500-1800',
                    '1800-2200'
                    ]
                                                                                                 
}  


print("start")
xt.run_tensorflow("gpu_work.py", json.dumps(param1))
print("end")