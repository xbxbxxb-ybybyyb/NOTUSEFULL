import BT_HDFS.GENERATE_SIGNAL as gentrate_signal
import BT_HDFS.GET_TICK_TRANS_CAPACITY as get_trade_and_combine
import BT_HDFS.RUN_BT as run_bt
import TimerTask.run_get_order_capacity_1 as get_capacity_1
import TimerTask.run_get_order_capacity_2 as get_capacity_2
import TimerTask.run_get_order_capacity_3 as get_capacity_3


def main():
    if False:
        get_capacity_1.main()  # 获取Order Capacity
    if False:
        get_capacity_2.main()   # 获取Order Capacity
    if False:   
        get_capacity_3.main()   # 获取Order Capacity
    if False:
        get_trade_and_combine.main(is_get_trade=True) # 获取交易数据


    if False:
        gentrate_signal.main()        # 生成信号
    if True:
        # 生成组合
        get_trade_and_combine.main(is_get_trade=False, is_combine_trade_capacity=True, is_copy_trade_2_share=True)
    if False:
        # copy信号，并回测
        run_bt.main()


if __name__ == "__main__":
    main()
