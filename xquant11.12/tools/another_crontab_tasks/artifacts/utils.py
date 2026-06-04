import base64
from Crypto.Cipher import AES
import os
import ray
import platform
import json
import pandas as pd
if platform.system().lower() == 'linux':
    import fcntl
elif platform.system().lower() == 'windows':
    import fcntlock as fcntl
else:
    raise Exception("系统：{} 暂不支持！".format(platform.system().lower()))
import time

CIPHER_KEY = 'eUMMn9zWE8EBPHt6hkNooQ=='
xquant_id = None

def decrypt(ciphertext):
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]

    enc = base64.b64decode(ciphertext)
    iv = enc[:AES.block_size]
    cipher = AES.new(CIPHER_KEY, AES.MODE_CBC, iv)
    return _unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

def get_user_id():
    XQUANT_CONF_FILE = os.environ['XQUANT_CONF_FILE']
    with open(XQUANT_CONF_FILE, 'r') as f:
        r = f.readlines()
        for line in r:
            if line.startswith("userId"):
                return line.strip().split("=")[-1].strip()


def start_ray_cluster(object_spill_path = None, num_cpus = None, restart = True):
    if ray.is_initialized() and restart:
        ray.shutdown()
    if not object_spill_path:
        try:
            user_id = get_user_id()
            if os.path.exists(f"/dfs/user/{user_id}/"):
                object_spill_path = f"/dfs/user/{user_id}/"
            else:
                object_spill_path = f"/data/user/{user_id}/"
        except:
            object_spill_path = "/data/user/013150/tmp"

    # print("object_spill_path:", object_spill_path)
    if not num_cpus:
        ray.init(_system_config={
            "object_spilling_config": json.dumps(
                {"type": "filesystem", "params": {"directory_path": object_spill_path}},
            )},ignore_reinit_error=True)
    else:
        ray.init(num_cpus=num_cpus, _system_config={
            "object_spilling_config": json.dumps(
                {"type": "filesystem", "params": {"directory_path": object_spill_path}},
            )}, ignore_reinit_error=True)


class FileLock:
    def __init__(self, filename):
        self.filename = filename
        self.handle = open(self.filename, 'w')

    def acquire(self):
        fcntl.lockf(self.handle.fileno(), fcntl.LOCK_EX)# | fcntl.LOCK_NB)  # LOCK_EX与LOCK_NB按位或使用不阻塞，报OSError错误

    def release(self):
        # 延迟0.5秒释放锁，其他进程非阻塞return，不再写入文件
        time.sleep(0.5)
        if platform.system().lower() == 'linux':
            fcntl.lockf(self.handle.fileno(), fcntl.LOCK_UN)
        elif platform.system().lower() == 'windows':
            fcntl.unlock(self.handle.fileno())
        else:
            raise Exception("系统：{} 暂不支持！".format(platform.system().lower()))

    def close(self):
        try:
            self.handle.close()
        except:
            pass

    def __del__(self):
        try:
            self.handle.close()
        except:
            pass

def save_and_append_xlsx(result_df, sheet_name, output_path = "/home/appadmin/signal.xlsx"):
    from openpyxl import load_workbook
    result_df = result_df.reset_index()
    result_df["SYMBOL"] = sheet_name
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl', mode = "a", if_sheet_exists = "replace") as writer:
            df_strategy = result_df
            df_strategy.to_excel(writer, sheet_name = sheet_name, index=False)
            writer.save()
    except Exception as e:
        print(e)
        with pd.ExcelWriter(output_path, engine='openpyxl', mode = "w") as writer:
            df_strategy = result_df
            df_strategy.to_excel(writer, sheet_name = sheet_name, index=False)
            writer.save()

save_backtest_result = save_and_append_xlsx


def save_and_append_parquet(symbol_name, signal_df, save_parquet_path, overwrite_col = "DATE"):
    """
    :param symbol_name:
    :param signal_df:
    :param save_parquet_path:
    :param overwrite_col: 需要覆盖的列， 该列的值不允许有重复，比如DATE列已有20191010的数据，需要删除后再写入
    :return:
    """
    if signal_df.empty:
        return
    dir_name = os.path.dirname(save_parquet_path)
    os.makedirs(dir_name, exist_ok=True)
    if os.path.exists(save_parquet_path):
        try:
            source_signal_df = pd.read_parquet(save_parquet_path)
            source_signal_df = source_signal_df[~source_signal_df[overwrite_col].isin(set(signal_df[overwrite_col].tolist()))]
            if not "SYMBOL" in source_signal_df.columns:
                source_signal_df["SYMBOL"] = symbol_name
            new_signal_df = pd.concat([source_signal_df, signal_df], axis=0)
            new_signal_df.to_parquet(save_parquet_path)
        except:
            print("WARNING: 信号文件损坏：", save_parquet_path)
            signal_df.to_parquet(save_parquet_path)
    else:
        print("WARNING: 信号文件不存在：", save_parquet_path)
        if not "SYMBOL" in signal_df.columns:
            signal_df["SYMBOL"] = symbol_name
        signal_df.to_parquet(save_parquet_path)


def save_and_append_pickle(detail_data, save_path, overwrite_col="date"):
    if detail_data.empty:
        return
    print("文件路径: ", save_path)
    if os.path.exists(save_path):
        try:
            source_detail_df = pd.read_pickle(save_path)
            source_detail_df = source_detail_df[~source_detail_df[overwrite_col].isin(set(detail_data[overwrite_col].tolist()))]
            new_signal_df = pd.concat([source_detail_df, detail_data], axis=0)
            new_signal_df.to_pickle(save_path)
            print("文件日增数据完成")
        except Exception as e:
            print("ERROR: ", e)
            print("WARNING: 文件损坏：", save_path)
            detail_data.to_pickle(save_path)
    else:
        print("WARNING: 文件不存在：", save_path)
        detail_data.to_pickle(save_path)




