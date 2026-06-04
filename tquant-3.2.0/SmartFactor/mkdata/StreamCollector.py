# -*- coding:utf-8 -*-
from insight.model import EMarketDataType_pb2 as EMarketDataType
import time
import sys
import datetime
import signal
from retrying import retry
from insight.data_handle import OnRecvMarkertDataBase
from insight import utils
from SmartFactor.logger import setup_logging
import os
import threading
import socket
from SmartFactor.constant import DataCollectMode, transform_datamode
from SmartFactor.util.util import check_security_type


class OnRecvMarkertData(OnRecvMarkertDataBase):
    def __init__(self, serverAddr, verbose = 0, auto_exit=True):
        self.logger = setup_logging("quant_info")
        # 启动UDS socket
        self.stock_dict = {}  # security和socket的绑定关系
        self.actor_stock = {}  # actor和security的绑定关系
        self.main_stock_dict = {}  # 主票与socket的绑定关系
        self.actor_main_stock = {}  # actor和主票的绑定关系
        self.socket_actor = {}  # socket和actor的绑定关系
        self.actor_socket = {}  # actor和socket的绑定关系
        self.verbose = verbose
        now = datetime.datetime.now()
        self.auto_exit = auto_exit
        self.exit_time = 153000000
        self.last_mdtime = 0

        self.serverAddr = serverAddr
        t1 = threading.Thread(target=self.acceptWorker, daemon=True)
        t1.start()
        time.sleep(5)

    def __socket_recv(self, client_sock, client_addr):
        size = client_sock.recv(5)
        data = int.from_bytes(size, byteorder='big')
        data = bytes.decode(client_sock.recv(data))
        actor_name, stock_list_str = data.split(':')
        stock_list = stock_list_str.split(',')
        main_stock = stock_list[0]

        if actor_name not in self.actor_socket:
            # actor在dict中不存在时，在dict中添加key
            self.actor_socket[actor_name] = client_sock
            self.socket_actor[client_sock.fileno()] = actor_name
            self.actor_main_stock[actor_name] = [main_stock]
            self.actor_stock[actor_name] = stock_list
        else:
            # 当同actor收到信息，需要更改标的，关闭原socket连接并建立新连接
            old_socket = self.actor_socket[actor_name]
            self.actor_socket[actor_name] = client_sock
            for stock in self.actor_stock[actor_name]:
                new_socket_list = []
                for socket_client in self.stock_dict[stock]:
                    if actor_name != self.socket_actor[socket_client.fileno()]:
                        new_socket_list.append(socket_client)
                self.stock_dict[stock] = new_socket_list
            self.actor_stock[actor_name] = stock_list
            for stock in self.actor_main_stock[actor_name]:
                new_main_stock_list = []
                for socket_client in self.main_stock_dict[stock]:
                    if actor_name != self.socket_actor[socket_client.fileno()]:
                        new_main_stock_list.append(socket_client)
                self.main_stock_dict[stock] = new_main_stock_list
            self.actor_main_stock[actor_name] = [main_stock]
            self.socket_actor[client_sock.fileno()] = actor_name
            old_socket.close()

        print("客户端名为%s, %s: %s进行了连接!" % (actor_name, client_sock, client_addr))
        if main_stock not in self.main_stock_dict:
            self.main_stock_dict[main_stock] = []
        self.main_stock_dict[main_stock].append(client_sock)
        for stock in stock_list:
            if stock not in self.stock_dict:
                self.stock_dict[stock] = []
            self.stock_dict[stock].append(client_sock)

    def acceptWorker(self):
        if os.path.exists(self.serverAddr):
            os.unlink(self.serverAddr)

        server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server_sock.bind(self.serverAddr)
        server_sock.listen(300)#最多接受300个链接

        while True:
            client_sock, client_addr = server_sock.accept()
            self.__socket_recv(client_sock, client_addr)

    @retry(stop_max_attempt_number=5, wait_fixed=2000)
    def send_uds_message(self, client_sock, data):
        if (self.auto_exit and (self.last_mdtime > self.exit_time)):
            os.killpg(os.getpgid(os.getpid()), signal.SIGINT)
        assert type(data)==bytes, "data must be bytes!"
        size = len(data).to_bytes(5, byteorder='big')# 默认一条数据长度不会超过32位
        try:
            client_sock.send(size)
            client_sock.send(data)
        except Exception as e:
            self.logger.error('socket发送失败')
            os.killpg(os.getpgid(os.getpid()), signal.SIGINT)

    def OnMarketData(self, marketdata):
        from insight.model import EMarketDataType_pb2 as EMarketDataType
        ##处理订阅的实时行情数据
        try:
            if marketdata.marketDataType == EMarketDataType.MD_TRANSACTION:  # .MD_TRANSACTION:逐笔成交
                if marketdata.HasField("mdTransaction"):
                    sockets = self.main_stock_dict.get(marketdata.mdTransaction.HTSCSecurityID)
                    if sockets:
                        # self.logger.info(
                        #     "start processing mdTransaction: {} {}".format(marketdata.mdTransaction.HTSCSecurityID,
                        #                                                    marketdata.mdTransaction.MDTime))
                        # actor.on_market_data.remote(marketdata.SerializeToString())
                        data = marketdata.SerializeToString()
                        t1 = str(round(time.time()*100000)).encode('ascii')
                        for socket in sockets:
                            self.send_uds_message(socket, t1)
                            self.send_uds_message(socket, data)
            elif marketdata.marketDataType == EMarketDataType.MD_ORDER:  # .MD_ORDER:逐笔委托
                if marketdata.HasField("mdOrder"):
                    sockets = self.main_stock_dict.get(marketdata.mdOrder.HTSCSecurityID)
                    if sockets:
                        # self.logger.info("start processing mdOrder: {} {}".format(marketdata.mdOrder.HTSCSecurityID,
                        #                                                           marketdata.mdOrder.MDTime))
                        data = marketdata.SerializeToString()
                        t1 = str(round(time.time() * 100000)).encode('ascii')
                        for socket in sockets:
                            self.send_uds_message(socket, t1)
                            self.send_uds_message(socket, data)
            elif marketdata.marketDataType == EMarketDataType.MD_KLINE_1MIN:
                if marketdata.HasField("mdKLine"):
                    sockets = self.stock_dict.get(
                        marketdata.mdKLine.HTSCSecurityID)
                    if sockets:
                        # self.logger.info("start processing mdOrder: {} {}".format(marketdata.mdOrder.HTSCSecurityID,
                        #                                                           marketdata.mdOrder.MDTime))
                        data = marketdata.SerializeToString()
                        t1 = str(round(time.time() * 100000)).encode('ascii')
                        for socket in sockets:
                            self.send_uds_message(socket, t1)
                            self.send_uds_message(socket, data)
            elif marketdata.marketDataType == EMarketDataType.MD_TICK:  # .MD_TICK 快照
                if marketdata.HasField("mdStock"):  # 股票
                    sockets = self.stock_dict.get(marketdata.mdStock.HTSCSecurityID)
                    if sockets:
                        self.logger.info("start processing mdTick: {} {}".format(marketdata.mdStock.HTSCSecurityID,
                                                                                 marketdata.mdStock.MDTime))
                        t1 = str(round(time.time()*100000)).encode('ascii')
                        data = marketdata.SerializeToString()
                        self.last_mdtime = marketdata.mdStock.MDTime
                        for socket in sockets:
                            self.send_uds_message(socket, t1)
                            self.send_uds_message(socket, data)
                elif marketdata.HasField("mdIndex"):  # 指数
                    print("HTSCSecurityID=%s lastprice=%d" % (
                        marketdata.mdIndex.HTSCSecurityID, marketdata.mdIndex.LastPx))
                elif marketdata.HasField("mdBond"):  # 债券
                    print(
                        "HTSCSecurityID=%s lastprice=%d" % (marketdata.mdBond.HTSCSecurityID, marketdata.mdBond.LastPx))
                elif marketdata.HasField("mdFund"):  # 基金
                    sockets = self.stock_dict.get(marketdata.mdFund.HTSCSecurityID)
                    if sockets:
                        if self.verbose > 0:
                            self.logger.info("start processing mdTick: {} {}".format(marketdata.mdFund.HTSCSecurityID,
                                                                                     marketdata.mdFund.MDTime))
                        t1 = str(round(time.time()*100000)).encode('ascii')
                        data = marketdata.SerializeToString()
                        self.last_mdtime = marketdata.mdFund.MDTime
                        for socket in sockets:
                            self.send_uds_message(socket, t1)
                            self.send_uds_message(socket, data)
                    # print("HTSCSecurityID=%s lastprice=%d" % (marketdata.mdFund.HTSCSecurityID, marketdata.mdFund.LastPx))
                elif marketdata.HasField("mdOption"):  # 期权
                    print("HTSCSecurityID=%s lastprice=%d" % (
                        marketdata.mdOption.HTSCSecurityID, marketdata.mdOption.LastPx))
            elif marketdata.marketDataType == EMarketDataType.MD_CONSTANT:  # .MD_CONSTANT:静态信息
                if marketdata.HasField("mdConstant"):
                    print(marketdata.mdConstant.HTSCSecurityID)
            elif marketdata.marketDataType == EMarketDataType.MD_TWAP_1S or marketdata.marketDataType == EMarketDataType.MD_TWAP_1MIN:  # .TWAP:TWAP数据
                if marketdata.HasField("mdTwap"):
                    print(marketdata.mdTwap)
            elif marketdata.marketDataType == EMarketDataType.MD_VWAP_1S or marketdata.marketDataType == EMarketDataType.MD_VWAP_1MIN:  # .VWAP:VWAP数据
                if marketdata.HasField("mdVwap"):
                    print(marketdata.mdVwap)

        except BaseException as e:
            print("onMarketData error happended!")
            import traceback
            print(traceback.print_exc())

    def OnPlaybackPayload(self, playload):
        # 处理订阅的回放行情数据
        try:
            utils.interface.set_service_value(4)
            # print("Parse Message id:" + playload.taskId)
            marketDataStream = playload.marketDataStream
            marketDataList = marketDataStream.marketDataList
            marketDatas = marketDataList.marketDatas
            for data in marketDatas:
                self.OnMarketData(data)
        except BaseException as e:
            print(e)

