import datetime
import re
import random
import time
import pandas as pd
import numpy as np
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtk
from collections import Counter
import json
from joblib import Parallel, delayed
import copy
import pymysql1
from xquant.xqutils.perf_profile import profile
from artifacts import parse_format

def compute_acc_single_by_file(signal_process_txt_path, d_1=0.001, d_2=0.002, r_1=0.001, r_2=0.002, index_as_str = False):
    if not os.path.exists(signal_process_txt_path):
        return pd.DataFrame()
    df1 = parse_format.parse_signal_txt(signal_process_txt_path)
    return compute_acc_single(df1, d_1=d_1, d_2=d_2, r_1=r_1, r_2=r_2, index_as_str = index_as_str)


def compute_acc_single(df1, d_1=0.001, d_2=0.002, r_1=0.001, r_2=0.002, index_as_str = False):
    res = []
    df1.index = df1.PERIOD_BEGIN
    for i in range(len(df1)):
        flag = df1[["D_2", "D_1", "O_1", "R_1", "R_2"]].iloc[i].idxmax()
        if flag in ["D_1", "D_2"]:
            start = df1.iloc[i].PERIOD_BEGIN
            end = df1.iloc[i].PERIOD_END
            min_v = min(df1.loc[start:end].TARGET_VALUE)
            pct = (min_v - df1.iloc[i].TARGET_VALUE) / df1.iloc[i].TARGET_VALUE
            if flag == "D_1":
                if -pct >= d_1:
                    res.append("D_1")
                else:
                    res.append("D_11")
            else:
                if -pct >= d_2:
                    res.append("D_2")
                else:
                    res.append("D_22")
        elif flag in ["R_1", "R_2"]:
            start = df1.iloc[i].PERIOD_BEGIN
            end = df1.iloc[i].PERIOD_END
            max_v = max(df1.loc[start:end].TARGET_VALUE)
            pct = (max_v - df1.iloc[i].TARGET_VALUE) / df1.iloc[i].TARGET_VALUE
            if flag == "R_1":
                if pct >= r_1:
                    res.append("R_1")
                else:
                    res.append("R_11")
            else:
                if pct >= r_2:
                    res.append("R_2")
                else:
                    res.append("R_22")
    res_stat = Counter(res)
    res_dict = {}
    if index_as_str:
        res_dict["date"] = str(df1.index[0].date())
    else:
        res_dict["date"] = df1.index[0].date()
    res_dict["R_1_num"] = res_stat["R_1"] + res_stat["R_11"]
    res_dict["R_2_num"] = res_stat["R_2"] + res_stat["R_22"]
    res_dict["D_1_num"] = res_stat["D_1"] + res_stat["D_11"]
    res_dict["D_2_num"] = res_stat["D_2"] + res_stat["D_22"]
    res_dict["R_1_auc"] = round(res_stat["R_1"] / (res_stat["R_1"] + res_stat["R_11"]), 3) if res_dict[
                                                                                                  "R_1_num"] != 0 else 0
    res_dict["R_2_auc"] = round(res_stat["R_2"] / (res_stat["R_2"] + res_stat["R_22"]), 3) if res_dict[
                                                                                                  "R_2_num"] != 0 else 0
    res_dict["D_1_auc"] = round(res_stat["D_1"] / (res_stat["D_1"] + res_stat["D_11"]), 3) if res_dict[
                                                                                                  "D_1_num"] != 0 else 0
    res_dict["D_2_auc"] = round(res_stat["D_2"] / (res_stat["D_2"] + res_stat["D_22"]), 3) if res_dict[
                                                                                                  "D_2_num"] != 0 else 0
    res_df = pd.DataFrame([res_dict]).set_index("date", drop=True)
    return res_df


