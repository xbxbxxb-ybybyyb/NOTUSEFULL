from insight.model import MarketData_pb2 as MarketData_pb2
from insight.model import MDPlayback_pb2 as MDPlayback
from insight.model import EMarketDataType_pb2 as EMarketDataType
from insight.model import ESecurityIDSource_pb2 as ESecurityIDSource
from insight.model import ESecurityType_pb2 as ESecurityType
from insight.model import MDSubscribe_pb2 as MDSubscribe
from insight.model import MDPlayback_pb2 as MDPlayback_pb2
from insight.interface import mdc_gateway_interface as mdc_gateway_interface

from insight.data_handle import OnRecvMarkertDataBase
from insight import utils
import time
from tquant.utils.event_trace import event_trace


class OnRecvMarkertData(OnRecvMarkertDataBase):
    def __init__(self):
        pass

    def OnMarketData(self, marketdata: MarketData_pb2.MarketData):
        ##处理订阅的实时行情数据
        try:
            if marketdata.marketDataType == EMarketDataType.MD_TICK:  # .MD_TICK 快照
                if marketdata.HasField("mdStock"):  # 股票
                    print(
                        "HTSCSecurityID=%s MDTime=%s" % (marketdata.mdStock.HTSCSecurityID, marketdata.mdStock.MDTime))
                elif marketdata.HasField("mdIndex"):  # 指数
                    print("HTSCSecurityID=%s lastprice=%d" % (
                        marketdata.mdIndex.HTSCSecurityID, marketdata.mdIndex.LastPx))
                elif marketdata.HasField("mdBond"):  # 债券
                    print(
                        "HTSCSecurityID=%s lastprice=%d" % (marketdata.mdBond.HTSCSecurityID, marketdata.mdBond.LastPx))
                elif marketdata.HasField("mdFund"):  # 基金
                    print(
                        "HTSCSecurityID=%s lastprice=%d" % (marketdata.mdFund.HTSCSecurityID, marketdata.mdFund.LastPx))
                elif marketdata.HasField("mdOption"):  # 期权
                    print("HTSCSecurityID=%s lastprice=%d" % (
                        marketdata.mdOption.HTSCSecurityID, marketdata.mdOption.LastPx))
            elif marketdata.marketDataType == EMarketDataType.MD_TRANSACTION:  # .MD_TRANSACTION:逐笔成交
                if marketdata.HasField("mdTransaction"):
                    print(marketdata.mdTransaction)
            elif marketdata.marketDataType == EMarketDataType.MD_ORDER:  # .MD_ORDER:逐笔委托
                if marketdata.HasField("mdOrder"):
                    print(marketdata.mdOrder)
            elif marketdata.marketDataType == EMarketDataType.MD_CONSTANT:  # .MD_CONSTANT:静态信息
                if marketdata.HasField("mdConstant"):
                    print(marketdata.mdConstant.HTSCSecurityID)
                # MD_KLINE:实时数据只提供15S和1MIN K线
            elif marketdata.marketDataType == EMarketDataType.MD_KLINE_15S or marketdata.marketDataType == EMarketDataType.MD_KLINE_1MIN or marketdata.marketDataType == EMarketDataType.MD_KLINE_5MIN or marketdata.marketDataType == EMarketDataType.MD_KLINE_15MIN or marketdata.marketDataType == EMarketDataType.MD_KLINE_30MIN or marketdata.marketDataType == EMarketDataType.MD_KLINE_60MIN or marketdata.marketDataType == EMarketDataType.MD_KLINE_1D:
                if marketdata.HasField("mdKLine"):
                    print(marketdata.mdKLine.HTSCSecurityID, marketdata.mdKLine.MDTime)
            elif marketdata.marketDataType == EMarketDataType.MD_TWAP_1S or marketdata.marketDataType == EMarketDataType.MD_TWAP_1MIN:  # .TWAP:TWAP数据
                if marketdata.HasField("mdTwap"):
                    print(marketdata.mdTwap)
            elif marketdata.marketDataType == EMarketDataType.MD_VWAP_1S or marketdata.marketDataType == EMarketDataType.MD_VWAP_1MIN:  # .VWAP:VWAP数据
                if marketdata.HasField("mdVwap"):
                    print(marketdata.mdVwap)
            elif marketdata.marketDataType == EMarketDataType.AD_FUND_FLOW_ANALYSIS:  # .AD_FUND_FLOW_ANALYSIS:
                if marketdata.HasField("mdFundFlowAnalysis"):
                    print(marketdata.mdFundFlowAnalysis)
            elif marketdata.marketDataType == EMarketDataType.MD_ETF_BASICINFO:  # .MD_ETF_BASICINFO:ETF成分股信息
                if marketdata.HasField("mdETFBasicInfo"):
                    print(marketdata.mdETFBasicInfo)

        except BaseException as e:
            print("onMarketData error happended!")
            print(e)

    def OnPlaybackPayload(self, playload: MDPlayback_pb2.PlaybackPayload):
        # 处理订阅的回放行情数据
        try:
            utils.interface.set_service_value(4)
            print("Parse Message id:" + playload.taskId)
            marketDataStream = playload.marketDataStream;
            print("OnPlaybackPayload total number=%d, serial=%d, isfinish=%d" % (
                marketDataStream.totalNumber, marketDataStream.serial,
                marketDataStream.isFinished));
            marketDataList = marketDataStream.marketDataList
            marketDatas = marketDataList.marketDatas
            for data in marketDatas:
                time.sleep(10)
                self.OnMarketData(data)
        except BaseException as e:
            print(e)


