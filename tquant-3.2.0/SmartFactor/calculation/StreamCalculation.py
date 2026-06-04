# _*_ coding:utf-8 _*_
import sys
import os
import ray
import time
import datetime
import pickle
import traceback
import signal
import numpy as np
import copy
import pandas as pd
from retrying import retry
# from utils.util import Kafka_producer
import socket
import threading
from queue import Queue
from insight.model import MarketData_pb2 as MarketData_pb2
from google.protobuf.json_format import MessageToJson
from SmartFactor.calculation.helper import set_ray_options, parse_callback_params
from SmartFactor.util.util import get_fac_class, factor_time_info, \
    check_date, check_return_and_lib, check_factor_list, check_factor_name, \
    check_factor_type, check_lag_date, check_security_type, \
    check_factor_sample_consist
from SmartFactor.util.data_context import get_stocks_pool
from SmartFactor.constant import DataCollectMode, transform_datamode
from SmartFactor.mkdata.StreamCollector import get_stream_data
import multiprocessing
from SmartFactor.logger import setup_logging
from SmartFactor.mkdata.helper import realtime_data_aux, \
    sample_transaction_data, sample_orderbook
from SmartFactor.util.event_trace import event_trace


@event_trace
def run_realtime_calculation_by_securities(factor_list=[],
        data_input_account="013150", data_input_mode=["TICK_RAW"], security_type=None,
        security_list=None, calculation_mode="tick", tick_sample_interval=3,  
        playback_or_realtime="playback", playback_date="20201221",
        file_path='./', num_cpus=None, object_store_memory=None, options=None,
        calc_callback=None, verbose=0, auto_exit=True):
    """
    :param factor_list: 需要计算的因子列表，每个元素代表一个因子，可以是srt或者因子类
    :param data_input_account: str,insight的登录账号，一般为工号，新用户使用需向项目组申请Insight访问账户
    :param data_input_mode: list，订阅的数据类型，目前支持TICK_RAW、TICK_SAMPLE（采样Tick数据）、TRANSACTION_RAW、ORDER_RAW、ORDER_SAMPLE、KLINE1M_RAW
    :param playback_or_realtime: str, 支持两种模式，REALTIME(订阅实时数据流)和PLAYBACK（实时数据流回放）。
    :param playback_date: str， 若playback_or_realtime为PLAYBACK，可选择数据回放的时间。
    :param tick_sample_interval: int，采样的时间间隔，单位为秒，当且仅当DataCollectMode为TICK_SAMPLE时必传
    :param security_type: str，订阅的标的类型，支持STOCK（股票）、FUND（基金）。
    :param security_list: list，需要计算的标的列表，如["159958.SZ", "159915.SZ"]。
    :param calculation_mode: 支持两种触发实时计算的模式：TICK（接收到tick行情后触发计算）和ALARM（按tick_sample_interval定时触发计算两种模式）.
    :param file_path: 默认值为’./’，file_path表示因子类文件的存储路径（绝对路径与相对路径均可），用于递归搜索并加载因子类。若factor_list中传的因子名为str，会从file_path下搜索。
    :param num_cpus:
    :param object_store_memory:
    :param options:
    :param calc_callback: object, 实时行情计算回调函数，可利用入参自定义计算因子数据，以后执行后续的模型预测、信号发送等逻辑
    :param verbose: int, 日志的输出级别，默认为0, 可取值0,10,20,30。大于0时显示详细的错误信息，大于10时显示收到的详细行情信息，大于20时保存两份实时数据到本地路径：df_dict.pkl（接收到行情数据），calc_df.pkl（实时计算的因子数据）。大于30显示详细的每条行情接收信息。
    :return:
    """
    # # 校验日期
    # check_date(start_date, end_date)
    # # 如果 是save模式 则校验library_name
    # check_return_and_lib(return_mode, library_name)
    # 检验security_tye
    check_security_type(security_type)
    # 初始化ray
    set_ray_options(num_cpus=1, object_store_memory=object_store_memory,
                    options=options, start_mode = 'actor')
    # # 校验factor_list
    # check_factor_list(factor_list, factor_type="TICK")

    # 启动insight行情客户端
    assert type(
        data_input_account) == str, "行情客户端账号data_input_account为工号，可联系项目组开通。"
    assert calculation_mode.lower() in ["tick",
                                        "alarm"], "calculation_mode只支持TICK（接收到tick行情后触发计算）和ALARM（按tick_sample_interval定时触发计算两种模式）！"
    if not calc_callback:
        raise Exception('请传入回调计算方法calc_callback')
    if not factor_list:
        parse_callback_params(calc_callback, has_factor_list = False)
    else:
        parse_callback_params(calc_callback, has_factor_list=True)

    if playback_or_realtime == 'playback' and calculation_mode.lower() == 'alarm':
        raise Exception('playback模式calculation_mode不能为alarm')

    has_tick_mode = False
    has_transaction_mode = False
    has_order_mode = False
    for mode in data_input_mode:
        if mode in ['TICK_RAW', 'TICK_SAMPLE', 'KLINE1M_RAW']:
            if has_tick_mode:
                raise Exception('只能选择TICK_RAW, TICK_SAMPLE, KLINE1M_RAW中的一种模式')
            has_tick_mode = True
        if mode in ['TRANSACTION_RAW', 'TRANSACTION_SAMPLE']:
            if has_transaction_mode:
                raise Exception(
                    '只能选择TRANSACTION_RAW, TRANSACTION_SAMPLE中的一种模式')
            has_transaction_mode = True
        if mode in ['ORDER_RAW', 'ORDER_SAMPLE']:
            if has_order_mode:
                raise Exception('只能选择ORDER_RAW, ORDER_SAMPLE中的一种模式')
            has_order_mode = True

    if playback_or_realtime == 'playback':
        auto_exit = False
    security_type_dict = {}
    if security_type is None:
        security_type = []
        from tquant import BasicData
        bd = BasicData()
        for security in security_list:
            if isinstance(security, (list, tuple)):
                for security_1 in security:
                    st = bd.get_security_type(security_1)
                    security_type.append(st)
                    security_type_dict[security_1] = st
            else:
                st = bd.get_security_type(security)
                security_type.append(st)
                security_type_dict[security] = st
        security_type = list(set(security_type))


    params = {"user_account": data_input_account,
              "data_input_mode": data_input_mode,
              "security_type": security_type,
              "playback_or_realtime": playback_or_realtime,
              "playback_date": playback_date, 'security_list': security_list,
              'auto_exit': auto_exit}
    market_process = multiprocessing.Process(target=get_stream_data,
                                             kwargs=params, daemon=True)
    market_process.start()

    actor_list = []

    # 映射因子与标的的关系
    fac_to_sec_dict = {}
    for fac_cls in factor_list:
        if type(fac_cls) == str:
            fac_cls = get_fac_class(fac_cls, file_path)
        assert fac_cls.__name__ == fac_cls.factor_name, "因子名称冲突：因子类名{}与因子名{}不一致！".format(
            fac_cls.__name__, fac_cls.factor_name)
        # 校验factor_name
        check_factor_name(fac_cls.factor_name)
        # 校验factor_type
        check_factor_type(fac_cls.factor_type)

        # cur_security_pool = get_stocks_pool(day=calc_date, security_type=fac_cls.security_type,
        #                                     securities=fac_cls.security_pool)
        fac_to_sec_dict[fac_cls] = None
    if {'TICK_SAMPLE', 'TRANSACTION_SAMPLE', 'ORDER_SAMPLE'}.intersection(
            {i.upper() for i in data_input_mode}) or calculation_mode == 'alarm':
        if fac_to_sec_dict:
            check_factor_sample_consist(fac_to_sec_dict.keys())
            tick_sample_interval = fac_cls.custom_params["sample_period"]
        else:
            tick_sample_interval = tick_sample_interval

    # # 映射标的与因子的关系
    # sec_to_fac_dict = {}
    # for key, value in fac_to_sec_dict.items():
    #     for code in value:
    #         sec_to_fac_dict[code] = sec_to_fac_dict.get(code, [])
    #         sec_to_fac_dict[code].append(key)
    # security_list = list(sec_to_fac_dict.keys())

    # TODO 默认所有因子计算的标的相同
    new_security_list = []
    for stock in security_list:
        if type(stock) == list:
            new_security_list.append(stock)
        elif type(stock) == str:
            new_security_list.append([stock])
        else:
            raise Exception(
                'security_list中只支持list与str,存在{}'.format(type(stock)))
    auto_exit_time = 153000000
    for sidx, stock_list in enumerate(new_security_list):
        actor_list.append(
            StreamCalcActor.remote(stock_list, list(fac_to_sec_dict.keys()),
                                   data_input_mode=data_input_mode,
                                   security_type=security_type,
                                   tick_sample_interval=tick_sample_interval,
                                   serverAddr="/tmp/test_unix.sock",
                                   calculation_mode=calculation_mode,
                                   calc_callback=calc_callback,
                                   verbose=verbose,
                                   playback_or_realtime=playback_or_realtime,
                                   auto_exit=auto_exit,
                                   auto_exit_time = auto_exit_time,
                                   security_type_dict=security_type_dict,
                                   worker_no = sidx))
        time.sleep(0.5)

    while True:
        if auto_exit and playback_or_realtime == "realtime" and int(datetime.datetime.now().strftime('%H%M%S'))*1000>auto_exit_time:
            print("【INFO】程序已到指定停止时间{}，正自动退出程序。。。".format(auto_exit_time))
            sys.exit(0)
        time.sleep(60)  # for actor in actor_list:  #     ray.get(actor.get_calc_df.remote())
    # Ray Actor远程函数获取因子计算结果
    # while True:
    #     time.sleep(60)
    #     pickle.dump(ray.get(actor_list[0].get_calc_df.remote()), open("cal_df_tmp.pkl", 'wb'))
    ray.shutdown()