def plot_signal(df, adj=False):
    # 绘图流程
    def decorateAx(ax, ts, ys):
        def x_fmt_func(x, pos=None):
            idx = np.clip(int(x + 0.5), 0, len(ts) - 1)
            return ts[idx]

        # 用下标代理原始时间戳数据
        xs = range(len(ys))
        # 下标-时间转换func
        ax.plot(xs, ys, color="blue", linewidth=1, linestyle="-")
        ax.xaxis.set_major_formatter(mtk.FuncFormatter(x_fmt_func))
        ax.grid(True)
        return

    def return_flag(df):
        if np.argmax(df) in ["R_1", 0]:
            return 1
        if np.argmax(df) in ["R_2", 1]:
            return 2
        if np.argmax(df) in ["D_1", 3]:
            return -1
        if np.argmax(df) in ["D_2", 4]:
            return -2
        return 0

    def getCho(s):
        s = np.sign(s)
        if not isinstance(s, pd.core.series.Series):
            s = pd.Series(s)
        prt_ary = s.groupby(s).count().values / float(len(s))
        return -(np.log2(prt_ary) * prt_ary).sum()

    df["flag"] = df[["D_2", "D_1", "O_1", "R_1", "R_2"]].apply(return_flag, axis=1)
    if adj:
        df['cho'] = df["flag"].rolling(2, 1).apply(getCho)
        df['flag'] = df['flag'] * (df['cho'] < 0.5)
    df["Number"] = range(len(df))
    df_r1 = df[df.flag == 1]
    df_r2 = df[df.flag == 2]
    df_d1 = df[df.flag == -1]
    df_d2 = df[df.flag == -2]

    day_list = list(map(str, df.index.tolist()))
    fig = plt.figure(figsize=(100, 10))
    ax1 = fig.subplots()
    decorateAx(ax1, day_list, df.TARGET_VALUE.values)
    ax1.scatter(df_r1.Number.values.tolist(), df_r1.TARGET_VALUE.values.tolist(), color="red", linewidth=1,
                linestyle="-")
    ax1.scatter(df_r2.Number.values.tolist(), df_r2.TARGET_VALUE.values.tolist(), color="#8B0000", linewidth=1,
                linestyle="-")
    ax1.scatter(df_d1.Number.values.tolist(), df_d1.TARGET_VALUE.values.tolist(), color="green", linewidth=1,
                linestyle="-")
    ax1.scatter(df_d2.Number.values.tolist(), df_d2.TARGET_VALUE.values.tolist(), color="#006400", linewidth=1,
                linestyle="-")

def parse_tab2dict(table=None):
    pattern_reg = '(.*):'
    pattern_prob = ':(.*)\/'
    predict_dict = {}
    for t in table:
        reg = re.search(pattern_reg, t).group(0)[:-1]
        prob = re.search(pattern_prob, t).group(0)[1:][:-1]
        predict_dict[float(reg)] = float(prob)
    return predict_dict


###############################V:0:最早的插值版本#######################################################
def translate(df, th=0.6):
    # [D2, D1, 01, R1, R2]
    # less than 0.001
    if (df["O1"] > df["D1"] and df["O1"] > df["R1"]) or (df["R1"] < th and df["D1"] < th):
        tmp = np.random.random_sample(4)
        tmp = np.insert(tmp, 2, 1.5)
        tmp = tmp / sum(tmp)
        return tmp.tolist()
    if df["R1"] >= th and df["R2"] >= th:
        tmp = np.random.random_sample(4)
        tmp = np.insert(tmp, 4, 1.5)
        tmp = tmp / sum(tmp)
        return tmp.tolist()
    if df["R1"] >= th and df["R2"] < th:
        tmp = np.random.random_sample(4)
        tmp = np.insert(tmp, 3, 1.5)
        tmp = tmp / sum(tmp)
        return tmp.tolist()
    if df["D1"] >= th and df["D2"] >= th:
        tmp = np.random.random_sample(4)
        tmp = np.insert(tmp, 0, 1.5)
        tmp = tmp / sum(tmp)
        return tmp.tolist()
    if df["D1"] >= th and df["D2"] < th:
        tmp = np.random.random_sample(4)
        tmp = np.insert(tmp, 1, 1.5)
        tmp = tmp / sum(tmp)
        return tmp.tolist()


