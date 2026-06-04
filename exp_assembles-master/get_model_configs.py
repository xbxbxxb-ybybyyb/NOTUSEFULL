import os
import re
from artifacts.utils import update_model_config
base_path = "/dfs/group/800657/exp_results/KG101_model"

model_list = ['hs300_px_lvl_1', 'hs300_px_lvl_123', 'hs300_px_lvl_2', 
              'hs300_px_lvl_3', 'hs300_px_lvl_4', 'hs300_px_lvl_45',
              'hs300_px_lvl_5', 'HS_big', 'HS_l2p2', 'HS_mid',
              'HS_sml', 'HS_tick', 'HS_tick2_add', 'HS_tick2_new']
model_config = {}
for model in model_list:
    model_config[model] = []
    model_file_path = os.path.join(base_path, model, "saved_models")
    files = os.listdir(model_file_path)
    pattern = re.compile("(\d{6}.SH|\d{6}.SZ)")
    for fil in files:
        response = re.findall(pattern, fil)
        if response:
            sk = response[0]
            model_config[model].append(sk)
# print(model_config)

for model in model_list:
    label_name = "LabelFirstPeak_th10_120s"
    exp_name = "KG101_model"
    if 'l2p' in model:
        data_type = "tick_l2p"
    else:
        data_type = "enhanced_tick_norm"
    if not model_config[model]:
        continue
    update_model_config(label_name, exp_name, version_alias=model, 
                        symbol_list=model_config[model], data_type=data_type,
                        file_path="/data/user/013150/exp_assembles-master/artifacts/run/tools/model_config.json")    


