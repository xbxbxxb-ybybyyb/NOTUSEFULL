# _*_ coding:utf-8 _*_

import pandas as pd
from op_tables import tables,hours
import cx_Oracle

def execute_sql(sql_use):
    # conn = cx_Oracle.connect("center_admin/timegao@168.61.2.2/servdb", encoding="UTF-8", nencoding="UTF-8")
    conn = cx_Oracle.connect("center_read/Htsc_Htzx@168.9.2.43/qdb04", encoding="UTF-8", nencoding="UTF-8")
    cur = conn.cursor()
    cur.execute(sql_use)
    res = cur.fetchall()
    result = res[0][0]
    return result

def calc_opdate(table,hour):

    sql_use = "select count(*) from %s where to_char(opdate,'hh24') = '%s' and to_char(opdate,'yyyy') >= 2016"%(table,hour)
    count = execute_sql(sql_use)
    return count


if __name__ == "__main__":
        for table in tables:
            print("正在统计：",table)
            try:
                for hour in hours:
                    count = calc_opdate(table,hour)
                    with open('opdate.csv','a') as f:
                        f.write(table+"|"+hour+"|"+str(count)+"\n")
            except Exception as e:
                print(table, "----->", e)
                continue








