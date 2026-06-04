#!/bin/bash
# CUR_DIR=$(cd `dirname $0`; pwd)
# echo $CUR_DIR
# PACKAGE_DIR=$(cd $CUR_DIR; cd ../package; pwd)
# export PATH="$PATH:/home/appadmin/python-ddb/bin"
# deploy_dir="/app/indicator"
# deploy_config_dir="${deploy_dir}/tmp"
# if [ ! -d $deploy_dir ];then
#     mkdir -p  $deploy_dir
# fi
# if [ -d $deploy_config_dir ];then
#     cur_date=$(date +%Y%m%d)
#     mv $deploy_config_dir $deploy_config_dir$cur_date
#     #rm -rf $deploy_config_dir
# fi
# mkdir -p  $deploy_config_dir
# cp -arf $PACKAGE_DIR/* $deploy_config_dir
# cd $deploy_config_dir && unzip 000465*_automininghff.zip
# cd AutoMiningFrame/DolphinDBServer/server
# #python3 start.py $*
# #rm -rf $deploy_config_dir

import os
import sys
import argparse
import datetime
parser = argparse.ArgumentParser()

# ??
deploy_types = "all"


# ????
cur_dir = os.getcwd()
print("?????{}".format(cur_dir))
package_dir = os.path.join(cur_dir, "../package")

os.system("""
            export PATH="$PATH:/home/appadmin/python-ddb/bin" \
          """)

# ?????????????
deploy_dir = "/app/indicator"
if not os.path.exists(deploy_dir):
    os.mkdir(deploy_dir)

deploy_config_dir = os.path.join(deploy_dir, "tmp")
if not os.path.exists(deploy_config_dir):
    os.mkdir(deploy_config_dir)

# ?????????
cur_date = datetime.datetime.now().strftime("%Y%m%d")
bak_deploy_config_dir = deploy_config_dir+cur_date

parser.add_argument('-dt', '--deploy_types', nargs="+", default="stock_mm1", type=str,
                        help='input the deploy_type')
parser.add_argument('-uf', '--update_factor', default="no", type=str,
                        help='need update factor yes or no')
parser.add_argument('-e', '--env', default="dev", type=str,
                        help='input the env[dev or prd]')
parser.add_argument('-ft', '--factor_type', default="stock_tick_norm", type=str,
                        help='input need update factor type')
args = parser.parse_args()
deploy_types = args.deploy_types
env = args.env
factor_type = args.factor_type
update_factor_tag = False if args.update_factor == "no" else True

# ????
if "all" in deploy_types:
    os.system("rm -rf {}".format(bak_deploy_config_dir))
    os.system("mv {} {}".format(deploy_config_dir, bak_deploy_config_dir))
    os.makedirs(deploy_config_dir)
    os.system("cp -rf {}/* {}".format(package_dir, deploy_config_dir))
    os.system("cd {} && unzip 000465*_automininghff.zip".format(deploy_config_dir))

# ??????????????
else:
    os.system("rm -rf {}".format(bak_deploy_config_dir))
    os.system("cp -r {} {}".format(deploy_config_dir, bak_deploy_config_dir))
    for deploy_type in deploy_types:

        #unzip -o -j 000465_S_automininghff.zip "AutoMiningFrame/DolphinDBServer/server/dev/se_stock_tick_l2p_mm1/*" \
        # -d AutoMiningFrame / DolphinDBServer / server / dev / se_stock_tick_l2p_mm1 /
        # ????
        if not os.path.exists(os.path.join(deploy_config_dir, f"AutoMiningFrame/DolphinDBServer/server/{env}/{deploy_type}/")):
            os.makedirs(os.path.join(deploy_config_dir, f"AutoMiningFrame/DolphinDBServer/server/{env}/{deploy_type}/"))
        os.system(f"""
                  cd {deploy_config_dir} && unzip -o -j 000465*_automininghff.zip "AutoMiningFrame/DolphinDBServer/server/{env}/{deploy_type}/*" -d AutoMiningFrame/DolphinDBServer/server/{env}/{deploy_type}/  
                  """)
    if update_factor_tag:
        if factor_type == "stock_tick_norm":
            os.system(f"""
                  cd {deploy_config_dir} && unzip -n -j 000465*_automininghff.zip "AutoMiningFrame/DolphinDBServer/server/modules/StockMMNormAllFactors/*" -d AutoMiningFrame/DolphinDBServer/server/modules/StockMMNormAllFactors/  
                  """)
            os.system(f"""
                  cd {deploy_config_dir} && unzip -o -j 000465*_automininghff.zip "AutoMiningFrame/DolphinDBServer/server/modules/StockMMNormAllNoneFactors/*" -d AutoMiningFrame/DolphinDBServer/server/modules/StockMMNormAllNoneFactors/  
                  """)
        elif factor_type == "stock_tick_l2p":
            os.system(f"""
                  cd {deploy_config_dir} && unzip -n -j 000465*_automininghff.zip "AutoMiningFrame/DolphinDBServer/server/modules/StockMMNormAllFactors/*" -d AutoMiningFrame/DolphinDBServer/server/modules/StockMMNormAllFactors/  
                  """)
            os.system(f"""
                  cd {deploy_config_dir} && unzip -o -j 000465*_automininghff.zip "AutoMiningFrame/DolphinDBServer/server/modules/StockMMNormAllNoneFactors/*" -d AutoMiningFrame/DolphinDBServer/server/modules/StockMMNormAllNoneFactors/  
                  """)

