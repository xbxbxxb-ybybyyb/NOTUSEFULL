import os, json, re
from collections import defaultdict
import datetime as dt
from ftplib import FTP

def download_from_ftp(remotepath, localpath):
    ftp_68 = FTP()  # ????
    ftp_68.set_debuglevel(2)  # ??????2???????
    ftp_68.connect("168.8.2.68", 21)  # ???ftp sever???
    ftp_68.login("ftphzh", "ftphzh2602")  # ?????????
    ftp_68.cwd("/016869/dolphin_server/")
    bufsize = 1024                # ???????
    fp = open(localpath, 'wb')     # ???????????
    ftp_68.retrbinary('RETR ' + remotepath, fp.write, bufsize)# ???????????????
    ftp_68.set_debuglevel(0)         # ????
    fp.close()                    # ????

def get_docker_memory():
    with open('/sys/fs/cgroup/memory/memory.limit_in_bytes') as f:
        byte_memory_limit = int(f.read())
    with open('/sys/fs/cgroup/memory/memory.usage_in_bytes') as f:
        byte_memory_usage = int(f.read())
    return int((byte_memory_limit - byte_memory_usage))


def get_docker_cpu():
    with open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us') as f:
        cpu_quota = int(f.read())
    with open('/sys/fs/cgroup/cpu/cpu.cfs_period_us') as f:
        cpu_period = int(f.read())
    return int(cpu_quota / cpu_period)


def start_dolphin_server():
    print("[DolphindbServer]安装启动本地DolphinDB服务")
    # 下载最新服务端版本
    download_from_ftp("start.sh", "/home/appadmin/start.sh")
    # 根据docker资源调整启动服务的配置
    docker_cpu = get_docker_cpu()
    docker_mem = get_docker_memory()//1024//1024 # 单位转成GB
    proper_cpu = docker_cpu
    proper_mem = min(docker_mem, proper_cpu*8)
    os.system("sh /home/appadmin/start.sh {} {}".format(proper_cpu, proper_mem))

def gen_online_factor_zip(factor_path, non_factor_path=None, config_file=None, zip_name=None):
    root_path = "./OnlineFactors"
    target_nonfactors_path = os.path.join(root_path, "NonFactors")
    target_factors_path = os.path.join(root_path, "Factors")
    custom_factor_dict = defaultdict(list)

    os.system("mkdir -p {}".format(target_factors_path))
    os.system("mkdir -p {}".format(target_nonfactors_path))
    if non_factor_path:
        os.system("mkdir -p {}".format(target_nonfactors_path))
        os.system("cp -r {} {}".format(non_factor_path, target_nonfactors_path))
    # 加载json文件
    factor_config = json.load(open(config_file))
    factor_list = [i for i in factor_config]
    for factor_name in factor_list:
        prefunc_script = ""
        # 加载配置文件参数
        custom_params = factor_config[factor_name]
        # 因子文件路径
        total_path = os.path.join(factor_path, factor_name) + ".dos"
        with open(total_path, "r") as f:
            content = f.readlines()
            script_factor = "\n".join([i for i in content])
            for i in content:
                if "module" in i or 'use' in i:
                    prefunc_script += i + "\n"
                else:
                    if "@state" in i:
                        break

        script_factor = re.search(r'@.*', script_factor, re.DOTALL).group()
        script_factor = prefunc_script + script_factor

        print(script_factor)
        for custom_param_dict in custom_params:
            pattern = re.compile(r"[(](.*?)[)][{]", re.S)
            res = re.findall(pattern, script_factor)[0]
            res_copy = res
            for k, v in custom_param_dict.items():
                if k not in res:
                    raise Exception("自定义参数没有: {}".format(k))
                # target_param = [i for i in res.split(",") if k in i][0]
                target_param = [i for i in res.split(",") if i.strip().startswith(k) and "=" in i][0]
                res = res.replace(target_param, " " + k + "=" + str(v))
            script_factor_cus = script_factor.replace(res_copy, res)
            if custom_param_dict:
                script_factor_cus = script_factor_cus.replace(factor_name, factor_name + "_" + "_".join(
                    [k + str(v) for k, v in custom_param_dict.items()]))
            custom_factor_dict[factor_name].append(script_factor_cus)

    for factor_name, script_factor_list in custom_factor_dict.items():
        for script_factor in script_factor_list:
            # 提取因子名和参数
            sear = re.search(r'def (.*?){.*?return (.*?)}', script_factor, re.DOTALL)
            # 提取因子函数名+依赖
            funcFactor = sear.group(1)
            # 提取结果因子名
            resFactor = sear.group(2)
            resFactor = re.sub(r'\s', '', resFactor).split(',')
            for res in resFactor:
                if not res.startswith(factor_name):
                    raise Exception(
                        'return因子名需以函数名为前缀，如{res} --> {factor_name}_{res}'.format(factor_name=factor_name, res=res))

            # s.run(script_factor)
            file_handle = open('{}/{}.dos'.format(target_factors_path, funcFactor.split("(")[0]), mode='w')

            file_handle.write(script_factor)

            print('{} - parse factor ok'.format(factor_name))

    # 打包命名
    os.system("zip -r {} {}".format(zip_name, root_path))
    return


def check_date(date):
    if len(date) != 8:
        raise Exception("{}:时间格式错误, 请使用正确格式,如20200802".format(date))
    try:
        dt.datetime.strptime(date, '%Y%m%d')
    except BaseException:
        raise Exception("{}:时间格式错误".format(date))


if __name__ == "__main__":
    factor_path = "/app/nsw_test/online_factor/test/factor_star"
    config_file = "/app/nsw_test/online_factor/test/factor_config_star_tick_all_param.json"
    res = gen_online_factor_zip(factor_path,
                                non_factor_path=None,
                                config_file=config_file,
                                zip_name="OnlineFactor.zip")
