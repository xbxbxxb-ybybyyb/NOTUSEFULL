import sys
sys.path.insert(0, "/tmp/pycharm_project_710/exp_assembles/")
import artifacts
import importlib
importlib.reload(artifacts)

from artifacts import exp_artifacts, save_to_mongo, model_save_and_evaluate,utils, factor_save_and_evaluate
from artifacts import parse_format, backtest_save_and_evaluate, model_plot, online_model, model_metrics
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from artifacts import backtest_plot
from artifacts import flying_functions
from artifacts.flying_functions import *

import os
import json
import polars as pl


##############################################################
from artifacts import online_model, model_save_and_evaluate
import os
import json
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from xquant.factordata import FactorData
from tqdm import tqdm
import ray

if __name__=="__main__":

    def rewrite_parquet(label_name, exp_name,signal_name, version_alias):
        save_parquet_path = os.path.join("/home/appadmin/signal_files/", signal_name)
        os.makedirs(save_parquet_path, exist_ok=True)
        expa = exp_artifacts.ExpArtifacts(exp_name=exp_name)
        exp_path = expa.exp_path
        expa.activate_version_to_save({}, version_alias=version_alias)
        exp_version_path = expa.path_of_exp_version()

        # save_parquet_path = os.path.join(os.path.join(model_base_dir, f"signal_files/{label_name}-{symbol}.parquet"))
        for symbol in tqdm(symbol_list):
            signal_df = expa.model_signal_load(version_alias, label_name, symbol)
            signal_df["STRATEGY_NAME"] = signal_name
            signal_df["SYMBOL"] = symbol
            signal_df = signal_df.drop(columns = ["flying_flag"])
            signal_df.to_parquet(os.path.join(save_parquet_path, f"{label_name}-{symbol}.parquet"))

    SYMBOL_LIST = []  # pd.read_csv("kc50.csv", header=None)[0].tolist()
    flying_factor = pd.read_csv("extra_factors.csv", header=None)[0].tolist()
    flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders"]

    label_name, exp_name, version_alias = ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98')
    # label_name, exp_name, version_alias = ("LabelFirstPeak_th12_60s", "exp_l3_zzkc_flying4", 'LabelFirstPeak_th12_60s_factor98')
    label_name, exp_name, version_alias = ("LabelFirstPeak_th12_60s", "exp_l3_kc_flying4", 'LabelFirstPeak_th12_60s')


    symbols = pd.read_csv("kc_amt_swing.csv", header=None)[0].tolist()
    symbols1 = pd.read_csv("zz500_select74.csv", header=None)[0].tolist()
    symbol_list = list(sorted(set(symbols + symbols1)))
    symbol_list = symbols
    # symbol_list = ["688012.SH","688041.SH","688047.SH","688256.SH","688271.SH","688498.SH","688506.SH", "688017.SH"]
    symbol_list = ['688525.SH', '688361.SH', '688037.SH', '688506.SH', '688536.SH', '688409.SH', '688318.SH', '688052.SH',
                   '688521.SH', '688390.SH']
    signal_name = "l2p_zzkc_middle"
    rewrite_parquet(label_name, exp_name, signal_name, version_alias)