@ray.remote
class StreamCalcActor():
    def __init__(self, stock_list, factor_list, data_input_mode, security_type,
            tick_sample_interval, serverAddr="/tmp/test_unix.sock",
            calculation_mode="tick", calc_callback=None, verbose=0,
            playback_or_realtime='playback', auto_exit=True, auto_exit_time = 153000000,
            security_type_dict={}, worker_no = None):
        """
        :param actor_name:
        :param serverAddr:
        :param calculation_mode: "alarm":定时计算， tick获取到tick数据后计算
        :return:
        """

        self.calc_round = 0
        self.df = pd.DataFrame()
        self.worker_no = worker_no
        self.factor_list = [fac() for fac in factor_list]
        # self.kafka = Kafka_producer('test')
        self.sample_flag = False
        # assert isfunction(calculation_callback), "请传入因子计算的回调函数calculation_callback！"
        self.calculation_mode = calculation_mode
        self.data_input_mode = data_input_mode
        self.data_mode = ''
        self.security_type = security_type
        self.calc_callback = calc_callback
        if self.factor_list:
            self.calc_params = parse_callback_params(self.calc_callback, True)
        else:
            self.calc_params = parse_callback_params(self.calc_callback, False)
        self.verbose = verbose
        self.playback_or_realtime = playback_or_realtime
        self.security_type_dict = security_type_dict

        if {'TICK_SAMPLE', 'TRANSACTION_SAMPLE', 'ORDER_SAMPLE'}.intersection(
                {i.upper() for i in data_input_mode}) or calculation_mode == 'alarm':
            self.sample_flag = True
            self.tick_sample_interval = tick_sample_interval
            self.wait_time = self.tick_sample_interval  # 定时计算的时间间隔和采样间隔相同

        self.start(stock_list, serverAddr, calculation_mode, auto_exit, auto_exit_time)

    def start(self, stock_list, serverAddr="/tmp/test_unix.sock",
              calculation_mode='alarm', auto_exit=True, auto_exit_time = 153000000):
        self.security_list = stock_list
        self.main_stock = stock_list[0]#第一次传入的标的是主标的，即使change stock也不会再变化
        self.actor_name = '{}-{}'.format(self.main_stock, str(os.getpid()))
        self.logger = setup_logging("ray_processor_{}".format(self.actor_name))

        errors = []
        if type(stock_list) != list:
            errors.append("stock_list 必须为list.")
        if calculation_mode.lower() not in ["tick", "alarm"]:
            errors.append(
                "calculation_mode只支持TICK（接收到tick行情后触发计算）和ALARM（按tick_sample_interval定时触发计算两种模式）！")
        if not self.calc_callback:
            errors.append('请传入回调计算方法calc_callback')
        if self.playback_or_realtime == 'playback' and calculation_mode.lower() == 'alarm':
            errors.append('playback模式calculation_mode不能为alarm')
        if errors:
            for error in errors:
                self.logger.error(error)
            os.killpg(os.getpgid(os.getpid()), signal.SIGINT)

        self.task_queue = Queue()  # 任务队列
        self.his_price = {}
        self.his_count = {}
        self.past_count = {}
        self.df_dict = {}
        self.df_dict_last_batch = {}
        self.market_type_modes = {}
        self.__get_market_type_modes()
        self.__build_data_structure()
        self.calc_df = pd.DataFrame()  # 存储每个因子的计算结果
        self.calc_results_flag = []  # 存储每次因子计算的结果是否成功
        self.serverAddr = serverAddr
        self.new_socket_client = None
        self.auto_exit = auto_exit
        self.exit_time = auto_exit_time
        self.last_mdtime = 0

        # 独立线程消费行情
        t1 = threading.Thread(target=self.__on_receive_market_data,
                              daemon=True)
        t1.start()
        # 单独线程定时计算
        if calculation_mode.lower() == 'alarm':
            self.logger.info('alarm计算模式下,定时计算开始：计算间隔tick_sample_interval为{}'.format(str(self.tick_sample_interval)))
            t2 = threading.Thread(target=self.calculation_by_time, daemon=True)
            t2.start()
        else:
            self.logger.info(
                'tick计算模式下,触发式计算开始：每次接收到第一只票{}的行情即开始计算'.format(
                    str(self.main_stock)))


    @retry(stop_max_attempt_number=5, wait_fixed=2000)
    def send_uds_message(self, client_sock, data):
        if (self.auto_exit and (self.last_mdtime > self.exit_time)):
            self.logger.info('exit succeed')
            os.killpg(os.getpgid(os.getpid()), signal.SIGINT)
        size = len(data).to_bytes(5, byteorder='big')
        stock_list_str = data.encode('ascii')
        client_sock.send(size)
        client_sock.send(stock_list_str)
        self.logger.info(
            "regist success and send actor name: {}!".format(self.actor_name))

    def __get_market_type_modes(self):
        has_tick_mode = False
        has_transaction_mode = False
        has_order_mode = False
        for mode in self.data_input_mode:
            if mode in ['TICK_RAW', 'TICK_SAMPLE', 'KLINE1M_RAW']:
                if has_tick_mode:
                    self.logger.error(
                        '只能选择TICK_RAW, TICK_SAMPLE, KLINE1M_RAW中的一种模式')
                    os.killpg(os.getpgid(os.getpid()), signal.SIGINT)
                has_tick_mode = True
            if mode in ['TRANSACTION_RAW', 'TRANSACTION_SAMPLE']:
                if has_transaction_mode:
                    self.logger.error(
                        '只能选择TRANSACTION_RAW, TRANSACTION_SAMPLE中的一种模式')
                    os.killpg(os.getpgid(os.getpid()), signal.SIGINT)
                has_transaction_mode = True
            if mode in ['ORDER_RAW', 'ORDER_SAMPLE']:
                if has_order_mode:
                    self.logger.error('只能选择ORDER_RAW, ORDER_SAMPLE中的一种模式')
                    os.killpg(os.getpgid(os.getpid()), signal.SIGINT)
                has_order_mode = True
        for mode in self.data_input_mode:
            mode = transform_datamode(mode)
            if mode in [DataCollectMode.TICK_RAW, DataCollectMode.TICK_SAMPLE]:
                if isinstance(self.security_type, list):
                    for s_type in self.security_type:
                        self.data_mode = 'tick'
                        self.market_type_modes[s_type] = mode
                else:
                    self.data_mode = 'tick'
                    self.market_type_modes[self.security_type] = mode
            else:
                if mode == DataCollectMode.KLINE1M_RAW:
                    market_type = 'kline1m'
                    self.data_mode = 'kline1m'
                elif mode == DataCollectMode.TRANSACTION_RAW:
                    market_type = "transaction"
                elif mode == DataCollectMode.TRANSACTION_SAMPLE:
                    market_type = "transaction"
                elif mode == DataCollectMode.ORDER_RAW:
                    market_type = "order"
                elif mode == DataCollectMode.ORDER_SAMPLE:
                    market_type = "order"
                else:
                    self.logger.error("DataCollectMode不支持此枚举类型: {}！".format(mode))
                    os.killpg(os.getpgid(os.getpid()), signal.SIGINT)

                self.market_type_modes[market_type] = mode

    def __build_data_structure(self):
        self.__build_df_dict()
        self.__build_df_dict_last_batch()
        self.__build_his_data()

    def __build_df_dict(self):
        """
        初始化存储行情数据的数据结构
        """
        for security_id in self.security_list:
            if security_id not in self.df_dict:
                self.df_dict[security_id] = {}
                for market_type, mode in self.market_type_modes.items():
                    self.df_dict[security_id][market_type] = pd.DataFrame()
                    if (market_type in self.security_type and market_type == self.security_type_dict.get(security_id)) or (market_type == self.security_type) or market_type == 'kline1m':
                        self.df_dict[security_id][self.data_mode] = \
                        self.df_dict[security_id][market_type]

        for market_type, mode in self.market_type_modes.items():
            if market_type not in self.df_dict:
                self.df_dict[market_type] = pd.DataFrame()
                if (market_type in self.security_type) or (market_type == self.security_type) or market_type == 'kline1m':
                    self.df_dict[self.data_mode] = self.df_dict[market_type]

    def __build_df_dict_last_batch(self):
        """
        初始化存储行情数据最后一条数据
        """
        for security_id in self.security_list:
            if security_id not in self.df_dict_last_batch:
                self.df_dict_last_batch[security_id] = {}
                for market_type, mode in self.market_type_modes.items():
                    self.df_dict_last_batch[security_id][
                        market_type] = pd.DataFrame()
                    if (market_type in self.security_type and market_type == self.security_type_dict.get(security_id)) or (market_type == self.security_type) or market_type == 'kline1m':
                        self.df_dict_last_batch[security_id][self.data_mode] = \
                        self.df_dict_last_batch[security_id][market_type]

    def __build_his_data(self):
        """
        初始化实时数据存储结构
        """
        data_types = ['mdStock', 'mdFund', 'mdTransaction', 'mdOrder',
                      'mdKLine']
        for security_id in self.security_list:
            if security_id not in self.his_price:
                self.his_price[security_id] = {}
                self.his_count[security_id] = {}
                self.past_count[security_id] = {}
                for data_type in data_types:
                    self.his_price[security_id][data_type] = []
                    self.his_count[security_id][data_type] = 0
                    self.past_count[security_id][data_type] = 0

    def __on_receive_market_data(self):
        self.client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.client_sock.connect(self.serverAddr)
        stock_list_str = (',').join(self.security_list)
        data = '{}:{}'.format(self.actor_name, stock_list_str)
        self.send_uds_message(self.client_sock, data)  # 发送行情订阅请求

        while True:
            size = self.client_sock.recv(5)
            if not size:
                if self.new_socket_client:
                    self.client_sock.close()
                    self.client_sock = self.new_socket_client
                    self.new_socket_client = None
                    continue
                else:
                    self.logger.info("finish")
                    break
            size = int.from_bytes(size, byteorder='big')
            t1 = int(self.client_sock.recv(size))
            size = self.client_sock.recv(5)
            size = int.from_bytes(size, byteorder='big')
            ma = self.client_sock.recv(size)

            marketdata = MarketData_pb2.MarketData()
            marketdata.ParseFromString(ma)

            data_type = ''
            if marketdata.HasField("mdStock"):
                data_type = 'mdStock'
                self.last_mdtime = marketdata.mdStock.MDTime
            elif marketdata.HasField("mdFund"):
                data_type = 'mdFund'
                self.last_mdtime = marketdata.mdFund.MDTime
            elif marketdata.HasField("mdKLine"):
                data_type = 'mdKLine'
                self.last_mdtime = marketdata.mdKLine.MDTime
            elif marketdata.HasField("mdTransaction"):
                data_type = 'mdTransaction'
            elif marketdata.HasField("mdOrder"):
                data_type = 'mdOrder'
            else:
                self.logger.info(
                    "unknow marketdata type: {}.".format(marketdata))

            if (self.auto_exit and (self.last_mdtime > self.exit_time)):
                self.logger.info('exit succeed')
                os.killpg(os.getpgid(os.getpid()), signal.SIGINT)

            if data_type:
                security_id = getattr(marketdata, data_type).HTSCSecurityID
                ma_json = MessageToJson(getattr(marketdata, data_type))
                t2 = round(time.time() * 100000)
                if self.verbose >= 30:
                    self.logger.info(
                        "receive marketdata {}: HTSCSecurityID:{}, MDTime: {}, time cost: {}ms.".format(
                            data_type, security_id,
                            getattr(marketdata, data_type).MDTime, (t2 - t1) / 100.0))

                self.his_price[security_id][data_type].append(ma_json)
                self.his_count[security_id][data_type] += 1

            if self.calculation_mode.lower() == "tick" and (
                    marketdata.HasField("mdStock") or marketdata.HasField(
                "mdFund") or marketdata.HasField(
                "mdKLine")) and data_type and security_id == self.main_stock:
                calc_result_flag = self.calculation()
                self.calc_round += 1
                self.calc_results_flag.append(calc_result_flag)

    def calculation_by_time(self):
        while True:
            if datetime.datetime.now().second == 0:
                break
        last_time = self.tick_sample_interval
        while True:
            if last_time >= self.tick_sample_interval:
                pass
            else:
                time.sleep(self.tick_sample_interval - last_time)
            last_time = 0
            t1 = time.time()
            calc_result_flag = self.calculation()
            last_time = time.time() - t1 + last_time
            self.calc_round += 1
            self.calc_results_flag.append(calc_result_flag)

    def __get_market_data(self, data_type, security_id, increment=True):
        if data_type.lower() not in ['stock', 'fund', 'transaction', 'order',
                                     'kline1m']:
            self.logger.error('类型必须为stock,fund,transaction,order或kline1m')
            os.killpg(os.getpgid(os.getpid()), signal.SIGINT)
        if data_type.lower() != 'kline1m':
            data_type = 'md' + data_type.capitalize()
        else:
            data_type = 'mdKLine'
        data = self.his_price[security_id][data_type]
        his_count = self.his_count[security_id][data_type]
        past_count = self.past_count[security_id][data_type]
        if increment:
            # 可能增量数据为空
            data = data[past_count:his_count]  # 取增量数据
        self.past_count[security_id][data_type] = his_count
        df = pd.read_json("[" + ",".join(data) + "]", dtype=np.float)
        return df

    def get_calc_df(self):
        return self.calc_df

    def send_kafka(self):
        produceTime = time.strftime("%Y-%m-%d %H:%M:%S",
                                    time.localtime(time.time()))
        value = {
            "his_{}_count".format(self.data_mode): self.his_count.get('fund'),
            "past_{}_count".format(self.data_mode): self.past_count.get(
                'fund'),
            "his_transation_count": self.his_count.get('transaction'),
            "his_order_count": self.his_count.get('order'),
            "produceTime": produceTime}  # self.kafka.send_json_data(value)

    def calculation(self):
        """
        接收到tick行情后，触发calculation计算，返回值存放到self.calc_df
        :param his_tick: 截止此刻的历史tick数据
        :param his_transaction: 截止此刻的历史transaction数据
        :param his_order: 截止此刻的历史order数据
        :return:
        """
        try:
            # 处理行情数据
            for security_id in self.security_list:
                for market_type, mode in self.market_type_modes.items():
                    t1 = time.time()
                    df_dict_last_batch = copy.copy(self.df_dict_last_batch[security_id][market_type])
                    data = self.__get_market_data(market_type, security_id, increment=True)
                    if self.verbose >= 10:
                        self.logger.info(
                            "parsing time: {}s, {}-{} shape: {}. ".format(time.time() - t1, security_id, market_type, data.shape))
                    t1 = time.time()
                    if data.empty:
                        continue
                    self.df_dict_last_batch[security_id][market_type] = data
                    if mode == DataCollectMode.TICK_SAMPLE:
                        data = data.append(df_dict_last_batch,
                                           sort=False)  # 跟上一次采样计算的数据合并，保证采样时间区间的数据完整性
                        if isinstance(self.security_type, list):
                            security_type = self.security_type_dict.get(security_id)
                        else:
                            security_type = self.security_type
                        data = realtime_data_aux(data,
                                                 self.tick_sample_interval, security_type)
                    if mode == DataCollectMode.TRANSACTION_SAMPLE:
                        data = data.append(df_dict_last_batch,
                                           sort=False)  # 跟上一次采样计算的数据合并，保证采样时间区间的数据完整性
                        data = sample_transaction_data(data,
                                                       self.tick_sample_interval)
                    if mode == DataCollectMode.ORDER_SAMPLE:
                        data = data.append(df_dict_last_batch,
                                           sort=False)  # 跟上一次采样计算的数据合并，保证采样时间区间的数据完整性
                        data = sample_orderbook(data,
                                                self.tick_sample_interval)
                    if data.empty:
                        continue

                    if mode in [DataCollectMode.TICK_SAMPLE,
                                DataCollectMode.TRANSACTION_SAMPLE,
                                DataCollectMode.ORDER_SAMPLE]:
                        if self.df_dict[security_id][market_type].empty:
                            self.df_dict[security_id][market_type] = pd.concat(
                                [self.df_dict[security_id][market_type], data],
                                ignore_index=False, copy=False)
                        else:
                            # 更新最近的一次采样行情
                            check_index = \
                            self.df_dict[security_id][market_type].index[-1]
                            update_df = data[data.index == check_index]
                            if not update_df.empty:
                                if market_type == 'transaction':
                                    if (update_df.loc[
                                            check_index, 'buy_aux_count'][
                                            'sum'] > self.df_dict[security_id][
                                            market_type].loc[
                                            check_index, 'buy_aux_count'][
                                            'sum']) or (update_df.loc[
                                                            check_index, 'sell_aux_count'][
                                                            'sum'] >
                                                        self.df_dict[
                                                            security_id][
                                                            market_type].loc[
                                                            check_index, 'sell_aux_count'][
                                                            'sum']):
                                        # 避免误更新
                                        self.df_dict[security_id][
                                            market_type].update(update_df,
                                                                overwrite=True)
                                else:
                                    self.df_dict[security_id][
                                        market_type].update(update_df,
                                                            overwrite=True)
                            # 追加最新的采样行情
                            append_df = data[data.index >
                                             self.df_dict[security_id][
                                                 market_type].index[-1]]
                            self.df_dict[security_id][market_type] = \
                            self.df_dict[security_id][market_type].append(
                                append_df, sort=False)
                    else:
                        self.df_dict[security_id][market_type] = pd.concat(
                            [self.df_dict[security_id][market_type], data],
                            ignore_index=False, copy=False, sort = False)

                    if security_id == self.main_stock:
                        self.df_dict[market_type] = self.df_dict[security_id][market_type]

                    if (market_type in self.security_type and market_type == self.security_type_dict.get(security_id)) or (market_type == self.security_type) or market_type == 'kline1m':
                        # 每支标的外层tick或kline1m数据同步
                        self.df_dict[security_id][self.data_mode] = self.df_dict[security_id][market_type]
                        self.df_dict_last_batch[security_id][self.data_mode] = self.df_dict_last_batch[security_id][market_type]
                        if security_id == self.main_stock:
                            # 主票外层tick或kline1m数据同步
                            self.df_dict[self.data_mode] = self.df_dict[market_type]

                    if self.verbose >= 10:
                        self.logger.info(
                            "sampling time: {}s, {}-{} shape: {}. ".format(time.time() - t1, security_id, market_type, data.shape))

            if self.df_dict[self.data_mode].empty:
                self.logger.warning("暂未获取到交易时段行情数据，计算未开始。")
                return True

        except Exception as e:
            if self.verbose > 0:
                self.logger.error(traceback.print_exc())
            else:
                self.logger.error("error parsing marketdata：{}".format(e))

        try:
            t1 = time.time()
            df_dict_iter = copy.copy(self.df_dict)

            if not self.factor_list:
                self.calc_callback(self, df_dict_iter, **self.calc_params)
                if self.verbose >= 10:
                    self.logger.info("calculating calc_callback time:{}s.".format(time.time() - t1,))
            else:
                result_df = self.calc_callback(self, self.factor_list, df_dict_iter, **self.calc_params)
                # self.calc_df = self.calc_df.update(result_df, overwrite = True)#更新k值
                keep_index = self.calc_df.index.difference(result_df.index)
                # update_idx = result_df.index.intersection(self.calc_df.index).append(result_df.index.difference(self.calc_df.index))
                self.calc_df = self.calc_df.loc[keep_index].append(result_df, sort=False)
                if self.verbose >= 10:
                    self.logger.info("calculating calc_callback time: {}s. calc_df shape:{}.".format(time.time() - t1, result_df.shape))
            try:
                self.send_kafka()
                if self.verbose >= 20:
                    self.logger.info("finish calculation, now saving df_dict and calc_df...")
                    pickle.dump(self.df_dict, open("df_dict1_{}.pkl".format(self.main_stock), "wb"))
                    pickle.dump(self.calc_df, open("calc_df1_{}.pkl".format(self.main_stock), "wb"))
            except Exception as e:
                if self.verbose > 0:
                    self.logger.error(traceback.print_exc())
                else:
                    self.logger.error("error sending kafka：{}".format(e))
        except Exception as e:
            if self.verbose > 0:
                self.logger.error(traceback.print_exc())
            else:
                self.logger.error("error excuting calc_callback: {}, please check calc_callback!".format(e))
        return True

    def change_stocks(self, security_list):
        if self.playback_or_realtime == 'playback':
            self.logger.error('playback模式无法改变订阅标的')
            os.killpg(os.getpgid(os.getpid()), signal.SIGINT)
        if type(security_list) != list:
            self.logger.error('security_list必须为list')
            os.killpg(os.getpgid(os.getpid()), signal.SIGINT)
        old_client_sock = self.client_sock
        client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_sock.connect(self.serverAddr)
        self.new_socket_client = client_sock
        self.security_list = security_list
        self.security_list.insert(0, self.main_stock)
        # 将主票添加到更换标的列表的第一个，以便持续订阅主票
        # self.main_stock = security_list[0]
        self.__build_data_structure()
        stock_list_str = (',').join(self.security_list)
        data = '{}:{}'.format(self.actor_name, stock_list_str)
        self.send_uds_message(client_sock, data)


