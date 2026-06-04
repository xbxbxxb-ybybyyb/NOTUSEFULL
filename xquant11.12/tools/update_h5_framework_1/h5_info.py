# _*_ coding:utf-8 _*_

from tables import *
import os
import re

def get_h5_info():
    path = "/app/data/wdb_h5/WIND"
    h5_paths = []
    h5_names = os.listdir(path)
    for h5_name in h5_names:
        if h5_name in ['AShareBalanceSheet','AShareDescription']:
            continue
        h5_path = os.path.join(path, h5_name, h5_name + '.h5')
        h5_paths.append(h5_path)
    print("have %d pieces H5!"%len(h5_paths))
    for hdf5 in h5_paths:
        print("Now the number : %d"%(h5_paths.index(hdf5)))
        # 写入txt文件需指定编码utf8
        # with open("h5_info.txt", 'a', encoding='utf8') as f:
        print("Read H5 :",hdf5)
        with open(os.path.join("/app/data/wdb_h5/WIND_TEST","h5_info.csv"),'a') as f:
            # 全路径文件名
            h5file = open_file(hdf5)
            for group in h5file.root:
                regular = re.compile(r'/([\s\S]*?) \(')
                # 组名
                group_name = re.findall(regular,str(group))[0]
                f.write('"文件",%s' % hdf5 + '\n')
                f.write('"表",%s'% group_name + '\n')
                table = group.table
                # 表名
                table_name = table.name
                # f.write('"表",%s'% table_name + '\n')
                # 列名,类型
                for name in table.colnames:
                    name_type = table.coldtypes[name]
                    f.write('"列",%s,%s' %(name,name_type) + '\n')
                f.write('\n')

get_h5_info()