class InsightSDK:
    def __init__(self, user_id, serverAddr = '/tmp/test_unix.sock', verbose = 0, auto_exit=True):
        # 流量与日志开关设置
        # open_trace trace流量日志开关 # params:open_file_log 本地日志文件开关  # params:open_cout_log 控制台日志开关
        open_trace = True
        open_file_log = True
        open_cout_log = False
        self.verbose = verbose
        utils.get_interface().init(open_trace, open_file_log, open_cout_log)

        # 注册回调和接管日志
        self.callback = OnRecvMarkertData(serverAddr, verbose = verbose, auto_exit=auto_exit)
        utils.get_interface().setCallBack(self.callback)

        #登录
        utils.login(user_id)

    def __del__(self):
        utils.fini()

    def subscribe_by_type(self, security_type, data_types):
        from insight.interface import mdc_gateway_interface as mdc_gateway_interface
        from insight.model import ESecurityIDSource_pb2 as ESecurityIDSource
        from insight.model import MDSubscribe_pb2 as MDSubscribe
        from insight.model import ESecurityType_pb2 as ESecurityType

        if not security_type:
            raise Exception("实时计算框架的security_type为list或str类型，支持stock（股票）和fund（基金）！")
        if isinstance(security_type, str):
            security_type = [security_type]
        securitylist = []
        for s_type in security_type:
            if s_type.upper() == "STOCK":
                s_type = ESecurityType.StockType
            elif s_type.upper() == "FUND":
                s_type = ESecurityType.FundType
            else:
                raise Exception("security_type目前仅支持stock（股票）和fund（基金）两种！")

            # 沪深 - 股票
            if type(data_types) != list:
                element0 = mdc_gateway_interface.Element(ESecurityIDSource.XSHE, s_type, [data_types])
                element1 = mdc_gateway_interface.Element(ESecurityIDSource.XSHG, s_type, [data_types])
            else:
                element0 = mdc_gateway_interface.Element(ESecurityIDSource.XSHE, s_type, data_types)
                element1 = mdc_gateway_interface.Element(ESecurityIDSource.XSHG, s_type, data_types)
            securitylist.append(element0)
            securitylist.append(element1)

        # if security_type.upper() == "STOCK":
        #     security_type = ESecurityType.StockType
        # elif security_type.upper() == "FUND":
        #     security_type = ESecurityType.FundType
        # else:
        #     raise Exception("security_type目前仅支持stock（股票）和fund（基金）两种！")
        #
        # # 沪深 - 股票
        # if type(data_types) != list:
        #     element0 = mdc_gateway_interface.Element(ESecurityIDSource.XSHE, security_type, [data_types])
        #     element1 = mdc_gateway_interface.Element(ESecurityIDSource.XSHG, security_type, [data_types])
        # else:
        #     element0 = mdc_gateway_interface.Element(ESecurityIDSource.XSHE, security_type, data_types)
        #     element1 = mdc_gateway_interface.Element(ESecurityIDSource.XSHG, security_type, data_types)
        #
        # securitylist = [element0, element1]

        # MDSubscribe.COVERAGE模式，覆盖上一次的订阅内容
        action_type = MDSubscribe.COVERAGE
        utils.get_interface().subscribeByType(action_type, securitylist)
        utils.sync()

    def play_back_oneday(self, stock_list, start_time, stop_time, data_type = EMarketDataType.MD_TICK, sort=False):
        # 回放行情接口调用，调用回调类中的OnPlaybackPayload方法
        from insight.interface import mdc_gateway_interface as mdc_gateway_interface
        from insight.model import MDPlayback_pb2 as MDPlayback
        string_list = mdc_gateway_interface.StrList()
        for stock in stock_list:
            string_list.Add(stock)

        exrights_type = MDPlayback.NO_EXRIGHTS
        utils.get_interface().playSortCallback(string_list, start_time, stop_time, data_type, exrights_type, sort)



