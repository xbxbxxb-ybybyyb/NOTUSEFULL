import sys

sys.path.insert(0, "..")
import artifacts
from artifacts.exp_artifacts_todo import ExpArtifacts
from artifacts import backtest_save_and_evaluate
from artifacts import online_model
import os
import pandas as pd
import numpy as np

symbol = Symbol = "688012.SH"
StrategyModelName = "688012_model"
exp_path = f"/data/user/016869/exp_result/{Symbol}-{StrategyModelName}"

config = {
    # 数据段配置
    "data_config": {
        "symbol": symbol,
        "train_start_time": "20200102",
        "train_end_time": "20220201",
        "valid_start_time": "20221202",
        "valid_end_time": "20230321",
        "test_start_time": "20230322",
        "test_end_time": "20230804",
        "main_stocks": symbol,
        "w_size": 1,
        "n_job": 2,
        "transform": True,
        "clip_type": "5sigma",
        "scaler_type": "z-score",
        "quantile": [0.02, 0.98],
        "factor_name_list": ["ReferenceMidPrice",
                                "FactorAlpha101World041",
                                "FactorAsk1AvgLS",
                                "FactorBearPower_n_tick10",
                                "FactorBearPower_n_tick100",
                                "FactorBearPower_n_tick30",
                                "FactorBid1AvgLS",
                                "FactorBookBuy13MoveQtyDeltaSum",
                                "FactorBookBuy15Move1QtyDelta",
                                "FactorBookBuy15Move1QtyDeltaDy0TickQtyRatio",
                                "FactorBookBuy15Move1QtyDeltaDy0TickRatio",
                                "FactorBookBuy15Move1QtyDeltaMa100",
                                "FactorBookBuy15MoveQtyDeltaSum",
                                "FactorBookBuy610Move1QtyDeltaMa100",
                                "FactorBookBuy610MoveQtyDeltaSum",
                                "FactorBookBuyMaxQtyPxDwDelta",
                                "FactorBookBuyMaxQtyPxPxRatio",
                                "FactorBookBuyQtySumQtyMaxPxMuity",
                                "FactorBookBuySell10PriceRangeDeltaNegativeQtyRatio",
                                "FactorBookBuySell10PriceRangeDeltaNegativeTickRatio",
                                "FactorBookBuySell15DeltaMa100",
                                "FactorBookBuySell5PriceRangeDeltaNegativeQtyRatio",
                                "FactorBookBuySell5PriceRangeDeltaNegativeTickRatio",
                                "FactorBookBuySell610DeltaMa100",
                                "FactorBookBuySell610QtyRatiomaxsize",
                                "FactorBookBuySumQtyLastPreRatio",
                                "FactorBookSell610Move1QtyDeltaMa100",
                                "FactorBookSell610MoveQtyDeltaSum",
                                "FactorBookSellMaxQtyPxDwDelta",
                                "FactorBookSellMaxQtyPxPxRatio",
                                "FactorBookSellMaxVolIndex10VolRatio",
                                "FactorBuyOrderQtyStd_n_tick10",
                                "FactorBuyOrderQtyStd_n_tick100",
                                "FactorBuyOrderQtyStd_n_tick60",
                                "FactorBuySellOrderQtyRatio",
                                "FactorBuySellOrderQtyRatioDiff",
                                "FactorBuyTrade2OrderQtyRatio",
                                "FactorBuyVolumeAvgLS",
                                "FactorBuyWillingByCountEn1",
                                "FactorBuyWillingByMoneyEn1",
                                "FactorBuyWillingByPrice",
                                "FactorBuyWillingByQtyEn1",
                                "FactorChangjiangAlpha1_n_tick20",
                                "FactorChangjiangAlpha4_n_tick20",
                                "FactorErAlpha_n_tick100",
                                "FactorErAlpha_n_tick20",
                                "FactorErAlpha_n_tick40",
                                "FactorFqs01_n_tick100",
                                "FactorFqs01_n_tick20",
                                "FactorFqs01_n_tick40",
                                "FactorFqs02_n_tick100",
                                "FactorFqs02_n_tick20",
                                "FactorFqs02_n_tick40",
                                "FactorFqs04",
                                "FactorGtjaAlpha013",
                                "FactorGtjaAlpha014_n_tick20",
                                "FactorGtjaAlpha015_n_tick20",
                                "FactorGtjaAlpha015_n_tick50",
                                "FactorGtjaAlpha015_n_tick90",
                                "FactorGtjaAlpha047_n_tick10",
                                "FactorGtjaAlpha047_n_tick30",
                                "FactorGtjaAlpha078",
                                "FactorGuangFaTechIndicatorAPZ_n_tick10",
                                "FactorGuangFaTechIndicatorAPZ_n_tick30",
                                "FactorGuangFaTechIndicatorENV_n_tick20",
                                "FactorGuangFaTechIndicatorTDI_n_tick20",
                                "FactorGuangFaTechIndicatorVMA_n_tick20",
                                "FactorGuangFaTechIndicatorVMA_n_tick50",
                                "FactorGuangFaTechIndicatorVMA_n_tick90",
                                "FactorMidPriceSpeed_n_tick20",
                                "FactorOrderImbalance_level1",
                                "FactorOrderImbalance_level2",
                                "FactorOrderQtyChangeEachLevelBuy_n_tick100",
                                "FactorOrderQtyChangeEachLevelBuy_n_tick20",
                                "FactorOrderQtyChangeEachLevelBuy_n_tick60",
                                "FactorOrderQtySpread",
                                "FactorSellOrderQtyStd",
                                "FactorShortTermAmp",
                                "FactorSkew1",
                                "FactorSkew1_n_tick30",
                                "FactorSkew2",
                                "FactorSkew2_n_tick30",
                                "FactorSlicePressure",
                                "FactorTechIndicatorForB3612",
                                "FactorTechIndicatorForCMF",
                                "FactorTechIndicatorForSAR_n_tick100",
                                "FactorTechIndicatorForSAR_n_tick60",
                                "FactorTechIndicatorForWR_n_tick100",
                                "FactorTechIndicatorForWR_n_tick60",
                                "FactorTianFengAlpha14_n_tick100",
                                "FactorTianFengAlpha21_n_tick20",
                                "FactorTianFengAlpha21_n_tick40",
                                "FactorTianFengAlpha21_n_tick60",
                                "FactorTianFengAlpha3_n_tick100",
                                "FactorTianFengAlpha3_n_tick20",
                                "FactorTianFengAlpha3_n_tick40",
                                "FactorTianFengAlpha3_n_tick60",
                                "FactorTradeMoneyCum1",
                                "FactorTrendStrength_n_tick20",
                                "FactorTrendStrength_n_tick40",
                                "FactorUpCount_n_tick20",
                                "FactorUpCount_n_tick40",
                                "FactorVixDownRatio_n_tick20",
                                "FactorVixDownRatio_n_tick40",
                                "FactorVixUp_n_tick20",
                                "FactorVolPriceCorr_n_tick100",
                                ],  # 按条数筛选后写入
        "tagger_name_list": ["labelEQtriplebarriertaggerv2pricetypeEQmidpricedsizeEQ120barrierEQ1"],
        "tagger_limit": 50,
        "raw_name_list": [],
        "model_dir": os.path.join(exp_path, "saved_models/"),
        "thres": [0.02, 0.02],
        # 因子候选集, factor_select 是在这里的因子选
        # "factor_pool": "/data/user/019771/star_project/exp_result/688223.SH_trade_v1.1/factor_pool.csv",
        # 也可是public或personal
        "data_source": "{}_factor_df.parquet".format(
            symbol[:-3]),
        "label_source": "label_{}.parquet".format(symbol),
        # 不以Factor开头但是也能放进来的列表
        "other_factor_list": "",
        # 因子列表， 为空的话为全量
        "factor_json_path": "",
        # 因子黑名单列表，不能用的因子
        "exclude_json_path": "/data/user/013150/online_scripts/Signal_Pipeline/factor_exclude.json"},
    # 模型段配置
    "xgb_config": {
        'objective': 'reg:squarederror',
        'booster': 'gbtree',
        'tree_method': 'gpu_hist',
        'gamma': 0.5,
        'learning_rate': 0.01,
        'lambda': 2,
        'subsample': 0.7,
        'colsample_bytree': 0.7,
        'max_depth': 14,
        'n_estimators': 3000,
        'seed': 4},
    "metrics": {"reg_eval_abs_limits": [1.0, 3.0],
                "reg_eval_th": 0.5},
    "model": {"name": "mlp"},
    "optimizer": {"name": "adam", "lr": 0.001, },
    "criterion": {"name": "mse"},
    "model_dir": os.path.join(exp_path, "saved_models/"),
    "Model_save_mode": ["pkl", "onnx"],
    "n_jobs_model": 32,

}

