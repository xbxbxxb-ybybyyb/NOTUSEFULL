import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
import ToolBox.utils as utils
# import ToolBox.stock_groups as stocks
import ToolBox.get_order_capacity as get_order_capacity
import TimerTask.task_config as config
from DataAPI.DataToolkit import get_complete_stock_list


def main():
    # task_index = str(2)
    start, end = config.start, config.end
    dates = utils.get_signal_dates(start, end)
    # stock_list = stocks.stock_groups[task_index]
    stock_list = get_complete_stock_list()[1300:2600]
    dates.sort()
    get_order_capacity.get_order_capacity(dates, stock_list=stock_list)


if __name__ == "__main__":
    main()
