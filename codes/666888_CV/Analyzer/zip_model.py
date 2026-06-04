import os
import zipfile
import re


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
        # tar为写入的文件，tar[len(filePath)]为保存的文件名        
        # for pattern in alpha_code:
            # if re.search(pattern, tar):
        # print(tar)
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


#zip_file('C:\\Users\\USER\\Desktop\\algosystem-FC-master', 'D:\\a\\')
#un_zip(r'D:\01mine\06-Python\20171215\232717.zip', r'D:\01mine\06-Python\20171215\all')

#GPU数据地址
# source_path = "/app/data/011478/ModelSaved/"
#GPU数据地址
# save_path = "/app/data/011478/Production/"

# zip_file(source_path, save_path, "ModelSaved")