class InsightSample:
    """
    InsightSmaple，Insight示例类

    params:
    user_id: 用户id，类型str
    callback: 行情处理回调类。类型OnRecvMarkertData，默认为None则使用示例回调基类
    open_trace: 是否打开流量日志开关，类型bool，默认True
    open_file_log: 是否打开本地日志文件开关，类型bool，默认True
    open_cout_log: 是否打开控制台输出开关，类型bool，默认True
    """
    def __init__(self, user_id, callback=None, open_trace=True, open_file_log=True, open_cout_log=True):
        # 流量与日志开关设置
        # open_trace trace流量日志开关 # params:open_file_log 本地日志文件开关  # params:open_cout_log 控制台日志开关
        utils.get_interface().init(open_trace, open_file_log, open_cout_log)

        # 若回调类为空则使用默认示例回调类
        if callback is not None:
            if not isinstance(callback, OnRecvMarkertData):
                raise Exception("回调类必须继承自OnRecvMarkertData")
        else:
            callback = OnRecvMarkertData()
        # 注册回调接口，不注册无法接收数据、处理数据。订阅不同类型的行情，必须实现指定的回调接口。
        utils.get_interface().setCallBack(callback)
        # 2.接管日志
        # 若想关闭系统日志,自我处理日志,打开本方法
        # 打开本方法后,日志在insightlog.py的PyLog类的方法log(self,line)中也会体现,其中 line为日志内容）
        # use_init = True 系统日志以 utils.get_interface().init 配置的方式记录
        # use_init = False 系统不再记录或打印任何日志,日志只有自行处理部分处理
        ### 以下是示例 ###
        # use_init = True
        # utils.get_interface().own_deal_log(use_init)
        utils.login(user_id)

    def __del__(self):
        utils.fini()

    @event_trace
    def subscribe_by_type(self, security_type=ESecurityType.StockType, data_type=EMarketDataType.MD_KLINE_1MIN):
        """
        按类型订阅
        :param security_type: 标的订阅的类型，ESecurityType的枚举值
        :param data_type: 订阅数据的类型，EMarketDataType的枚举值
        :return: None
        """
        # 订阅行情接口调用，调用回调类中的OnMarketData方法
        # params1: ESecurityIDSource枚举值 --行情源
        # security_type: ESecurityType的枚举值 --证券品种类型
        # data_type: EMarketDataType的枚举值集合 --行情数据类型

        # 沪深 - 股票
        element0 = mdc_gateway_interface.Element(ESecurityIDSource.XSHE, security_type, [data_type])
        element1 = mdc_gateway_interface.Element(ESecurityIDSource.XSHG, security_type, [data_type])

        securitylist = [element0, element1]
        # MDSubscribe.COVERAGE模式，覆盖上一次的订阅内容
        action_type = MDSubscribe.COVERAGE
        utils.get_interface().subscribeByType(action_type, securitylist)
        utils.sync()

    # 盘中回放接口 --securitylist 和 securityIdList取并集
    # Can only query data for one day
    @event_trace
    def play_back_oneday(self, stock_list, start_time, stop_time, data_type=EMarketDataType.MD_KLINE_1MIN, sort=False):
        """
        :param stock_list: security_id_list 为 标的str集合
        :param start_time: 为 str,注意格式
        :param stop_time: 为 str,注意格式
        :param data_type: EMarketDataType的枚举值
        :param sort: 是否对所有数据按mdtime排序
        :return:
        """
        # 回放行情接口调用，调用回调类中的OnPlaybackPayload方法
        string_list = mdc_gateway_interface.StrList()
        for stock in stock_list:
            string_list.Add(stock)

        exrights_type = MDPlayback.NO_EXRIGHTS
        utils.get_interface().playSortCallback(string_list, start_time, stop_time, data_type, exrights_type, sort)


if __name__ == "__main__":
    callback = OnRecvMarkertData()
    insight = InsightSample(user_id='013150', callback=callback)
    # insight.subscribe_by_type()#订阅实时行情数据
    insight.play_back_oneday(stock_list=["601688.SH", "000016.SZ"], start_time="20190924000000", stop_time="20190924235959")#回放历史行情数据

