"""文件夹操作辅助函数：
（1）下载FTP文件
（2）压缩和解压文件
（3）拷贝文件夹
（4）删除文件夹
"""

import os
import zipfile
import shutil
from ftplib import FTP
from DataAPI.DataView import file_list_dir


def to_ftp(file_path, file_name):
    ftp = FTP_OP(host="168.8.2.60", username="zsd", password="zsd")
    ftp.uploadFile(f'{file_path}/{file_name}', f'STOR /011668/{file_name}')


# ----------------------------------------------------------------------------------------
# （1）下载FTP文件
class FTP_OP:
    def __init__(self, host="168.8.2.68", username="xquant", password="Xquant-32", port=21):
        self.host = host
        self.username = username
        self.password = password
        self.port = port

    def ftp_connect(self):
        ftp = FTP()
        ftp.set_debuglevel(0)
        ftp.connect(host=self.host, port=self.port)
        ftp.login(self.username, self.password)
        print(f"ftp is connected")
        return ftp

    def downloadFile(self, ftp_file_path, dst_file_path, target_file=None):
        buffer_size = 4096
        ftp = self.ftp_connect()
        ftp.encoding = 'gb2312'
        file_list = ftp.nlst(ftp_file_path)
        if target_file is None:
            download_files = file_list
        else:
            download_files = [file for file in file_list if file == target_file]

        for target_file in download_files:
            ftp_file = os.path.join(ftp_file_path, target_file)
            write_file = os.path.join(dst_file_path, target_file)
            if not os.path.exists(dst_file_path):
                os.makedirs(dst_file_path)
            if not os.path.exists(write_file):
                with open(write_file, "wb") as f:
                    ftp.retrbinary('RETR {0}'.format(ftp_file), f.write, buffer_size)
                print(f"target file {target_file} is downloaded")
            else:
                print(f"target file {target_file} is not downloaded, for it has been under {dst_file_path}")
        ftp.quit()

    def uploadFile(self, dst_file_path, ftp_file_path):
        ftp = self.ftp_connect()

        with open(dst_file_path, "rb") as f:
            ftp.storbinary(ftp_file_path, f)
        ftp.quit()


# ----------------------------------------------------------------------------------------
# （2）压缩和解压文件
def zip_file(source_path, save_path, file_name):
    """
    将文件夹下的文件保存到zip文件中。
    :param source_path: 待存文件夹
    :param save_path: 存储路径
    :return:
    """
    save_path = os.path.realpath(save_path)
    print(save_path)
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    file_list = []
    if file_name[-1] == '/':
        file_name = file_name[: -1]
    new_zip = zipfile.ZipFile(save_path + "/" + file_name + '.zip', 'w')
    for dir_path, dir_names, file_names in os.walk(source_path):
        for filename in file_names:
            file_list.append(os.path.join(dir_path, filename))
    count = 0
    for tar in file_list:
        new_zip.write(tar, tar[len(source_path):])
        count = count + 1
    print ("num:", count)
    new_zip.close()
    print('save to :', save_path)


def un_zip(file_path, unzip_path):
    """
    解压zip文件到指定路径
    :param file_path: 待解压文件
    :param unzip_path: 解压路径
    :return:
    """
    file = zipfile.ZipFile(file_path)
    file.extractall(unzip_path)
    print('unzip successfully to :', unzip_path)


# ----------------------------------------------------------------------------------------
# （3）拷贝文件夹
def copy_file(source_dir, target_dir, is_clear_target_dir=True, is_dir=True):
    if not os.path.exists(target_dir):  # 如果目标路径不存在原文件夹的话就创建
        os.makedirs(target_dir)
    if os.path.exists(source_dir) and is_clear_target_dir:  # 如果目标路径存在原文件夹的话就先删除
        shutil.rmtree(target_dir)
    shutil.copytree(source_dir, target_dir)


# ----------------------------------------------------------------------------------------
# （4）将文件从HDFS上传到NAS上
def transfer_file(hdfs_dir, nas_dir):
    from xquant.xqutils.xqfile import Pyfile
    if os.path.exists(nas_dir):
        shutil.rmtree(nas_dir)
    os.makedirs(nas_dir, exist_ok=True)
    Pyfile().download(nas_dir, hdfs_dir)


# ----------------------------------------------------------------------------------------
# （5）删除文件夹
def delete_dir(dir_path):
    shutil.rmtree(dir_path)


# (6) 文件夹重命名
def rename(src, dst):
    os.rename(src, dst)


def rename_dir(abs_path, suffix='_mt5'):
    all_file = file_list_dir(abs_path)
    for file in all_file:
        os.rename(f'{abs_path}/{file}', f'{abs_path}/{file}{suffix}')