if __name__ == "__main__":

    # from SmartFactor.factors import pxchange
    # from SmartFactor import get_custom_factor_class
    # pxchange = get_custom_factor_class(pxchange.pxchange, {"custom_params":{"interval_seconds": 60, "sample_period": 3}})
    # print(pxchange)

    def calc_callback(self, factor_list, df_dict, **kwargs):
        """
        实时行情计算回调函数，可利用入参自定义计算因子数据，以后执行后续的模型预测、信号发送等逻辑
        :param self, StreamCalcActor对象，可以获取self.logger日志对象,也可以添加用户自定义的变量，如模型等。
        :param factor_list: list，表示需要计算的因子列表，每个元素代表一个因子类fac，可调用fac.calc方法计算因子
        :param df_dict: 开盘以来累计接收到的全部行情数据，可按自定义窗口截取行情数据，用于计算因子
        :return:
        """
        if not hasattr(self, 'model'):
            from keras.models import \
                load_model  # 可选步骤一：加载自定义的模型用于数据预测  # self.model = load_model('/home/appadmin/xxx_model')
        # 可选步骤二：自定义选取因子计算需要依赖的窗口大小
        window = 60  # 依赖前60个行情数据
        for key in df_dict.keys():
            df_dict[key] = df_dict["tick"].iloc[-window:]
        # 关键步骤：计算因子数据，并返回因子数据的DataFrame
        result_list = []
        for i in range(10):
            for fac in factor_list:
                try:
                    tmp_series = fac.calc(df_dict, 0, fac.custom_params)
                    tmp_series.rename(fac.factor_name, inplace=True)
                    result_list.append(tmp_series)
                except Exception as e:
                    result_list.append(pd.Series([], name=fac.factor_name))
                    if self.verbose > 0:
                        # self.verbose可设置不同的日志级别
                        self.logger.error(traceback.print_exc())
                    else:
                        self.logger.error(e)
        calc_df = pd.concat(result_list, axis=1)
        pickle.dump(calc_df, open("calc_df_tmp.pkl", "wb"))  # 可缓存数据，方便调试
        return calc_df


    # 定义需要计算的因子列表
    factor_list = ["pxchange", "TotalBuySellOrderQtyMinus", "order_dispersion",
                   "cor_px_vol", "px_vol_corr_slope",
                   "px_to_high_premium_discount", "sell_buy_qty_spread", "rsi",
                   "roc"]  # ]""roll_measure_autocorr"]#"",
    calc_date = "20201221"
    security_list = [["159915.SZ"], ["159958.SZ"]]  # ["159915.SZ"]
    security_type = "fund"
    data_input_mode = ["TRANSACTION_SAMPLE", "TICK_SAMPLE"]
    # run_realtime_calculation_by_securities新增**kwargs可变参数
    run_realtime_calculation_by_securities(factor_list,
                                           data_input_account="013150",
                                           data_input_mode=data_input_mode,
                                           security_list=security_list,
                                           calculation_mode="tick",
                                           playback_or_realtime="playback",
                                           file_path='../factors/',
                                           num_cpus=None,
                                           object_store_memory=None,
                                           options={"local_mode": False},
                                           calc_callback=calc_callback,
                                           verbose=40)

