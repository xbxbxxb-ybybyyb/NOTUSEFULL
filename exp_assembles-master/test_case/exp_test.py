import sys

sys.path.append("..")
from artifacts.exp_artifacts import ExpArtifacts
from artifacts import backtest_save_and_evaluate
import os
import pandas as pd
import numpy as np
import datetime as dt

symbol = Symbol = "688012.SH"
StrategyModelName = "688012_model"
exp_path = f"/data/user/016869/exp_result/{Symbol}-{StrategyModelName}"
config = {
    # 数据段配置
    "data_config": {
        "symbol": symbol,
        "train_start_time": "20200101",
        "train_end_time": "20220201",
        "valid_start_time": "20221202",
        "valid_end_time": "20230321",
        "test_start_time": "20230322",
        "test_end_time": "20230805",
        "main_stocks": symbol,
        "w_size": 1,
        "n_job": 2,
        "transform": True,
        "clip_type": "3sigma",
        "scaler_type": "z-score",
        "quantile": [0.02, 0.98],
        "factor_name_list": ["ReferenceMidPrice",
                             "FactorWBSQtySpread_n_tick40",
                             "FactorSellOrderQtyStd",
                             "FactorChangjiangAlpha3_n_tick40",
                             "FactorPrice2PriceRatio",
                             "FactorPriceVolumeCorr_n_tick30",
                             "FactorGuangFaTechIndicatorAPZ_n_tick30",
                             "FactorPxVolCorr_n_tick30",
                             "FactorChangjiangAlpha4_n_tick20",
                             "FactorVixDownRatio_n_tick40",
                             "FactorGuangFaTechIndicatorAPZ_n_tick10",
                             "FactorPrice2PriceRatio1",
                             "FactorRSI_n_tick60",
                             "FactorTradeMoneyCum",
                             "FactorZDRatio",
                             "FactorAlpha101World041",
                             "FactorRetStd_n_tick10",
                             "FactorAlpha101World101",
                             "FactorBearPower_n_tick10",
                             "FactorUpCount_n_tick20",
                             "FactorPxVolCorr_n_tick10",
                             "FactorTechIndicatorForSAR_n_tick30",
                             "FactorBigPushV1_n_tick10",
                             "FactorFqs04",
                             "FactorChangjiangAlpha3_n_tick20",
                             "FactorOrderQtySpread",
                             "FactorAsk1AvgLS",
                             "FactorAvgOutRatio_n_tick10",
                             "FactorUpCount_n_tick40",
                             "FactorTechIndicatorForOSC",
                             "FactorTechIndicatorForSAR_n_tick10",
                             "FactorSkew2",
                             "FactorBuyWillingByPriceEn1",
                             "FactorAsk1StdLS",
                             "FactorBid1AvgLS",
                             "FactorAvgOutRatio_n_tick20",
                             "FactorBuyOrderQtyMeanLS",
                             "FactorRSI_n_tick30",
                             "FactorOBV",
                             "FactorTradeMoneyCum1",
                             "FactorGuangFaTechIndicatorENV_n_tick20",
                             "FactorAverageAskScopes",
                             "FactorChangjiangAlpha4_n_tick50",
                             "FactorTianFengAlpha14_n_tick50",
                             "FactorBuyWillingByMoneyEn1",
                             "FactorOrderImbalance",
                             "FactorTianFengAlpha14_n_tick20",
                             "FactorBuyWillingByCountEn1",
                             "FactorGuangFaTechIndicatorENV_n_tick50",
                             "FactorShortTermAmp",
                             "FactorBuyVolumeAvgLS",
                             "FactorPrice2PriceRatio2",
                             "FactorGtjaAlpha171"],  # 按条数筛选后写入
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

    "path_config": {
        "Exp_path": exp_path,
        "model_saved_path": os.path.join(exp_path, "saved_models/"),
        "dataset_saved_path": os.path.join(exp_path, "dataset"),
        "signal_saved_path": os.path.join(exp_path, "signal_files/"),
        "signal_saved_txt_path": os.path.join(exp_path, "signal_files_txt/"),
        "plot_saved_path": os.path.join(exp_path, "plot_files"),
        "backtest_saved_path": os.path.join(exp_path, "backtest")
    }
}

strategy_config = {
    "data_config": {
        "策略标的": "688012.SH",
        "交易时间": "093201-113000,130001-145700",
        "尾盘对冲时间": "145600",
        "午盘撤单时间": "112950",
        "交易账户": "801c",
        "对冲周期(秒)": 1,
        "信号下单周期(秒)": 1,
        "全局撤单重试时间(秒)": 1,
        "信号开仓基准": "盘口中间价",
        "单笔委托最大量(股)": 50000,
        "信号基准价偏移比例": 0,
        "基准价格偏移方向": "向上",
        "对报价进行涨跌停限制": "是",
        "异常控制措施": "无",
        "铺单模式是否考虑靠档": "否",
        "是否启用增强tick": "否",
        "订单指向模式": "自行下单",
        "子策略的优先级": "子策略高优先级",
        "订阅主策略类型": "STARNewStrategy",
        "是否启动纯净盘口": "启动",
        "模式开关控制": [
            {
                "是否启动对冲开关": "是",
                "是否启动信号因子套利开关": "是"
            }
        ],
        "对冲模式": [
            {
                "敞口轧差模式": "时间最前",
                "对冲单是否靠档": "对冲止盈单靠档",
                "对冲模式下止盈单盈利金额": 0,
                "单笔持仓上限对冲时间": 300,
                "单笔总价止盈判定": 1000,
                "单笔总价止损判定": -1000,
                "单价止盈率": 0.003,
                "单价止损率": -0.005,
                "中间价最优止损率": None,
                "抢跑机制下一档数量": 50000,
                "最新主动买卖价时间设置": 10,
                "最优档掩埋再次下单周期": 10,
                "最优档掩埋抬价次数上限": 3,
                "最优一档的Tick金额": 0.01,
                "买交易费率": 0.001,
                "卖交易费率": 0.001,
                "趋势预测阈值": 0.001,
                "波动率计算窗口(s)": 60,
                "主动成交时未成交撤单时间(s)": 10
            }
        ],
        "异常废单处理": [
            {
                "废单总次数上限": 200,
                "滑窗废单次数": 40,
                "滑窗时间": 10,
                "单笔对敲重复申报次数": 3,
                "降档次数": 3,
                "拉抬废单转换时间": 10,
                "单笔撤单上限": 10,
                "单笔下单上限": 10
            }
        ],
        "事件应对机制": [
            {
                "接近行情涨跌停价比例": 0.02,
                "达到涨跌停价比例": 0.002,
                "单边成交最大控制": 5000,
                "股价异常波动_幅度": 0.01,
                "股价异常波动_窗口时间(秒)": 180,
                "禁止敞口数量": 600,
                "铺单模式下敞口控制": 600,
                "零股卖单控制上限": 10
            }
        ],
        "信号参数设置": [
            {
                "订阅铺单信号策略类型": "OnnxTest",
                "是否启动趋势AI铺单信号": "趋势AI铺单信号",
                "是否进行信号的前后一致性判断": "否",
                "铺单指定的类型": "OnnxTest",
                "铺单抢订的最优一档的tick个数": 2,
                "信号失效时间": 20,
                "是否启动浮亏控制": "否"
            }
        ],
        "信号套利模式": [
            {
                "模式档位名称": "卖五",
                "平衡模式数量(股)": 0,
                "平衡模式距离基准最小距离": 0.005,
                "平衡模式波动容忍价格": 0.002,
                "平衡模式止盈单止盈率": 0,
                "轻微偏向买数量(股)": 0,
                "轻微偏向买距离基准最小距离": 0.005,
                "轻微偏向买波动容忍价格": 0,
                "轻微偏向买止盈单止盈率": 0,
                "轻微偏向卖数量(股)": 0,
                "轻微偏向卖距离基准最小距离": 0.005,
                "轻微偏向卖波动容忍价格": 0,
                "轻微偏向卖止盈单止盈率": 0,
                "强烈偏向买数量(股)": 0,
                "强烈偏向买距离基准最小距离": 0.005,
                "强烈偏向买波动容忍价格": 0,
                "强烈偏向买止盈单止盈率": 0,
                "强烈偏向卖数量(股)": 0,
                "强烈偏向卖距离基准最小距离": 0.005,
                "强烈偏向卖波动容忍价格": 0,
                "强烈偏向卖止盈单止盈率": 0
            },
            {
                "模式档位名称": "卖四",
                "平衡模式数量(股)": 0,
                "平衡模式距离基准最小距离": 0.004,
                "平衡模式波动容忍价格": 0.002,
                "平衡模式止盈单止盈率": 0,
                "轻微偏向买数量(股)": 0,
                "轻微偏向买距离基准最小距离": 0.004,
                "轻微偏向买波动容忍价格": 0,
                "轻微偏向买止盈单止盈率": 0,
                "轻微偏向卖数量(股)": 0,
                "轻微偏向卖距离基准最小距离": 0.004,
                "轻微偏向卖波动容忍价格": 0,
                "轻微偏向卖止盈单止盈率": 0,
                "强烈偏向买数量(股)": 0,
                "强烈偏向买距离基准最小距离": 0.004,
                "强烈偏向买波动容忍价格": 0,
                "强烈偏向买止盈单止盈率": 0,
                "强烈偏向卖数量(股)": 0,
                "强烈偏向卖距离基准最小距离": 0.004,
                "强烈偏向卖波动容忍价格": 0,
                "强烈偏向卖止盈单止盈率": 0
            },
            {
                "模式档位名称": "卖三",
                "平衡模式数量(股)": 200,
                "平衡模式距离基准最小距离": 0.003,
                "平衡模式波动容忍价格": 0.05,
                "平衡模式止盈单止盈率": 0,
                "轻微偏向买数量(股)": 0,
                "轻微偏向买距离基准最小距离": 0.003,
                "轻微偏向买波动容忍价格": 0,
                "轻微偏向买止盈单止盈率": 0,
                "轻微偏向卖数量(股)": 0,
                "轻微偏向卖距离基准最小距离": 0.003,
                "轻微偏向卖波动容忍价格": 0,
                "轻微偏向卖止盈单止盈率": 0,
                "强烈偏向买数量(股)": 0,
                "强烈偏向买距离基准最小距离": 0.003,
                "强烈偏向买波动容忍价格": 0,
                "强烈偏向买止盈单止盈率": 0,
                "强烈偏向卖数量(股)": 0,
                "强烈偏向卖距离基准最小距离": 0.003,
                "强烈偏向卖波动容忍价格": 0,
                "强烈偏向卖止盈单止盈率": 0
            },
            {
                "模式档位名称": "卖二",
                "平衡模式数量(股)": 0,
                "平衡模式距离基准最小距离": 0.002,
                "平衡模式波动容忍价格": 0.1,
                "平衡模式止盈单止盈率": 0,
                "轻微偏向买数量(股)": 0,
                "轻微偏向买距离基准最小距离": 0.002,
                "轻微偏向买波动容忍价格": 0,
                "轻微偏向买止盈单止盈率": 0,
                "轻微偏向卖数量(股)": 0,
                "轻微偏向卖距离基准最小距离": 0.002,
                "轻微偏向卖波动容忍价格": 0,
                "轻微偏向卖止盈单止盈率": 0,
                "强烈偏向买数量(股)": 0,
                "强烈偏向买距离基准最小距离": 0.002,
                "强烈偏向买波动容忍价格": 0,
                "强烈偏向买止盈单止盈率": 0,
                "强烈偏向卖数量(股)": 0,
                "强烈偏向卖距离基准最小距离": 0.002,
                "强烈偏向卖波动容忍价格": 0,
                "强烈偏向卖止盈单止盈率": 0
            },
            {
                "模式档位名称": "卖一",
                "平衡模式数量(股)": 0,
                "平衡模式距离基准最小距离": 0.001,
                "平衡模式波动容忍价格": 0.002,
                "平衡模式止盈单止盈率": 0,
                "轻微偏向买数量(股)": 0,
                "轻微偏向买距离基准最小距离": 0.001,
                "轻微偏向买波动容忍价格": 0,
                "轻微偏向买止盈单止盈率": 0,
                "轻微偏向卖数量(股)": 200,
                "轻微偏向卖距离基准最小距离": -0.5,
                "轻微偏向卖波动容忍价格": 1,
                "轻微偏向卖止盈单止盈率": 0.003,
                "强烈偏向买数量(股)": 0,
                "强烈偏向买距离基准最小距离": 0.001,
                "强烈偏向买波动容忍价格": 0,
                "强烈偏向买止盈单止盈率": 0,
                "强烈偏向卖数量(股)": 300,
                "强烈偏向卖距离基准最小距离": -0.5,
                "强烈偏向卖波动容忍价格": 1,
                "强烈偏向卖止盈单止盈率": 0.004
            },
            {
                "模式档位名称": "买一",
                "平衡模式数量(股)": 0,
                "平衡模式距离基准最小距离": 0.001,
                "平衡模式波动容忍价格": 0.002,
                "平衡模式止盈单止盈率": 0,
                "轻微偏向买数量(股)": 200,
                "轻微偏向买距离基准最小距离": -0.5,
                "轻微偏向买波动容忍价格": 1,
                "轻微偏向买止盈单止盈率": 0.003,
                "轻微偏向卖数量(股)": 0,
                "轻微偏向卖距离基准最小距离": 0.001,
                "轻微偏向卖波动容忍价格": 0,
                "轻微偏向卖止盈单止盈率": 0,
                "强烈偏向买数量(股)": 300,
                "强烈偏向买距离基准最小距离": -0.5,
                "强烈偏向买波动容忍价格": 1,
                "强烈偏向买止盈单止盈率": 0.004,
                "强烈偏向卖数量(股)": 0,
                "强烈偏向卖距离基准最小距离": 0.001,
                "强烈偏向卖波动容忍价格": 0,
                "强烈偏向卖止盈单止盈率": 0
            },
            {
                "模式档位名称": "买二",
                "平衡模式数量(股)": 0,
                "平衡模式距离基准最小距离": 0.002,
                "平衡模式波动容忍价格": 0.1,
                "平衡模式止盈单止盈率": 0,
                "轻微偏向买数量(股)": 0,
                "轻微偏向买距离基准最小距离": 0.002,
                "轻微偏向买波动容忍价格": 0,
                "轻微偏向买止盈单止盈率": 0,
                "轻微偏向卖数量(股)": 0,
                "轻微偏向卖距离基准最小距离": 0.002,
                "轻微偏向卖波动容忍价格": 0,
                "轻微偏向卖止盈单止盈率": 0,
                "强烈偏向买数量(股)": 0,
                "强烈偏向买距离基准最小距离": 0.002,
                "强烈偏向买波动容忍价格": 0,
                "强烈偏向买止盈单止盈率": 0,
                "强烈偏向卖数量(股)": 0,
                "强烈偏向卖距离基准最小距离": 0.002,
                "强烈偏向卖波动容忍价格": 0,
                "强烈偏向卖止盈单止盈率": 0
            },
            {
                "模式档位名称": "买三",
                "平衡模式数量(股)": 200,
                "平衡模式距离基准最小距离": 0.003,
                "平衡模式波动容忍价格": 0.05,
                "平衡模式止盈单止盈率": 0,
                "轻微偏向买数量(股)": 0,
                "轻微偏向买距离基准最小距离": 0.003,
                "轻微偏向买波动容忍价格": 0,
                "轻微偏向买止盈单止盈率": 0,
                "轻微偏向卖数量(股)": 0,
                "轻微偏向卖距离基准最小距离": 0.003,
                "轻微偏向卖波动容忍价格": 0,
                "轻微偏向卖止盈单止盈率": 0,
                "强烈偏向买数量(股)": 0,
                "强烈偏向买距离基准最小距离": 0.003,
                "强烈偏向买波动容忍价格": 0,
                "强烈偏向买止盈单止盈率": 0,
                "强烈偏向卖数量(股)": 0,
                "强烈偏向卖距离基准最小距离": 0.003,
                "强烈偏向卖波动容忍价格": 0,
                "强烈偏向卖止盈单止盈率": 0
            },
            {
                "模式档位名称": "买四",
                "平衡模式数量(股)": 0,
                "平衡模式距离基准最小距离": 0.004,
                "平衡模式波动容忍价格": 0.002,
                "平衡模式止盈单止盈率": 0,
                "轻微偏向买数量(股)": 0,
                "轻微偏向买距离基准最小距离": 0.004,
                "轻微偏向买波动容忍价格": 0,
                "轻微偏向买止盈单止盈率": 0,
                "轻微偏向卖数量(股)": 0,
                "轻微偏向卖距离基准最小距离": 0.004,
                "轻微偏向卖波动容忍价格": 0,
                "轻微偏向卖止盈单止盈率": 0,
                "强烈偏向买数量(股)": 0,
                "强烈偏向买距离基准最小距离": 0.004,
                "强烈偏向买波动容忍价格": 0,
                "强烈偏向买止盈单止盈率": 0,
                "强烈偏向卖数量(股)": 0,
                "强烈偏向卖距离基准最小距离": 0.004,
                "强烈偏向卖波动容忍价格": 0,
                "强烈偏向卖止盈单止盈率": 0
            },
            {
                "模式档位名称": "买五",
                "平衡模式数量(股)": 0,
                "平衡模式距离基准最小距离": 0.005,
                "平衡模式波动容忍价格": 0.002,
                "平衡模式止盈单止盈率": 0,
                "轻微偏向买数量(股)": 0,
                "轻微偏向买距离基准最小距离": 0.005,
                "轻微偏向买波动容忍价格": 0,
                "轻微偏向买止盈单止盈率": 0,
                "轻微偏向卖数量(股)": 0,
                "轻微偏向卖距离基准最小距离": 0.005,
                "轻微偏向卖波动容忍价格": 0,
                "轻微偏向卖止盈单止盈率": 0,
                "强烈偏向买数量(股)": 0,
                "强烈偏向买距离基准最小距离": 0.005,
                "强烈偏向买波动容忍价格": 0,
                "强烈偏向买止盈单止盈率": 0,
                "强烈偏向卖数量(股)": 0,
                "强烈偏向卖距离基准最小距离": 0.005,
                "强烈偏向卖波动容忍价格": 0,
                "强烈偏向卖止盈单止盈率": 0
            }
        ]
    }
}

if __name__ == '__main__':
    model_df = pd.DataFrame(np.arange(16).reshape(4, 4), columns=["FactorAlpha101World041", "FactorRetStd_n_tick10",
                                                                  "FactorAlpha101World101", "FactorBearPower_n_tick10"])
    version_a = "exp_test5"
    base_dir = os.path.join("/data/user/quanttest007/013150/exp_result/002594.SZ-002594.SZ_trade_v00")
    expa = ExpArtifacts("exp_name_ceshi_1")
    expa.activate_version_to_save(model_config=config, version_alias=version_a)
    #  1. 存储模型
    expa.model_file_save(model_obj=model_df, mode="pkl_mode", overwrite=True)
    # 2. 加载模型, 指定版本号加载
    model_obj1 = expa.model_file_load(version_alias=version_a, mode="pkl")
    print("model_obj1: ", model_obj1)
    # 3. 保存信号文件
    base_dir = os.path.join("/data/user/quanttest007/013150/exp_result/002594.SZ-002594.SZ_trade_v00")
    TARGET_df_test, T_test, X_train, Y_train, X_valid, Y_valid, X_test, Y_test = pd.read_pickle(
        os.path.join(base_dir, "dataset/data.pkl"))
    Y_test_pred, Y_valid_pred = pd.read_pickle(os.path.join(base_dir, "dataset/data1.pkl"))
    # 减少数据量，只存filter_dt之前的数据
    filter_dt = dt.datetime.strptime("20230505094000", "%Y%m%d%H%M%S")
    T_test1 = [i for i in T_test if i <= filter_dt]
    TARGET_test1 = TARGET_df_test.loc[T_test1].values  # 预测价格
    Y_test_pred1 = Y_test_pred[:len(T_test1)]
    Y_test1 = Y_test[:len(T_test1)]
    print("T_test1: \n", type(T_test1))
    print("Y_test_pred1: \n", type(Y_test_pred1))
    print("Y_test1: \n", type(Y_test1))
    print("TARGET_test1: \n", type(TARGET_test1))
    signal_df1 = expa.model_signal_save(label_name=config["data_config"]["tagger_name_list"][0],
                                        symbol=config["data_config"]["symbol"],
                                        tm_values=T_test1, yhat_values=Y_test_pred1, y_values=Y_test1,
                                        target_values=TARGET_test1, period=120, target_type="mid")
    print("signal_df1:\n", signal_df1)

    # 4. 加载信号文件
    signal_df_load = expa.model_signal_load(version_alias=version_a, symbol=config["data_config"]["symbol"],
                                            label_name=config["data_config"]["tagger_name_list"][0])
    print("signal_df_load:", signal_df_load)

    # 5. 评价信号
    df_th1, df_th2 = expa.model_signal_evalatioin_single_label_th_classify(
        label_name=config["data_config"]["tagger_name_list"][0],
        symbol=config["data_config"]["symbol"],
        label_th=1.1, pred_th_abs_limits=[1, 6.0])
    print("df_th1:\n", df_th1)
    print("df_th2:\n", df_th2)

    # 6. 按单标签阈值分为不同的类别
    expa.model_signal_process_single_label_th_classify(label_name=config["data_config"]["tagger_name_list"][0],
                                                       symbol=config["data_config"]["symbol"], label_th1=1.0,
                                                       probs_up=0.60, probs_dw=0.60)

    # 7. 绘制信号文件
    label_name = config["data_config"]["tagger_name_list"][0]
    symbol = config["data_config"]["symbol"]
    label_th1 = 1.0
    probs_up = 0.60
    probs_dw = 0.60
    signal_txt_save_path = os.path.join(expa.exp_version_path, f"{label_name}-{symbol}")
    sig_path = os.path.join(signal_txt_save_path,
                            f"label_th&{'%.1f' % label_th1}-probs_up&{'%.2f' % probs_up}-probs_dw&{'%.2f' % probs_dw}/")
    signal_df_day = backtest_save_and_evaluate.parse_signal_txt(
        os.path.join(sig_path, "signal_files_processed", "2023-05-04.txt"))
    expa.backtest_plot_signal_only(signal_df_day,
                                   plot_save_dir=os.path.join(sig_path, "signal_files_plot"))

    # 8. 绘制信号和成交数据文件
    from xquant.marketdata import MarketData

    ma = MarketData()

    # ma_df_day = ma.get_data_by_date("STOCK", symbol, "20230808")
    # 造数据
    ma_df_day = pd.read_parquet(
        "/data/user/quanttest007/K0380021/Level2Data/XSHE_Stock_Snapshot_Level2_000036.SZ_202204.parquet")
    ma_df_day["MDDate"] = "20230504"
    base_dir = os.path.join("/data/user/quanttest007/013150/exp_result/002594.SZ-002594.SZ_trade_v00")
    trade_records_df_day = pd.read_parquet(
        os.path.join(base_dir, "backtest/xbrain_result/trade_records_20230504.parquet"))
    # trade_records_df_day = backtest_save_and_evaluate.parse_ats_trade_records(trade_records_df_day)#将xbrain回测数据格式转换为ATS格式
    expa.backtest_plot_signal_trade(signal_df_day, trade_records_df_day, ma_df_day)

    # 9.成交数据文件存储
    strategy_name = "StrategySignalT0Simple-tradesize200"
    strategy_config_alias = "hold_position800"
    signal_process_path = os.path.join(sig_path, "signal_files_processed")
    trade_df = pd.read_parquet(
        os.path.join(base_dir, "backtest/xbrain_result/trade_records_20230504.parquet"))
    expa.backtest_trade_file_save(strategy_name, strategy_config_alias, signal_process_path, trade_df)

    # 10. 成交数据获取
    res_trade_file = expa.backtest_trade_file_load(strategy_name, strategy_config_alias,
                                                   signal_process_base_dir=signal_process_path,
                                                   start_date="20230504", end_date="20230504")
    print("res_trade_file:\n", res_trade_file)

    # 11. 信号评价数据存储
    base_dir = os.path.join("/data/user/quanttest007/013150/exp_result/002594.SZ-002594.SZ_trade_v00")
    trade_records_df = pd.read_parquet(
        os.path.join(base_dir, "backtest/xbrain_result/trade_records_20230504.parquet"))
    strategy_name = "StrategySignalT0Simple-tradesize200"
    strategy_config_alias = "hold_position800"
    res_eval = expa.backtest_trade_evaluation(strategy_name, strategy_config_alias,
                                              signal_process_base_dir=signal_process_path,
                                              trade_records_df=trade_records_df)
    pd.set_option("display.max_columns", None)
    print("res_eval: \n", res_eval)

    # 12. 获取五分类存储路径
    path_5 = expa.path_of_signal_process_save(label_name=config["data_config"]["tagger_name_list"][0],
                                              symbol=config["data_config"]["symbol"],
                                              label_th1=1.0,
                                              probs_up=0.60,
                                              probs_dw=0.60)
    print(path_5)
    # /data/user/quanttest007/013150/exp_result/exp_name_ceshi_1/exp_test5/labelEQtriplebarriertaggerv2pricetypeEQmidpricedsizeEQ120barrierEQ1-688012.SH/label_th&1.0-probs_up&0.60-probs_dw&0.60/signal_files_processed

    # 13. 获取模型版本号路径
    path_version = expa.path_of_exp_version()
    print(path_version)
    # /data/user/quanttest007/013150/exp_result/exp_name_ceshi_1/exp_test5

    # 14 . 获取策略版本号路径
    path_strategy_version = expa.path_of_backtest_signal_process_save(
        strategy_name="StrategySignalT0Simple-tradesize200",
        strategy_version_alis="hold_position800",
        label_name=config["data_config"]["tagger_name_list"][0],
        symbol=config["data_config"]["symbol"],
        label_th1=1.0,
        probs_up=0.60,
        probs_dw=0.60
    )
    print(path_strategy_version)
    # /data/user/quanttest007/013150/exp_result/exp_name_ceshi_1/exp_test5/labelEQtriplebarriertaggerv2pricetypeEQmidpricedsizeEQ120barrierEQ1-688012.SH/label_th&1.0-probs_up&0.60-probs_dw&0.60/StrategySignalT0Simple-tradesize200-hold_position800

    # 15. 获取参数及版本号信息
    pd.set_option("display.max_columns", None)
    version_msg = expa.load_exp_params(version_alias="exp_test5")
    print(version_msg)

    # 16. 获取信号评价信息
    signal_evaluate_df = expa.load_signal_evaluation_data(exp_id=expa.exp_name, version_alias="exp_test5")
    print(signal_evaluate_df)

    # 17. 获取策略评价信息
    backtest_evaluate_df = expa.load_backtest_evaluation_data(exp_id=expa.exp_name)
    print(backtest_evaluate_df)

    # 18. 注册版本号信息
    # 为策略路径传参
    version_strategy = expa.regist_config(config=strategy_config, config_alias="hold_position800", reg_type="strategy",
                                          strategy_name="StrategySignalT0Simple-tradesize200",
                                          strategy_version_alis="hold_position800",
                                          label_name=config["data_config"]["tagger_name_list"][0],
                                          symbol=config["data_config"]["symbol"],
                                          label_th1=1.0,
                                          probs_up=0.60,
                                          probs_dw=0.60)
    print(version_strategy)

    # 19. 根据版本号别名获取配置参数
    params = expa.get_regist_config("hold_position800")
    print(params)
