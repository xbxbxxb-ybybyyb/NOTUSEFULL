import ray
import pandas as pd
from xquant.compute.streamcalculation import run_realtime_calculation_by_securities
# 因子回调计算函数
def calc_callback(self, df_dict,custom_param=pd.DataFrame()):
    """
    实时行情计算回调函数，可利用入参自定义计算因子数据，以后执行后续的模型预测、信号发送等逻辑
    :param self, StreamCalcActor对象，可以获取self.logger日志对象,也可以添加用户自定义的变量，如模型等。
    :param df_dict: 开盘以来累计接收到的全部行情数据，可按自定义窗口截取行情数据，用于计算因子
    :return:
    """
    # 除df_dict外可添加多个关键字参数用于自定义计算  
    # 可选步骤一：加载自定义的模型用于数据预测
    if not hasattr(self, 'model'):
        from keras.models import load_model#import 模块最好在call-back函数中写
        # self.model = load_model('/home/appadmin/xxx_model')

    # 可选步骤二：自定义选取因子计算需要依赖的窗口大小
    window = 60  # 依赖前60个行情数据
    for stock in df_dict.keys():
        if type(df_dict[stock])==dict:
            for key in df_dict[stock].keys():
                df_dict[stock][key] = df_dict[stock][key].iloc[-window:]
                self.logger.info("{} {}数据形状为：{}".format(stock, key, df_dict[stock][key].shape))
        else:
            self.logger.warning("df_dict中存在key为{}的元素为DataFrame：{}，为订阅的第一只票的行情数据！".format(key, df_dict[key].shape))

    # 可选步骤三： 变更订阅的标的
    if not hasattr(self, 'flag'):
        self.flag = False
    if not self.flag and self.calculation_mode == 'realtime':
        stocks = ['600000.SH', '600004.SH', '601688.SH', '600007.SH','600519.SH']
        import random
        sub_stocks = list(set([stocks[random.randint(0,len(stocks)-1)], stocks[random.randint(0,len(stocks)-1)]]))
        self.change_stocks(sub_stocks)
        self.flag = True

    # 关键步骤：计算因子数据，并返回因子数据的DataFrame
    calc_df = df_dict['kline1m']['ClosePx'] - df_dict['kline1m']['ClosePx'].shift(1)
    print('worker_no:{}，finish calculation! now mdtime {} {}!'.format(self.worker_no,df_dict['kline1m']['MDTime'].iloc[-1], df_dict['kline1m']['HTSCSecurityID'].iloc[-1]))
    return None

calc_date = "20201221"
security_list = [["000001.SZ"], ["601688.SH"]]  # ["159915.SZ"]
security_type = "stock"
data_input_mode = ["KLine1M_RAW"]

#（1）选择alram+realtime模式范例：playback_or_realtime="realtime"
#run_realtime_calculation_by_securities(data_input_account="013150",
#                                       data_input_mode=data_input_mode,
#                                       security_list=security_list,
#                                       security_type=security_type,
#                                       calculation_mode="alarm",
#                                       tick_sample_interval = 3,
#                                       playback_or_realtime="realtime",
#                                       options={"local_mode": False},
#                                       calc_callback=calc_callback,
#                                       verbose=0)

#（2）选择tick+playback模式范例：playback_or_realtime="playback"
run_realtime_calculation_by_securities(data_input_account="013150", data_input_mode=data_input_mode,
                                        security_list=security_list, security_type=security_type,
                                        calculation_mode="tick", playback_or_realtime="playback", 
                                        playback_date = '20190701', options={"local_mode": False},
                                        calc_callback=calc_callback, verbose=0)   

