import requests
import pandas as pd
import json
import os
from FactorProvider.setEnv import xquantEnv
from FactorProvider.conf.DubboConf import get_userid
from FactorProvider.utils.utils import is_valid_date
import base64
from Crypto.Cipher import AES
import time
import pexpect
import random
import paramiko
import warnings

warnings.filterwarnings("ignore")


def __get_apollo_conifg():
    if xquantEnv == 0:
        apollo_ip = "168.61.11.7:8085"
        appid = "XQUANT-THIRDPARTYDATA.c40857173f29cd20f509967567c791ce"
    else:
        apollo_ip_pool = ["168.9.26.28:8080", "168.9.26.29:8080", "168.15.77.196:8080", "168.15.77.197:8080"]
        i = random.randint(0, len(apollo_ip_pool) - 1)
        apollo_ip = apollo_ip_pool[i]
        appid = "XQUANT-THIRDPARTYDATA.c40857173f29cd20f509967567c791ce"
    apollo_http = "http://" + apollo_ip + "/configfiles/json/" + appid + "/default/table_authority"
    try:
        response = requests.get(apollo_http)
        status_code = response.status_code
        if status_code != 200:
            raise Exception("Apollo config connect failed !")
    except Exception as e:
        raise e
    res_json = response.text
    apollo_config = json.loads(res_json)
    return apollo_config


def decrypt(ciphertext):
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]

    CIPHER_KEY = 'eUMMn9zWE8EBPHt6hkNooQ=='
    CIPHER_KEY_bytes = CIPHER_KEY.encode('utf-8')
    enc = base64.b64decode(ciphertext)
    iv = enc[:AES.block_size]
    if not os.path.exists('/opt/anaconda3/lib/python3.11'):
        cipher = AES.new(CIPHER_KEY, AES.MODE_CBC, iv)
    else:
        cipher = AES.new(CIPHER_KEY_bytes, AES.MODE_CBC, iv)
    return _unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')


def __borrow_stock_pool(page_no=None, page_size=None, stk_code=None, start_time=None,
                        end_time=None, team=None, p_user=None, config=None):
    url = config["stockborrow_gateway"]
    post_data = {"pageNo": page_no, "pageSize": page_size}
    if stk_code:
        post_data["securityId"] = stk_code
    if start_time and end_time:
        post_data["startTime"] = start_time
        post_data["endTime"] = end_time
    if team:
        post_data["team"] = team
    if p_user:
        post_data["publishUserId"] = p_user
    response = requests.post(url, data=post_data)
    res_data = json.loads(response.text)
    return res_data


def borrow_stock_pool_sdk(stk_code=None, start_time=None, end_time=None, team=None, p_user=None):
    """
    查询所有可借的券源信息
    :param page_no: 页码
    :param page_size: 每页信息数 （若大于1000，默认返回1000）
    :param stk_code: 可选，可填写标的名称或代码，不填默认查询所有
    :param start_time: 可选，YYYYMMDD，返回出借信息发布时间 >= start_time的信息，不填返回所有，如果传了开始时间必须传结束时间
    :param end_time: 可选,YYYYMMDD,返回出借信息发布时间 <= end_time的信息，不填，返回所有
    :param team: 可选，券源归属团队，目前只有投资团队，不填返回所有团队
    :param p_user: 发布人工号
    :return:
    """
    user_id = get_userid()
    apollo_config = __get_apollo_conifg()
    # 可访问用户列表，后期若用户较多再配置到Apollo上
    permission_list = apollo_config["stockborrow_account"].split(",")
    # permission_list = ["013150", "016869", " 021041", "quanttest005", "quanttest007"]
    if user_id not in permission_list:
        raise Exception(f"{user_id}没有访问借券信息接口权限。")
    if start_time and not end_time:
        raise Exception("【start_time】如果传了开始时间必须传结束时间。")
    if start_time and not is_valid_date(start_time, date_type='year_month_day'):
        raise Exception("【start_time】的日期为YYYYMMDD格式，如 '20200330'")
    if end_time and not is_valid_date(end_time, date_type='year_month_day'):
        raise Exception("【end_time】的日期为YYYYMMDD格式，如 '20200330'")
    res1 = __borrow_stock_pool(page_no=1, page_size=100, config=apollo_config)
    total_num = res1['total']
    if total_num == 0:
        print("网关查询暂无借券信息！！！")
        return pd.DataFrame()
    pageSize = 1000
    if total_num > pageSize:
        page_num = total_num // pageSize + 1
    else:
        page_num = 1
    df_list = []
    for i in range(page_num):
        res_data = __borrow_stock_pool(page_no=i + 1, page_size=pageSize, stk_code=stk_code,
                                       start_time=start_time, end_time=end_time, team=team,
                                       p_user=p_user, config=apollo_config)
        df_p = pd.DataFrame(res_data["list"])
        if not df_p.empty:
            df_list.append(df_p)
    if df_list:
        df = pd.concat(df_list)
        if "class" in df.columns:
            df.drop("class", axis=1, inplace=True)
        cols_CH = {"publishTime": "发布时间", "securityId": "证券代码", "securityDesc": "证券名称",
                   "publishUserId": "发布人", "portfolioNo": "券源归属组合", "team": "券源归属团队",
                   "tradingAccount": "出借账户", "securityAccount": "出借股东", "period": "出借期限",
                   "orderQty": "出借数量", "cumQty": "剩余可借(股)"}
        df = df.rename(columns=cols_CH)
        df = df[["发布时间", "证券代码", "证券名称", "出借账户", "出借股东", "出借数量",
                 "出借期限", "剩余可借(股)", "券源归属组合", "券源归属团队", "发布人"]]
        return df
    else:
        return pd.DataFrame(columns=["发布时间", "证券代码", "证券名称", "出借账户", "出借股东", "出借数量",
                                     "出借期限", "剩余可借(股)", "券源归属组合", "券源归属团队", "发布人"])