def generate_probs_oneday(path, datasettype, t, y_hat, y, amp, table1, table2, threshold, target_value,
                          target_type="mid", rate=1.2, period=300, probsThreshold=0.6):
    yhat_df = pd.DataFrame(y_hat, index=t, columns=["yhat"])
    #     pdict=parse_tab2dict(table)
    tmp_df = yhat_df["yhat"].apply(reg_get_cls_prob, **{
        "maxamp": amp,
        "minamp": -amp,
        "threshold": threshold,
        #         "predict_dict": parse_tab2dict(table1)
        "predict_dict": table1

    })
    # sig_df = tmp_df.apply(pd.Series,index=['R','O','D'])
    sig_df1 = tmp_df.apply(pd.Series, index=['D1', 'O1', 'R1'])

    tmp_df2 = yhat_df["yhat"].apply(reg_get_cls_prob, **{
        "maxamp": amp,
        "minamp": -amp,
        "threshold": threshold,
        #         "predict_dict": parse_tab2dict(table2)
        "predict_dict": table2

    })
    sig_df2 = tmp_df2.apply(pd.Series, index=['D2', 'O2', 'R2'])

    tmpdf = pd.concat([sig_df1, sig_df2], axis=1)

    from functools import partial
    translate1 = partial(translate, th=probsThreshold)
    sig_df = tmpdf.apply(translate1, axis=1).apply(pd.Series, index=['D_2', 'D_1', 'O_1', 'R_1', 'R_2'])

    sig_df["PERIOD_BEGIN"] = sig_df.index
    sig_df["PERIOD_END"] = sig_df.index + datetime.timedelta(seconds=period)
    sig_df["TARGET_TYPE"] = target_type
    sig_df["TARGET_VALUE"] = target_value
    sig_df["PREDICTED"] = y_hat
    return sig_df

