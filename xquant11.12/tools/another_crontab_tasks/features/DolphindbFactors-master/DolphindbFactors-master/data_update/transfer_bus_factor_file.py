import os
import re
# 将业务老师提供的因子文件中的非因子逻辑整合到NoneFactor中，因子逻辑按照函数分配到不同的文件中
source_file = "/home/appadmin/DolphindbFactors/factors/CentralTrading/factor_update.dos"
target_file_path = "./CentralFactors"
target_non_factor = "./CentralNoneFactors/CentralTradingNoneFactor.dos"
all_content = open(source_file,'r').read()

all_content_list = all_content.split("@state")
nonfactor = all_content_list[0]
factors = all_content_list[1:]
for factor in factors:
    sear = re.search(r'def (.*?){.*?return (.*?)}', factor, re.DOTALL)
   # 提取结果因子名
    resFactor = sear.group(2).strip("")[:-1]
    print("["+resFactor+"]")
    factor_name = sear.group(1)
    script = "module Factors::{}".format(resFactor)
    all_script = script+"\n"+"use NoneFactor::CentralTradingNoneFactor\n"+"@state\n"+factor
    with open(os.path.join(target_file_path, "{}.dos".format(resFactor)),"w") as f:
        f.write(all_script)

#print("module NoneFactor::CentralTradingNoneFactor")
#print(nonfactor)
#script = "module NoneFactor::CentralTradingNoneFactor\n"+nonfactor
#with open(target_non_factor,"w") as f:
#        f.write(script)


import os
import json
# 生成配置文件
a = open("factor_config.json",'w')
res_dict = {}
# "CentralFactors"
# "../factors/InfoTech/StockMMRetV1Factors"
for root,dir,files in os.walk("./CentralFactors"):
    
    for file in files:
        print(file)
        if file.endswith(".dos"):        
            res_dict[file[:-4]] = [{}]
a.write(json.dumps(res_dict))
        
