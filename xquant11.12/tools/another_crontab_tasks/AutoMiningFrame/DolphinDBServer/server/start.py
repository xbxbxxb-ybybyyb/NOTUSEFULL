# coding=utf-8
import os
from datetime import datetime
import json
import socket
import subprocess
import argparse

CURRENT_WORK_FILE = os.path.abspath(__file__)
BASE_WORK_DIR = os.path.dirname(CURRENT_WORK_FILE)

#WORK_DIR = "/app/indicator/compute"
WORK_DIR = "/app/indicator/tmp/AutoMiningFrame/DolphinDBServer/server"
#持久化目录，包括hdd，coredump
PRESIST_DIR = "/app/indicator/presist"
if not os.path.exists(PRESIST_DIR):
    os.makedirs(PRESIST_DIR)



def log(msg):
    print('[{0}] {1}'.format(
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg))


def read_config(env, deploy_type_list, host_file, ip):
    with open(host_file, "r") as f:
        f_data = f.read()

    json_config = json.loads(f_data)

    for k, v in json_config.items():
        dir_num, dir_letter = split_num_letter(k)
        if dir_letter in deploy_type_list and v == ip:
            log("current ip is %s, dir is %s, begin..." % (v, k))
            #generate_full_dir(env, k)
            start_command(env, k)
            log("current ip is %s, dir is %s, end..." % (v, k))
        else:
            log("dir:%s,ip:%s , %s not equal type:%s,machineip:%s, skip..." % (k, v, dir_letter, deploy_type_list, ip))


def split_num_letter(string):
    nums, letters = "", ""
    val = string.split('-')[0]
    for i in val:
        if i.isdigit():
            nums = nums + i
        elif i.isspace():
            pass
        else:
            letters = letters + i
    return nums, letters


def run_shell(cmd):
    log("run command: %s" % cmd)
    res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = res.communicate()
    if res.returncode != 0:
        raise Exception('run cmd:%s failed. returncode:%s, cause:%s' % (cmd, res.returncode, stderr))


def generate_full_dir(env, dir_name):
    full_dir = os.path.join(WORK_DIR, dir_name)
    if not os.path.exists(full_dir):
        os.makedirs(full_dir)

    dir_num, dir_letter = split_num_letter(dir_name)
    log("current type is %s" % dir_letter)

    # 拷贝common中文件夹为dir_letter到full_dir
    log("copy common/%s to %s" % (dir_letter, full_dir))
    cmd = 'cp -rf {}/* {}'.format(os.path.join(BASE_WORK_DIR, 'common', dir_letter), full_dir)
    run_shell(cmd)

    # 拷贝args.env到full_dir
    log("copy %s to %s" % (env, full_dir))
    env_dir = os.path.join(BASE_WORK_DIR, env, dir_name)
    cmd = 'cp -rf {}/ddb.cfg {}/config'.format(env_dir, full_dir)
    run_shell(cmd)
    cmd = 'cp -rf {}/*-compose.yml {}'.format(env_dir, full_dir)
    run_shell(cmd)

    stock_dos = os.path.join(env_dir, 'stock.dos')
    if os.path.exists(stock_dos):
        cmd = 'cp -rf {}/stock.dos {}/config/default_cfg'.format(env_dir, full_dir)
        run_shell(cmd)


def get_host_ip():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return ip


def start_command(env, dir_name):
    service_dir = os.path.join(WORK_DIR, env)#, dir_name)
    start_file = "start.sh"
    cmd = "cd {} && bash {} {}".format(service_dir, start_file, dir_name.strip())
    log("{} is ready to start! Command is {}".format(dir_name, cmd))
    # os.system(cmd)
    run_shell(cmd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--env', help='The deployment environment, dev/sim/prod', required=True)
    parser.add_argument('-t', '--type', help='The deployment type, fund_mm', required=True)
    parser.add_argument('-s', '--site', help='The deployment site, nj/sz', required=True)
    args = parser.parse_args()

    env = args.env
    deploy_type = args.type
    site_val = args.site

    deploy_type_list = deploy_type.split(',')
    site_list = site_val.split(',')

    ip = get_host_ip()

    for site in site_list:
        if site == "nj":
            host_file = os.path.join(BASE_WORK_DIR, env, "host.json")
        else:
            host_file = os.path.join(BASE_WORK_DIR, env, "host-{}.json".format(site))

        read_config(env, deploy_type_list, host_file, ip)