def reg_get_cls_prob(y, predict_dict, maxamp, minamp, threshold):
    if abs(y) < threshold:
        other = random.uniform(0.48, 0.5)
        up = random.uniform(0.15, 0.25)
        down = 1 - other - up
        ans = [down, other, up]
    elif (abs(y) >= threshold) and (abs(y) <= maxamp):
        if y >= 0:
            left = round(int(y // 0.1) * 0.1, 2)
            right = round(int(y // 0.1 + 1) * 0.1, 2)
            up = ((y - left) / (right - left)) * \
                 (predict_dict[right] - predict_dict[left]) + predict_dict[left]
            down = random.uniform(0, (1 - up) / 2)
            other = 1 - up - down
            ans = [down, other, up]
        else:
            right = round(int(y * 10) * 0.1, 2)
            left = round(int(y * 10 - 1) * 0.1, 2)
            down = ((-y + right) / (right - left)) * \
                   (predict_dict[right] - predict_dict[left]) + predict_dict[left]
            up = random.uniform(0, (1 - down) / 2)
            other = 1 - up - down
            # ans = [down, other, up]
            ans = [down, other, up]
    elif y > maxamp:
        up = predict_dict[maxamp]
        down = random.uniform(0, (1 - up) / 2)
        other = 1 - up - down
        ans = [down, other, up]
    elif y <= minamp:
        up = predict_dict[minamp]
        down = random.uniform(0, (1 - up) / 2)
        other = 1 - up - down
        ans = [up, other, down]
    ans = [round(v, 4) for v in ans]
    return ans
###############################V:0:最早的插值版本#######################################################


###############################V1: 根据阈值table划分5分类#######################################################
def reg2cls(y, predict_dict1, predict_dict2, maxamp, minamp, threshold, probs_up, probs_dw):
    """回归值转成onehot
    Params:
            y : Predict 原始值
            predict_dict1：置信度表格1(小涨小跌)
            predict_dict2：置信度表格2(大涨大跌)
            maxamp:    最大预测边界
            minamp:    最小预测边界
            threshold: 预测值阈值，预测值小于该值直接认为0分类
            probs_up:  上涨置信度阈值，查表, 大于该阈值才可信
            probs_dw:  下跌置信度阈值，查表, 大于该阈值才可信
    Return:
           ans： one-hot格式的list
    """
    y = float(y)
    if abs(y) < threshold:  # pred出来的值太小了
        return [0, 0, 1, 0, 0]
    if y >= maxamp:
        return [0, 0, 0, 0, 1]
    if y <= minamp:
        return [1, 0, 0, 0, 0]

    try:
        if y > 0:
            v1 = predict_dict1[str(np.floor(y * 10) / 10)]
            v2 = predict_dict2[str(np.floor(y * 10) / 10)]
        else:
            v1 = predict_dict1[str(np.ceil(y * 10) / 10)]
            v2 = predict_dict2[str(np.ceil(y * 10) / 10)]
    except:
        if y > 0:
            v1 = predict_dict1[(np.floor(y * 10) / 10)]
            v2 = predict_dict2[(np.floor(y * 10) / 10)]
        else:
            v1 = predict_dict1[(np.ceil(y * 10) / 10)]
            v2 = predict_dict2[(np.ceil(y * 10) / 10)]

    if (abs(y) >= threshold) and (abs(y) < maxamp):  # 预测值涨跌在tabel范围内
        if y > 0:  # 涨情况
            if v2 > probs_up:  # 置信度查表2, 大于阈值
                ans = [0, 0, 0, 0, 1]
            elif v1 > probs_up:  # 置信度查表1, 大于阈值
                ans = [0, 0, 0, 1, 0]
            else:
                ans = [0, 0, 1, 0, 0]
        else:  # 跌情况
            if v2 > probs_dw:  # 置信度查表2, 大于阈值
                ans = [1, 0, 0, 0, 0]
            elif v1 > probs_dw:  # 置信度查表1, 大于阈值
                ans = [0, 1, 0, 0, 0]
            else:
                ans = [0, 0, 1, 0, 0]
    return ans

###############################V1: 根据阈值table划分5分类#######################################################

def return_flag(df):
    if np.argmax(df) in ["R_1", 0]:
        return 1
    if np.argmax(df) in ["R_2", 1]:
        return 2
    if np.argmax(df) in ["D_1", 3]:
        return -1
    if np.argmax(df) in ["D_2", 4]:
        return -2
    return 0

# pkl 转 txt
def generate_signal_files(df, output_path, date, symbol="688599.SH"):
    with open(os.path.join(output_path, str(date) + ".txt"), "w") as f:
        header = {"StrategyName": "OnnxTest"}
        f.write(json.dumps(header))
        f.write("\n")
        # df["flag"] = df[["D_2", "D_1", "O_1", "R_1", "R_2"]].apply(return_flag, axis=1)
        # df["cho"] = df["flag"].rolling(2,1).apply(getCho)

        for index, row in df.iterrows():
            # if row["cho"] >= 0.5:
            #    PROBABILITY = [0.1,0.1,0.6,0.1,0.1]
            # else:
            predictJson = {
                "PROBABILITY": row["PROBABILITY"],
                "RANGE": [-0.002, -0.0012, 0.0, 0.0012, 0.002],
                "PERIOD_BEGIN": str(row["PERIOD_BEGIN"]),
                "PERIOD_END": str(row["PERIOD_END"]),
                "TARGET_TYPE": "mid",
                "TARGET_VALUE": row["TARGET_VALUE"],
                "STRATEGY_NAME": "OnnxTest",
                "PREDICT": row["PREDICT"],
                "SYMBOL": symbol}
            #             signal_item = [str(row["PERIOD_BEGIN"]),"key",predictJson]
            signal_item = [str(row["PERIOD_BEGIN"]), "mm_ai_signal", str(json.dumps(predictJson).replace("\"", '\"'))]
            f.write(json.dumps(signal_item))
            f.write("\n")


def pk2txt(signal_df, sig_path, symbol, njobs = None):
    dates = set(signal_df["DATE"].tolist())
    if njobs:
        res = Parallel(n_jobs=njobs)(
            delayed(generate_signal_files)(signal_df[signal_df["DATE"]==v], sig_path, v, symbol)
            for n, v in enumerate(dates))
    else:
        for n, v in enumerate(dates):
            generate_signal_files(signal_df[signal_df["DATE"] == v], sig_path, v, symbol)


#################################################################
def generate_onnx_model_predict(clipper_sess, scaler_sess, model_sess, factor_df, factor_name_list, trainingStep):
    clipper_input_name = clipper_sess.get_inputs()[0].name
    clipper_label_name = clipper_sess.get_outputs()[0].name
    scaler_input_name = scaler_sess.get_inputs()[0].name
    scaler_label_name = scaler_sess.get_outputs()[0].name
    model_input_name = model_sess.get_inputs()[0].name
    model_label_name = model_sess.get_outputs()[0].name
    print("onnx: model_input_name:{}, model_label_name: {}".format(model_input_name, model_label_name))

    indx = []
    rest = []
    sub_factor_name_list = copy.copy(factor_name_list)
    try:
        sub_factor_name_list.remove("ReferenceMidPrice")
    except:
        pass
    for i in range(trainingStep, len(factor_df)):
        tmpdf = factor_df[sub_factor_name_list].iloc[i - trainingStep:i]  # .reshape(-1,120)
        #     print(tmpdf.index[-1])
        tmp = tmpdf.values
        pred_clip = clipper_sess.run([clipper_label_name], {clipper_input_name: tmp.astype(np.float32)})[0]
        pred_scale = scaler_sess.run([scaler_label_name], {scaler_input_name: pred_clip})[0]
        pred_model = model_sess.run([model_label_name], {model_input_name: pred_scale.reshape(-1, len(sub_factor_name_list))})[0]
        indx.append(tmpdf.index[-1])
        rest.append(pred_model[0][0])

    print("Succeed Predict")
    # todo: translate函数中获取probsThreshold
    yhat = pd.DataFrame(rest, index=indx, columns=["yhat"])
    print("yhat shape", yhat.shape)
    return yhat

def compare_signal_line(online_df,offline_df,yhat,d_1,d_2,r_1,r_2):
    '''
    对比线上线下信号的一致性及09:33之前的信号准确性
    param: online_df 线上信号
    param: offline_df 线下信号
    param: d_1,d_2,r_1,r_2,config['udrange']参数，为列表形式
    param: yhat，根据线上因子数据信号生成的yhat
    return
    signal_correlation : 线上线下信号相关性
    stats_dict_diff : 不一致信号的准确率(9:33以前)
    '''
    diff_df = pd.concat([offline_df, online_df]).drop_duplicates(subset=['PERIOD_BEGIN', 'PERIOD_END'],
                                                                            keep=False)
    stats_dict_diff = compute_acc_single(diff_df,d_1,d_2,r_1,r_2)
    stats_dict_diff.reset_index(inplace=True)
    tmp = copy.deepcopy(online_df[["predicted".upper()]])
    tmp["yhat"] = yhat["yhat"]
    signal_correlation = tmp.corr()
    return signal_correlation, stats_dict_diff

def signal_class_consist(online_df,offline_df):
    '''
    计算线上线下信号五分类一致性及不一致性明细
    param: online_df ,线上信号
    param: offline_df,线下信号
    '''
    # 校验实盘和盘后的one-hot编码的一致性

    offline_df["flag"] = offline_df[["D_2", "D_1", "O_1", "R_1", "R_2"]].apply(return_flag, axis=1)
    online_df["flag"] = online_df[["D_2", "D_1", "O_1", "R_1", "R_2"]].apply(return_flag, axis=1)
    offline_df_flag = offline_df[offline_df.flag.isin([-2, -1, 0, 1, 2])][
        ["D_2", "D_1", "O_1", "R_1", "R_2", "flag", "PREDICTED"]]
    online_df_flag = online_df[online_df.flag.isin([-2, -1, 0, 1, 2])][
        ["D_2", "D_1", "O_1", "R_1", "R_2", "flag", "PREDICTED"]]

    concat_df = pd.merge(online_df_flag, offline_df_flag, how="outer", left_index=True, right_index=True)
    concat_df = concat_df[concat_df["flag_y"] != 0]
    concat_df = concat_df[concat_df["flag_x"] != 0]
    concat_df_consist = concat_df[["flag_x", "flag_y"]].corr()
    concat_df_consist_detail = concat_df[concat_df["flag_x"] != concat_df["flag_y"]]

    return concat_df_consist,concat_df_consist_detail

def get_df_order_source(date,strategyname,symbol,save_path,curl_ftp=False):
    '''
    数据库连接，如果save_path存在将数据库查询结果存入指定路径并上传ftp
    :param save_path
    :param ftp是否需要将数据上传到ftp://168.8.2.68/013150
    return
    从数据库查询到的原数据
    '''
    if date == datetime.now().strftime("%Y%m%d"):
        sql_use_real = True
        print(sql_use_real)
    else:
        sql_use_real = False
    db = pymysql1.connect(host='168.11.33.144',
                          port=3307,
                          user='xtraderops',
                          password='wXE1QGmIc3+gDYVOnwrzw37SZN0FBLx9OqBpEGJMVic=',
                          database='ats_quant',
                          )
    if sql_use_real:
        schema = "security"
    else:
        schema = "history_security"

    sql_trade_all = """select * FROM {}.exchangeorder WHERE EntrustType=0 
                AND substring_index(AlgoOrderId,'-',1) = '{}'
               and SecurityId in('{}')
                and tradedate = '{}'""".format(schema,strategyname, symbol.split(".")[0], date)

    df_order_source = pd.read_sql(sql_trade_all, con=db)
    if not df_order_source.empty:
        if save_path:
            df_order_source.to_parquet(save_path)
        if curl_ftp:
            os.system("curl ftp://168.8.2.68/013150/ -T {} -u 'ftphzh:ftphzh2602'".format(save_path))
    if df_order_source.empty:
        print("Online Empty!")
    if df_order_source.empty and os.path.exists(save_path):
        df_order_source = pd.read_parquet(save_path)
    return df_order_source

### 加载线上信号
def load_online_signal(path, symbol, strategymodelmame):
    '''
    从excel加载信号文件并对字段PERIOD_BEGIN、PERIOD_END、PROBABILITY做处理
    param path excel文件路径
    param symbol 标的名
    param strategymodelmame 策略名
    return
    返回线上信号
    '''
    df = pd.read_excel(path, sheet_name=symbol)
    df = df[(df.SYMBOL == symbol) & (df.STRATEGY_NAME == strategymodelmame)]
    df.index = df.PERIOD_BEGIN
    df.index = pd.to_datetime(df.index)
    df["PERIOD_BEGIN"] = df["PERIOD_BEGIN"].apply(pd.to_datetime)
    df["PERIOD_END"] = df["PERIOD_END"].apply(pd.to_datetime)
    tmp_df = df["PROBABILITY"].apply(eval).apply(pd.Series, index=['D_2', 'D_1', 'O_1', "R_1", "R_2"])
    df = pd.merge(df, tmp_df, left_index=True, right_index=True)
    return df

