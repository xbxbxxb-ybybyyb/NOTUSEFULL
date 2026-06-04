import ToolBox.get_trade_data as get_trade_data
import datetime as dt
import ToolBox.constant_params as constants
import ToolBox.utils as utils
import ToolBox.stock_groups as stocks

task_index = str(1)
out_trade_data_path =  constants.trade_data_path
import TimerTask.task_config as config
start, end = config.start, config.end
signal_dates = utils.get_signal_dates(start, end)
                           
stock_list = stocks.stock_groups[task_index]        
        
get_trade_data.get_trade_to_hdfs(out_trade_data_path, signal_dates, stock_list=stock_list)