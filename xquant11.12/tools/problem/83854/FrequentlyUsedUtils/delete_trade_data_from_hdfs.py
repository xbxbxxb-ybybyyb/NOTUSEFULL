from xquant.pyfile import Pyfile
import os 
from Logger.Logger import Logger
     
py = Pyfile()

last_date = "20181001"


log_file = "/app/data/666888/Logging/delete_trade/log_info_20190308.txt"
if not os.path.exists("/app/data/666888/Logging/delete_trade/"):
    os.makedirs("/app/data/666888/Logging/delete_trade/")
log_fd = Logger(log_file, level='info')


def delete_trade_data(end_date, path="TradeData/"):
    total_stocks = len(py.listdir(path))
    stock_index = 0
    for stock in py.listdir(path):
    # for stock in ["601318.SH"]:
       
        stock_path = path+"/"+stock 
        date_index = 0
        for date in py.listdir(stock_path):
            data_path = stock_path+"/"+date
            if date < end_date:
                date_index = date_index+1
                py.delete(data_path,recursive =True)
                log_fd.logger.info("deleting "+ data_path)
            else:
                pass
        stock_index = stock_index+1
        print("We have deleted {} days from stock {}".format(stock_index, stock))
        print("Having deleted {} stocks  ".format(stock_index))
        log_fd.logger.info("We have deleted {} days from stock {}".format(date_index, stock))
        log_fd.logger.info("Having deleted {} stocks  ".format(stock_index))

                                           
delete_trade_data("20181001")


