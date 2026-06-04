"""
rust代码编译为whl包后，在docker上用pip装包后调用
"""
from trade_mocker_rust import trade_mocker_rust as tmr
import time
import datetime as dt
import json
import sys

file_type = "hdfs"
mode = "L2P"
data_path = "/root/mdc_data"

stock_code = sys.argv[1]
trade_date = sys.argv[2]
#stock_code = "688012.SH"
order_time = 20230801093939000;
#trade_date =  str(int(order_time/1000000000))
print(trade_date)
order_price= 140.70;
order_volume= 400;
bs_flag = "B";
order_kind = "0";


# 初始化并加载数据
t1 = time.time()
tmk = tmr.trade_mocker_instance( mode, trade_date, True)
#t1 = time.time()
# 模拟下单
#tmk.send_order(stock_code=stock_code, order_time=order_time, order_price=order_price, order_volume=order_volume,
#         bs_flag=bs_flag)

t1 = time.time()
# 获取交易订单的成交信息
#record = tmk.match_order_util_mdtime(20230801150000000)
#result = tmk.get_current_l2p_snapshot("688012.SH")
#print(result)
#p_orders = tmk.get_pending_orders() 
#c_orders = tmk.get_cancel_orders()
#f_orders = tmk.get_finished_order()

#print(p_orders)
#print(c_orders)
#print(f_orders)
#print(json.loads(record))
#print("rust版TradeMocker模拟撮合时间：{}s".format(time.time() - t1))




#tmk.presist_l2p_data("000977.SZ")

#tmk.presist_l2p_data("300475.SZ")

t1 = time.time()
tmk.presist_l3_data(stock_code)
print("生成l2p耗时：", time.time()-t1)

#t1 = time.time()
#tmk.presist_l2p_data(stock_code)
#print(time.time()-t1)


#result = tmk.get_current_l2p_snapshot("688012.SH")
#print(result)


