# _*_ coding:utf-8 _*_
from ConnectionPool import OPMysql
import time

if __name__ == '__main__':
    t1 = time.time()
    #申请资源
    opm = OPMysql()
    sql = "select S_INFO_WINDCODE,ANN_DT,PAY_ALL_TYP_TAX from asharecashflow limit 100000"
    res = opm.op_select(sql)
    #print(res)
    t2 = time.time()
    print("查询花费时间为：%d s"%(t2-t1))
    #释放资源
    opm.dispose()





