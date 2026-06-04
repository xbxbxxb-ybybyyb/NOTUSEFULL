import ToolBox.get_trade_data as get_trade_data
import datetime as dt
import ToolBox.constant_params as constants
import ToolBox.utils as utils
import ToolBox.stock_groups as stocks
import ToolBox.get_order_capacity as get_order_capacity
import TimerTask.task_config as config


def main():
    task_index = str(3)
    outTradeDataPath = constants.order_capacity_path
    start, end = config.start, config.end
    signal_dates = utils.get_signal_dates(start, end)
    stock_list = stocks.stock_groups[task_index]
    signal_dates.sort()
    get_order_capacity.get_order_capacity(signal_dates, stock_list=stock_list)


if __name__ == "__main__":
    main()