if __name__ == "__main__":
    expa = ExpArtifacts("688012.SH_trade")
    expa.activate_version_to_save(model_config=config, version_alias="v3")
    # (1)存储模型
    model_df = pd.DataFrame(np.arange(16).reshape(4, 4), columns=["FactorAlpha101World041", "FactorRetStd_n_tick10",
                                                                  "FactorAlpha101World101", "FactorBearPower_n_tick10"])
    # expa.model_file_save(model_obj=model_df, mode="pkl_mode", overwrite=False)

    # (2)加载模型, 指定版本号加载
    model_obj1 = expa.model_file_load(version_alias="v3", mode="pkl")
    # model_obj2 = expa.model_file_load(version_alias="exp_test2", mode="pkl")


    # (3)生成信号数据
    factor_name_list =  config["data_config"]["factor_name_list"].copy()
    factor_name_list.remove("ReferenceMidPrice")
    base_dir = os.path.join("/data/user/quanttest007/013150/exp_result/002594.SZ-002594.SZ_trade_v00")
    TARGET_df_test, T_test, X_train, Y_train, X_valid, Y_valid, X_test, Y_test = pd.read_pickle(
        os.path.join(base_dir, "dataset/data.pkl"))
    Y_test_pred, Y_valid_pred = pd.read_pickle(os.path.join(base_dir, "dataset/data1.pkl"))
    factor_df = pd.DataFrame(X_test, index = T_test, columns=factor_name_list)
    clipper_sess, scaler_sess, model_sess = expa.model_file_load(version_alias=expa.version_alias, mode = "onnx")
    y_hat = online_model.generate_onnx_model_predict(clipper_sess, scaler_sess, model_sess, factor_df, factor_name_list, trainingStep = config["data_config"]["w_size"])
    print("y_hat:", y_hat)

    # (3)保存原始信号文件
    TARGET_test = TARGET_df_test.loc[T_test].values  # 预测价格
    signal_df = expa.model_signal_save(label_name=config["data_config"]["tagger_name_list"][0],
                                       symbol=config["data_config"]["symbol"],
                                       tm_values=T_test, yhat_values=Y_test_pred, y_values=Y_test,
                                       target_values=TARGET_test, period=120, target_type="mid")
    print("signal_df:", signal_df)

    # (4)加载原始信号文件
    signal_df_load = expa.model_signal_load(version_alias="v3", symbol=config["data_config"]["symbol"],
                                            label_name=config["data_config"]["tagger_name_list"][0])
    print("signal_df_load:", signal_df_load)


    # (6)将原始信号文件处理为分类信号文件：按单标签阈值分为不同的类别
    expa.model_signal_process_single_label_th_classify(label_name = config["data_config"]["tagger_name_list"][0], symbol=config["data_config"]["symbol"], label_th1=1.0, probs_up = 0.60, probs_dw=0.60)


    # (6)评价信号
    df_th1 = expa.model_signal_evalatioin_single_label_th_classify(label_name=config["data_config"]["tagger_name_list"][0],
                                                          symbol=config["data_config"]["symbol"],
                                                          label_th=1.1, pred_th_abs_limits=[1, 6.0])
    print("df_th1:", df_th1)

    # (7)绘制信号文件
    label_name = config["data_config"]["tagger_name_list"][0]
    symbol = config["data_config"]["symbol"]
    label_th1 = 1.0
    probs_up  = 0.60
    probs_dw = 0.60
    signal_txt_save_path = os.path.join(expa.exp_version_path, f"signal_files_process/{label_name}-{symbol}")
    sig_path = os.path.join(signal_txt_save_path, f"label_th{'%.1f'%label_th1}-probs_up{'%.2f'%probs_up}-probs_dw{'%.2f'%probs_dw}/")
    signal_df_day = backtest_save_and_evaluate.parse_signal_txt(os.path.join(sig_path, "2023-08-08.txt"))
    expa.backtest_evaluate_plot_signal_only(signal_df_day, plot_save_dir=sig_path.replace("signal_files_process", "signal_files_plot"))

    # (8)绘制信号和成交数据文件
    from xquant.marketdata import MarketData
    ma = MarketData()
    ma_df_day = ma.get_data_by_date("STOCK", symbol, "20230808")
    trade_records_df_day = pd.read_parquet(os.path.join(base_dir, "backtest/xbrain_result/trade_summary_20230801.parquet"))
    # trade_records_df_day = backtest_save_and_evaluate.parse_offline_trade_records(trade_records_df_day)#将xbrain回测数据格式转换为ATS格式
    expa.backtest_evaluate_plot_signal_trade(signal_df_day, trade_records_df_day, ma_df_day)