def get_stream_data(user_account, data_input_mode = ["TICK_ROW"], security_type = None, playback_or_realtime ="playback", playback_date = "20201221", security_list=None, verbose = 0, auto_exit=True):
    """
    :param user_account: str,insight的登录账号，一般为工号，新用户使用需向项目组申请Insight访问账户。
    :param data_input_mode: list，订阅的数据类型，目前支持TICK_RAW、TICK_SAMPLE（采样Tick数据）、TRANSACTION_RAW、ORDER_RAW、ORDER_SAMPLE、KLINE1M_RAW
    :param security_type: list，订阅的标的类型，支持STOCK（股票）、FUND（基金）。
    :param playback_or_realtime: str, 支持两种模式，REALTIME(订阅实时数据流)和PLAYBACK（实时数据流回放）。
    :param playback_date: str， 若playback_or_realtime为PLAYBACK，可选择数据回放的时间。
    :return:
    """
    # 检验security_type
    # check_security_type(security_type)
    insight = InsightSDK(user_id=user_account,  serverAddr = '/tmp/test_unix.sock', verbose = verbose, auto_exit=auto_exit)
    print("insight sdk start...")

    assert type(data_input_mode)==list, "data_input_mode必须为list类型！"

    data_types = []
    for mode in data_input_mode:
        mode = transform_datamode(mode)
        if mode == DataCollectMode.TICK_SAMPLE:
            data_types.append(EMarketDataType.MD_TICK)
        elif mode == DataCollectMode.TICK_RAW:
            data_types.append(EMarketDataType.MD_TICK)
        elif mode == DataCollectMode.TRANSACTION_RAW:
            data_types.append(EMarketDataType.MD_TRANSACTION)
        elif mode == DataCollectMode.TRANSACTION_SAMPLE:
            data_types.append(EMarketDataType.MD_TRANSACTION)
        elif mode == DataCollectMode.ORDER_RAW:
            data_types.append(EMarketDataType.MD_ORDER)
        elif mode == DataCollectMode.ORDER_SAMPLE:
            data_types.append(EMarketDataType.MD_ORDER)
        elif mode == DataCollectMode.KLINE1M_RAW:
            data_types.append(EMarketDataType.MD_KLINE_1MIN)
        else:
            raise Exception("DataCollectMode不支持此枚举类型: {}！".format(mode))


    if playback_or_realtime.lower() == "realtime":
        insight.subscribe_by_type(security_type=security_type, data_types=data_types)
    elif playback_or_realtime.lower() == "playback":
        if not security_list:
            raise Exception("playback模式必须传security_list")
        if len(data_input_mode) > 1:
            if len(data_input_mode) > 2:
                raise Exception("palyback模式下混合订阅仅支持以下方式：暂时只支持TRANSACTION和TICK同时订阅，或者ORDER和TICK数据同时订阅！")
            if EMarketDataType.MD_TRANSACTION in data_types and EMarketDataType.MD_TICK in data_types:
                data_types = [EMarketDataType.MD_TRANSACTION]  # 包含TICK数据
            elif EMarketDataType.MD_ORDER in data_types and EMarketDataType.MD_TICK in data_types:
                data_types = [EMarketDataType.MD_ORDER]  # 包含TICK数据
            else:
                raise Exception("palyback模式下混合订阅仅支持以下方式：暂时只支持TRANSACTION和TICK同时订阅，或者ORDER和TICK数据同时订阅！")
        # assert len(str(playback_date))==8 and datetime.datetime.strptime("20201010", "%Y%m%d"), "playback_or_realtime为playback模式时，需传入playback_date回测日期，如20201221！"
        # if security_type.lower() == "stock":
        #     stock_list = ['000001.SZ', '000012.SZ', '000026.SZ', '000037.SZ', '000055.SZ', '000068.SZ', '000150.SZ',
        #                   '000333.SZ', '000410.SZ', '000423.SZ', '000503.SZ', '000517.SZ', '000529.SZ', '000540.SZ',
        #                   '000552.SZ', '000564.SZ', '000581.SZ', '000593.SZ', '000606.SZ', '000617.SZ']
        # elif security_type.lower() == "fund":
        #     stock_list = ["159958.SZ", "159915.SZ"]
        # else:
        #     raise Exception()
        stock_list = []
        for stock in security_list:
            if type(stock) == list:
                stock_list += stock
            elif type(stock) == str:
                stock_list.append(stock)
            else:
                raise Exception('security_list中只支持list与str,存在{}'.format(type(stock)))
        stock_list = list(set(stock_list))
        insight.play_back_oneday(stock_list=stock_list, start_time="{}000000".format(playback_date),
                                 stop_time="{}235959".format(playback_date), data_type = data_types[0])  # 回放历史行情数据
    else:
        raise Exception("playback_or_realtime支持的模式仅为：REALTIME或PLAYBACK。")
    while True:
        time.sleep(10000)




if __name__ == "__main__":
    # ray.init(local_mode=False)
    # ray.init("auto", _temp_dir='/data/user/013150/tmp/ray', _redis_password='5241590000000000')
    params = {"user_account":"013150","data_input_mode":["TRANSACTION_SAMPLE", "TICK_SAMPLE"], "security_type":"fund", "playback_or_realtime":"playback", "security_list": ["159958.SZ", "159915.SZ"]}
    # get_stream_data(**params)
    # print("check_status: ", ray.get(dis_actor.check_status.remote()))#阻塞
    print("==============================InsightActor start success!============================")

    import multiprocessing
    market_process = multiprocessing.Process(target=get_stream_data, kwargs=params)
    market_process.start()


