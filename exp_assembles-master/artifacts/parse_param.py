
def parse_target_type(label_name):
    target_type = None
    if label_name.startswith("LabelFirstPeak"):
        target_type = "mid"
    elif label_name.startswith("LabelLong") or  label_name.startswith("LabelShort"):
        target_type = "longshort"
    elif "short_ret" in  label_name or "long_ret" in label_name:
        target_type = "longshort"
    elif "ask2ask" in  label_name:
        target_type = "ask1"
    elif "bid2bid" in  label_name:
        target_type = "bid1"
    else:
        raise Exception("无法识别target_type!", label_name)
    return target_type


def parse_winloss_columns(label_name):
    if "Long" in label_name:
        plot_columns = ['涨日均个数', '涨总体止盈率', '涨总体平率', '涨总体止损率', "信号质量加权"]
    elif "Short" in label_name:
        plot_columns = ['跌日均个数', '跌总体止盈率', '跌总体平率', '跌总体止损率', "信号质量加权"]
    elif "short_ret" in  label_name:
        plot_columns = ['跌日均个数', '跌总体止盈率', '跌总体平率', '跌总体止损率', "信号质量加权"]
    elif "long_ret" in label_name:
        plot_columns = ['涨日均个数', '涨总体止盈率', '涨总体平率', '涨总体止损率', "信号质量加权"]
    elif "ask2ask" in  label_name:
        plot_columns = ['涨跌日均个数', '涨跌总体止盈率', '涨跌总体平率', '涨跌总体止损率', "信号质量加权"]
    elif "bid2bid" in  label_name:
        plot_columns = ['涨跌日均个数', '涨跌总体止盈率', '涨跌总体平率', '涨跌总体止损率', "信号质量加权"]
    else:
        plot_columns = ['涨跌日均个数', '涨跌总体止盈率', '涨跌总体平率', '涨跌总体止损率', "信号质量加权", '涨跌日均止盈率', '涨跌日均平率', '涨跌日均止损率']
    return plot_columns



import pandas as pd
import datetime as dt
import os
import json
from dataclasses import dataclass
from artifacts import exp_artifacts, model_save_and_evaluate
from xquant.xqutils.perf_profile import profile

