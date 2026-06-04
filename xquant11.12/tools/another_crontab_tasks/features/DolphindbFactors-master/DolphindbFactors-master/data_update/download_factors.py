from ftplib import FTP
import os
def download_from_ftp(remotepath, localpath):
    # ?ftp??
    ftp_68 = FTP()
    ftp_68.set_debuglevel(2)
    ftp_68.connect("168.8.2.68", 21)
    ftp_68.login("ftphzh", "ftphzh2602")
    ftp_68.cwd("/016869/DolphindbFactors/")
    bufsize = 1024
    fp = open(localpath, 'wb')
    ftp_68.retrbinary('RETR ' + remotepath, fp.write, bufsize)
    ftp_68.set_debuglevel(0)
    fp.close()

    # ???
    os.system("tar -xvf {}".format(localpath))



if __name__ == "__main__":
    file_name = "OnlineFactors20230612.tar"
    target_path = "/home/appadmin/{}".format(file_name)
    download_from_ftp(file_name, target_path)