def check_and_create_remote_directory(hostname, port, username, password, remote_path):
    # 创建 SSH 客户端
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # 连接到远程服务器
        ssh.connect(hostname, port=port, username=username, password=password)

        # 检查目录是否存在
        stdin, stdout, stderr = ssh.exec_command(f'if [ ! -d "{remote_path}" ]; then echo "not_exists"; fi')
        result = stdout.read().decode().strip()

        if result == "not_exists":
            # 如果目录不存在，则创建它
            ssh.exec_command(f'mkdir -p "{remote_path}"')
    finally:
        # 关闭 SSH 连接
        ssh.close()


def generate_rsa(hostname):
    # 将目标主机ip密钥信息添加到已知主机列表中
    tmp_file = "/tmp/known_hosts.txt"
    known_hosts_path = "~/.ssh/known_hosts"
    if not os.path.exists(tmp_file):
        # 如果文件不存在，创建文件，如果文件存在会更新文件的访问及修改时间，文件内容不变
        os.system("mkdir -p ~/.ssh")
        os.system(f"touch {known_hosts_path}")
        os.system(f"ssh-keyscan {hostname} >> {known_hosts_path} 2> /dev/null")
    cmd_info = f"ssh-keyscan -f {known_hosts_path} > {tmp_file} 2>&1"
    os.system(cmd_info)
    flag = True
    with open(tmp_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            if hostname in line:
                flag = False
                break
    if flag:
        os.system(f"ssh-keyscan {hostname} >> {known_hosts_path} 2> /dev/null")


def upload_borrowstock_file_sdk(file):
    """
    上传Excel文件进行批量借券
    :param file:  借券信息文件地址，Excel文件(.xlsx)
    :return:
    """
    user_id = get_userid()
    apollo_config = __get_apollo_conifg()
    # 可访问用户列表，后期若用户较多再配置到Apollo上
    permission_list = apollo_config["stockborrow_account"].split(",")
    if user_id not in permission_list:
        raise Exception(f"{user_id}没有访问借券信息接口权限。")
    if not os.path.isfile(file) or not file.endswith(".xlsx"):
        raise Exception(f"file: {file} 不是.xlsx文件或文件地址不存在！")
    if xquantEnv == 0:
        hostname = "168.61.113.49"
        port = 22
        username = "appadmin"
        password = decrypt("XxafUkIateVyVzi4oDbVIVwnYGiwkTLnXfYHZK49L9VB3LQlZE6/x19yDXDpv+3u")
        target_path = "/app/to-nas/"
    else:
        hostname = "168.11.18.47"
        port = 22
        username = "appadmin"
        password = decrypt("RbcmtDrNTHY2wGdcT+CqY5IJaFACczckTfQR+zuFIGsimn3hnS+rfxrS7jLAidUt")
        target_path = "/app/to-nas/"
    today = time.strftime("%Y-%m-%d")
    remote_path = os.path.join(target_path, today)
    if not remote_path.endswith("/"):
        remote_path = remote_path + "/"
    check_and_create_remote_directory(hostname, port, username, password, remote_path)
    generate_rsa(hostname)
    # 匹配 要求输密码的正则 appadmin@168.61.113.49's password:
    password_key = ".*?\'s password:"
    cmd_info = f"/usr/bin/rsync -raz -t {file} {username}@{hostname}:{remote_path}"
    execute = pexpect.spawn(cmd_info, encoding='utf-8')
    # 等待密码提示
    # py38加上timeout=2会导致收不到输密码提示。
    idx = execute.expect([password_key, pexpect.EOF, pexpect.TIMEOUT])
    if idx == 0:  # 如果收到了密码提示
        execute.sendline(password)  # 发送密码
        # 等待命令结束
        execute.expect(pexpect.EOF)
        print("借券文件上传成功！")
        execute.close()
        return True
    else:
        print("借券文件上传失败！")
        execute.close()
        return False