@dataclass
class BackTestParams:
    # 解析artifacts结构信号和回测目录
    strategy_name:str # 策略名称
    exp_name:str
    version_alias:str
    label_name:str
    pred_up:float # 信号涨阈值
    pred_dw:float # 信号跌阈值
    start_date: str # 回测开始日期
    end_date:str # 回测结束日期
    # 策略参数
    strategy_params:dict
    timeframe:str = "TICK" #EnhancedTick
    online_or_research_path: bool = False # 为True使用线上信号路径，为False使用研究信号
    research_exp_path:str = "/dfs/group/800657/exp_results"
    online_exp_path:str = "/data/user/016869/AutoMiningFrame/trade_data/COO/"
    online_signal_file_format = "{exp_name}/signal_files/{label_name}-{stock}.parquet" # online信号需要参数指定exp_name
    research_signal_file_format = "{exp_name}/{version_alias}/signal_files/{label_name}-{stock}.parquet" # research信号需要参数指定exp_name, version_alias, label_name
    signal_process_dir:str = None # 处理后的信号文件目录
    backtest_result_dir:str = None # 存储回测结果的目录

    def __init__(self, online_or_research_path, strategy_name, exp_name, start_date, end_date, version_alias = None, label_name = None, pred_up = None, pred_dw = None):
        self.online_or_research_path = online_or_research_path
        self.strategy_name = strategy_name
        self.exp_name = exp_name
        self.version_alias = version_alias
        self.label_name = label_name
        self.pred_up = pred_up
        self.pred_dw = pred_dw
        self.start_date = start_date
        self.end_date = end_date
        if self.online_or_research_path:
            self.backtest_result_dir = os.path.join(self.online_exp_path, exp_name, "backtest_result",
                                                    self.strategy_name)

        else:
            self.backtest_result_dir = os.path.join(self.research_exp_path, exp_name, version_alias, "backtest_result",
                                                    self.strategy_name)

    def _get_dynamic_str(self, src_str):
        dst_str = "f\"" + src_str + "\""
        return dst_str

    def _check_signal_path(self):
        if not self.signal_process_dir:
            raise Exception("请先调用get_signal_path方法拼接信号路径！")
        if not os.path.exists(self.signal_process_dir):
            print("ERRRO: signal_process_path_dir does not exist！", self.signal_process_dir)
            return False
        return True


    def _get_signal_path_online(self, exp_name, stock, pred_th_up, pred_th_dw, label_name = None, process_signal = True):
        signal_dir = os.path.join(self.online_exp_path, exp_name, "mm_ai_signal/online", f"{stock}")
        threshold_path = os.path.join(self.online_exp_path, exp_name, exp_name, "threshold.json")
        threshold_dict = json.load(open(threshold_path, "r"))
        self.pred_up = threshold_dict[stock]["longPredTh"]
        self.pred_dw = threshold_dict[stock]["shortPredTh"]
        if process_signal:
            # parquet_path = os.path.join(self.online_exp_path, eval(self._get_dynamic_str(self.online_signal_file_format)))
            # parquet_dir = os.path.dirname(parquet_path)
            # if not label_name or not os.path.exists(parquet_path):
            #     for f in os.listdir(parquet_dir):
            #         if stock in f:
            #             parquet_path =  os.path.join(parquet_dir, f)
            #             break
            # if not os.path.exists(parquet_path):
            #     raise Exception("无该标的的信号文件！{}".format(parquet_path))
            signal_df_load = pd.read_parquet(parquet_path)
            # 存储该阈值信号文件
            model_save_and_evaluate.model_signal_process_long_short_pred_th_classify(signal_df_load,
                                                                                     pred_th_up=pred_th_up,
                                                                                     pred_th_dw=pred_th_dw,
                                                                                     symbol=stock,
                                                                                     signal_process_base_dir=signal_dir)
        print("INFO: online signal_dir: {}, pred_up {}, pred_dw {}.".format(signal_dir, self.pred_up, self.pred_dw))
        self.signal_process_dir = signal_dir
        os.makedirs(self.backtest_result_dir, exist_ok=True)
        return signal_dir


    def _get_signal_path_research(self, exp_name, version_alias, stock, pred_th_up, pred_th_dw, label_name, process_signal = True):
        parquet_path = os.path.join(self.research_exp_path, eval(self._get_dynamic_str(self.research_signal_file_format)))
        parquet_dir = os.path.dirname(parquet_path)
        if not label_name or not os.path.exists(parquet_path):
            for f in os.listdir(parquet_dir):
                if stock in f:
                    parquet_path =  os.path.join(parquet_dir, f)
                    label_name = f.split("-")[0]
                    break
        if not os.path.exists(parquet_path):
            raise Exception("无该标的的信号文件！{}".format(parquet_path))
        expa = exp_artifacts.ExpArtifacts(exp_name=exp_name,  exp_base = "/dfs/group/800657/exp_results")
        signal_dir = expa.path_of_signal_process_save(evaluate_type="long_short_pred_th_classify",
                                                      version_alias=version_alias,
                                                      label_name=label_name,
                                                      symbol=stock,
                                                      pred_th_up=pred_th_up, pred_th_dw=pred_th_dw)
        if process_signal:
            signal_df_load = pd.read_parquet(parquet_path)
            model_save_and_evaluate.model_signal_process_long_short_pred_th_classify(signal_df_load, pred_th_up=pred_th_up,
                                                                                     pred_th_dw=pred_th_dw,
                                                                                     symbol=stock,
                                                                                     signal_process_base_dir=signal_dir)
        self.pred_up = pred_th_up
        self.pred_dw = pred_th_dw
        print("INFO: research signal_dir: {}, pred_up {}, pred_dw {}.".format(signal_dir, self.pred_up, self.pred_dw))
        self.signal_process_dir = signal_dir
        os.makedirs(self.backtest_result_dir, exist_ok=True)
        return signal_dir


    def get_result_path(self):
        # 返回回测结果路径
        return self.backtest_result_dir


    def get_signal_path(self, stock, pred_up = None, pred_dw = None, process_signal = True):
        # 返回信号路径
        online_or_research_path = self.online_or_research_path
        # online_path, 是否读取线上信号文件路径
        if online_or_research_path:
            exp_name = self.exp_name
            pred_up = pred_up if pred_up else self.pred_up
            pred_dw = pred_dw if pred_dw else self.pred_dw
            label_name = self.label_name
            signal_file = os.path.join(self.online_exp_path, eval(self._get_dynamic_str(self.online_signal_file_format)))
            # assert pred_up, "信号文件不合法，{}： pred_up为空，请指定pred_up。".format(signal_file)
            # assert pred_dw, "信号文件不合法，{}： pred_dw为空，请指定pred_dw。".format(signal_file)
            signal_dir = self._get_signal_path_online(exp_name, stock, pred_up, pred_dw, label_name = label_name,
                                                      process_signal = False)
        else:
            exp_name = self.exp_name
            version_alias = self.version_alias
            pred_up = pred_up if pred_up else self.pred_up
            pred_dw = pred_dw if pred_dw else self.pred_dw
            label_name = self.label_name
            signal_file = os.path.join(self.research_exp_path, eval(self._get_dynamic_str(self.research_signal_file_format)))
            assert exp_name, "信号文件不合法，{}： exp_name为空，请指定exp_name。".format(signal_file)
            assert version_alias, "信号文件不合法，{}： version_alias为空，请指定version_alias。".format(signal_file)
            # assert label_name, "信号文件不合法，{}：  label_name为空，请指定label_name。".format(signal_file)
            assert pred_up, "信号文件不合法，{}： pred_up为空，请指定pred_up。".format(signal_file)
            assert pred_dw, "信号文件不合法，{}： pred_dw为空，请指定pred_dw。".format(signal_file)
            signal_dir = self._get_signal_path_research(exp_name, version_alias, stock, pred_up, pred_dw, label_name,
                                       process_signal=process_signal)
        return signal_dir


    def get_valid_backtest_dates(self):
        if not self._check_signal_path():
            return  []
        start_date = self.start_date
        end_date = self.end_date
        days = []

        for v in os.listdir(self.signal_process_dir):
            if v.endswith("txt"):
                try:
                    day = dt.datetime.strptime(v[:-4], "%Y-%m-%d").strftime("%Y%m%d")
                    days.append(day)
                except:
                    pass
        days = sorted(days)
        if start_date and end_date:
            start_date = start_date.replace("-", "")
            end_date =  end_date.replace("-", "")
            days = [day for day in days if day >= start_date and day <= end_date]
        print("INFO: valid parallel backtest days: ", days)
        return days

    def get_valid_symbols(self):
        exp_name = self.exp_name
        version_alias = self.version_alias
        label_name = self.label_name
        stock = None
        symbol_list = []
        if self.online_or_research_path:
            parquet_path = os.path.join(self.online_exp_path,
                                        eval(self._get_dynamic_str(self.online_signal_file_format)))
            parquet_dir = os.path.dirname(parquet_path)
            for f in os.listdir(parquet_dir):
                if f.endswith("parquet"):
                    symbol = f.split("-")[1][:-8]
                    symbol_list.append(symbol)
        else:
            parquet_path = os.path.join(self.research_exp_path,
                                        eval(self._get_dynamic_str(self.research_signal_file_format)))
            parquet_dir = os.path.dirname(parquet_path)
            for f in os.listdir(parquet_dir):
                if f.endswith("parquet"):
                    symbol = f.split("-")[1][:-8]
                    symbol_list.append(symbol)
        print("symbol_list: ",len(symbol_list), symbol_list)
        return symbol_list


if __name__=="__main__":
    # 线上信号路径
    backtest_params = BackTestParams(
        online_or_research_path = True,
        strategy_name = "StrategyT0",
        exp_name = "HS_tick2",
        start_date = "20240930",
        end_date = "20241016"
    )
    signal_dir = backtest_params.get_signal_path("688012.SH", pred_up = None, pred_dw = None, process_signal=False)
    result_dir = backtest_params.get_result_path()
    valid_dates = backtest_params.get_valid_backtest_dates()
    symbols = backtest_params.get_valid_symbols()

    # 研究信号路径
    backtest_params = BackTestParams(
        online_or_research_path= False,
        strategy_name="StrategyT0",
        exp_name="KG101_model",
        version_alias="HS_tick2",
        start_date="20240930",
        end_date="20241016"
    )
    signal_dir = backtest_params.get_signal_path("688012.SH", pred_up = 1.1, pred_dw = -1.1, process_signal=False)
    result_dir = backtest_params.get_result_path()
    valid_dates = backtest_params.get_valid_backtest_dates()
    print("result_dir: ", result_dir)
    symbols = backtest_params.get_valid_symbols()

