#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/4/30 14:02

import os
from ftplib import FTP


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

    def download_file(self, ftp_file_path, dst_file_path, target_file=None):
        buffer_size = 4096
        ftp = self.ftp_connect()
        ftp.encoding = 'gb2312'
        file_list = ftp.nlst(ftp_file_path)
        if target_file is None:
            download_files = file_list
        else:
            download_files = [file for file in file_list if file==target_file]

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
                print(
                    f"target file {target_file} is not downloaded, for it has been under {dst_file_path}")
        ftp.quit()


if __name__ == "__main__":
    ftp_path = "/Xquant/516/T0/Easy_2020/"
    local_path = "/data/user/015629/Easy/LiveReturnStat/"
    target_file = "20200729_T0_easy.xlsx"
    ftp = FTP_OP()
    ftp.download_file(ftp_path, local_path, target_file)