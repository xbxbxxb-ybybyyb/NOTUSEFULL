import sys
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../.."))
from xquant.pyfile import Pyfile
from Logger.Logger import Logger


def copy_signals_to_share(symbols, src_path, dst_path, end_date, is_big):
    log_file_path = "/data/user/666888/Logging/bt/{}/".format(str(end_date))
    if not os.path.exists(log_file_path):
        os.makedirs(log_file_path)

    if is_big:
        file_name = "debug_big.txt"
    else:
        file_name = "debug.txt"
    log_debug_file = log_file_path + file_name
    log_fd = Logger(log_debug_file, level='debug')
    log_fd.logger.debug("Start to copy signal...")

    py = Pyfile()
    i = 0
    for symbol in symbols:
        print(symbol)
        for date in py.listdir(src_path + symbol):
            source_file_dir = src_path + "/" + symbol + "/" + date + "/"
            dst_file_dir = dst_path + "/" + symbol + "/"
            print(source_file_dir, dst_file_dir)
            try:
                py.copyToShare(dst_file_dir, source_file_dir + '/')
            except Exception as e:
                print(repr(e))
                print("error copy {}, successfully copy {} stocks".format(symbol, i))
                log_fd.logger.debug("error copy {}".format(symbol))
                continue
            log_fd.logger.debug("successfully copied {} symbols".format(i))
            i = i + 1
            print("Copied {} stocks".format(i))


def main():
    import CV_NEW.CV_BIG.CONFIG_BIG as cv_config_big
    config = cv_config_big.CVConfig()
    model_prefix = '20190101_48_end'

    src_path = config.signalPath + "ModelSignalDataSet/"
    dst_path = 'ModelProduction/' + model_prefix + '/universe/'
    symbols = config.codes
    end_date = config.today_str
    copy_signals_to_share(symbols, src_path, dst_path, end_date, is_big=True)


if __name__ == '__main__':
    main()
