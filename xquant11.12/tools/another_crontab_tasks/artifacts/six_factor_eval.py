from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
import pandas as pd
import time
import ray
from xquant.factordata import FactorData
from datetime import datetime, timedelta

# ray.init(num_cpus=8)
fp = FactorProvider("016884")
fd = FactorData()

@ray.remote
def cal_dk_yk_sl_eval(factor_name_list,factor_df,tagger_df,date,stock,df,label_name):
    # 1.获取因子列表\计算时间区间
    factor_df = factor_df[factor_df["M_HTSCSecurityID"]==stock]
    factor_df["date"] = factor_df['timestamp'].dt.strftime('%Y%m%d')
    factor_df = factor_df[factor_df["date"]==date]
    factor_df.drop(columns=['R_HTSCSecurityID',"date","M_HTSCSecurityID"], inplace=True)

    tagger_df = tagger_df[tagger_df["M_HTSCSecurityID"]==stock]
    tagger_df["date"] = tagger_df['timestamp'].dt.strftime('%Y%m%d')
    tagger_df = tagger_df[tagger_df["date"]==date]
    tagger_df.drop(columns=['R_HTSCSecurityID',"date","M_HTSCSecurityID"], inplace=True)
    
    if len(factor_df)==len(tagger_df):        
        df_merge = pd.concat([tagger_df,factor_df],axis=1)
        df_merge=df_merge.drop(["timestamp"],axis=1).fillna(0)
    else:
        df_merge=pd.merge(tagger_df,factor_df,how="inner",on="timestamp")
        df_merge=df_merge.drop(["timestamp"],axis=1).fillna(0)

    # 对每个因子值列进行计算
    factor_cols = df_merge.columns[1:]  # 假设因子值列从第2列开始
    absolute_difference_lis=[]
    profit_loss_ratio_lis=[]
    win_rate_lis=[]

    for factor_col in factor_cols:
        # 计算前10%和后10%的因子值分位数
        q_10th_percentile = df_merge[factor_col].quantile(0.10)
        q_90th_percentile = df_merge[factor_col].quantile(0.90)

        # 计算前10%和后10%的标签总和

        top_10 = df_merge[df_merge[factor_col] >= q_90th_percentile]
        top_10_sum = top_10[label_name].sum()
        bottom_10 = df_merge[df_merge[factor_col] <= q_10th_percentile]
        bottom_10_sum = bottom_10[label_name].sum()
        absolute_difference = abs(top_10_sum - bottom_10_sum)

        # 计算因子前10%和后10%的大于万五和小于负万五标签和
        top_10_label_A5 = top_10[top_10[label_name] >= 0.5][label_name]
        top_10_label_A5_sum = (top_10[top_10[label_name] >= 0.5][label_name]-0.5).sum()
        top_10_label_B_5 = top_10[top_10[label_name] <= -0.5][label_name]
        top_10_label_B_5_sum = abs((top_10[top_10[label_name] <= -0.5][label_name]+0.5).sum())
        bottom_10_label_A5 = bottom_10[bottom_10[label_name] >= 0.5][label_name]
        bottom_10_label_A5_sum = (bottom_10[bottom_10[label_name] >= 0.5][label_name]-0.5).sum()
        bottom_10_label_B_5 = bottom_10[bottom_10[label_name] <= -0.5][label_name]
        bottom_10_label_B_5_sum = abs((bottom_10[bottom_10[label_name] <= -0.5][label_name]+0.5).sum())

        top_10_label_B5_sum = abs((top_10[top_10[label_name] < 0.5][label_name]-0.5).sum())
        top_10_label_A_5_sum = (top_10[top_10[label_name] > -0.5][label_name]+0.5).sum()
        bottom_10_label_B5_sum = abs((bottom_10[bottom_10[label_name] < 0.5][label_name]-0.5).sum())
        bottom_10_label_A_5_sum = (bottom_10[bottom_10[label_name] > -0.5][label_name]+0.5).sum()

        if len(top_10)==0:
            P1=0
            P3=0
        else:
            P1=len(top_10_label_A5)/len(top_10)
            P3=len(top_10_label_B_5)/len(top_10)
        if len(bottom_10)==0:
            P2=0
            P4=0
        else:
            P2=len(bottom_10_label_B_5)/len(bottom_10)
            P4=len(bottom_10_label_A5)/len(bottom_10)

        # 获取因子ic
    #     if ic_df.loc[factor_col,"normal_ic"]>=0:
        if df.loc[factor_col,"normal_ic"]>=0:
            if (top_10_label_B5_sum + bottom_10_label_A_5_sum)==0:
                profit_loss_ratio=0
            else:
                profit_loss_ratio=(top_10_label_A5_sum + bottom_10_label_B_5_sum) / (top_10_label_B5_sum + bottom_10_label_A_5_sum)
            win_rate=(P1+P2)/2
#             win_rate=P1/2

        else:
            if (top_10_label_A_5_sum + bottom_10_label_B5_sum)==0:
                profit_loss_ratio=0
            else:
                profit_loss_ratio=(top_10_label_B_5_sum + bottom_10_label_A5_sum) / (top_10_label_A_5_sum + bottom_10_label_B5_sum)
            win_rate=(P3+P4)/2
#             win_rate=P4/2
        absolute_difference_lis.append(absolute_difference)
        profit_loss_ratio_lis.append(profit_loss_ratio)
        win_rate_lis.append(win_rate)
    res = pd.DataFrame()
    res["多空收益分离"] = absolute_difference_lis
    res["盈亏比"] = profit_loss_ratio_lis
    res["胜率"] = win_rate_lis
    res["日期"] = date
    res.index=factor_cols
    return res

def six_factor_eval(start_date=None,end_date=None,stock_lis=None,factor_name_list=None,trading_frequency=None,label_name=None):
    """计算因子六边形评价"""
    # 1.获取因子列表\计算时间区间
    if factor_name_list==None:
        factor_name_list = list(fp.load_info_from_dfs('factor', source_type='public'))
        
    if start_date==None:
        # 获取当前日期
        current_date = datetime.now().date()
        # 计算去年的今天的日期
        start_date = current_date - timedelta(days=365)
        # 计算昨天的日期
        end_date = current_date - timedelta(days=1)
        # 格式化日期为"20230101"形式
        start_date = start_date.strftime('%Y%m%d')
        end_date = end_date.strftime('%Y%m%d')
    
    # 2.1计算因子相关性、自相关性、收益率显著性（和label的ic，按天平均，多票平均）
    print("开始计算相关性、自相关性、收益率显著性")
    # 2.1.1取现有因子多票多天因子评价数据，并做一定指标运算
    start_time = time.time()
    if trading_frequency=="1s":
        data_type="tick_l2p"
    if trading_frequency=="3s":
        data_type="enhanced_tick"
    factor_eval_data=fp.load_factor_analysis_res(data_type=data_type,
                                    factor_list=factor_name_list,
                                    start_date=start_date,
                                    end_date=end_date,
                                    label_name=label_name)
    df=factor_eval_data.loc[:,["MDDate","factor_name","stock","normal_ic","auto_corr_5","long_p_value_01","short_p_value_01"]]
    if stock_lis==None:
        stock_lis=list(set(factor_eval_data["stock"]))
    else:
        pass
    df = df[df["stock"].isin(stock_lis)]
    df["p_value"]=0.5*(df["long_p_value_01"]+df["short_p_value_01"])
    df=df.drop(["long_p_value_01","short_p_value_01"],axis=1)    
    # 2.1.2按天平均，按票平均
    df_by_day=df.groupby(["stock","factor_name"]).mean()
    df_by_stock=df_by_day.groupby("factor_name").mean()
    df_by_day=df_by_day.reset_index(level='stock')
    
    factor_name_list=list(df_by_stock.index)
#     print(df_by_stock)
#     print(factor_name_list)
#     print(len(factor_name_list))
        
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"计算相关性、自相关性、收益率显著性耗时: {elapsed_time} 秒")
#     df=df.groupby("factor_name").mean()
    
    # 2.2计算因子的多空收益分离、胜率、盈亏比
    # 2.2.1获取factor_df和label_df
    if stock_lis==None:
        stock_lis=list(set(factor_eval_data["stock"]))
    # 2.3计算指标
    # 2.3.1按标的循环
#     stock_lis = ["688599.SH","688363.SH"]#临时测试
    
    res_by_stock=pd.DataFrame()
    print("开始计算胜率、多空收益分离、盈亏比")
    for stock in stock_lis:
        print("开始取数"+stock)
        start_time = time.time()
        # 2.3.2按天并发计算指标值
        date_lis=fd.tradingday(start_date,end_date)
#         print("="*200)
#         print(data_type)
#         print(stock)
#         print(factor_name_list)
#         print(start_date)
#         print(end_date)
        factor_df = fp.load_public_data_from_dfs(
            data_type=data_type,
            symbol= stock,
            factor_list=factor_name_list,
            start_time=start_date,
            end_time=end_date,
            factor_type="factor")
        tagger_df = fp.load_public_data_from_dfs(
            data_type=data_type,
            symbol= stock,
            factor_list=label_name,
            start_time=start_date,
            end_time=end_date,
            factor_type="label")
#         print(factor_df.head(5))
#         print(tagger_df.head(5))
        
        print("开始并发"+stock)
#         for date in date_lis:
#             res1=cal_dk_yk_sl_eval(factor_name_list,factor_df,tagger_df,date,stock,df_by_stock)   
        tasks=[cal_dk_yk_sl_eval.remote(factor_name_list,factor_df,tagger_df,date,stock,df_by_stock,label_name) for date in date_lis]
        ray_res = ray.get(tasks)
        end_time = time.time()
        elapsed_time = end_time - start_time
        # 2.3.3按天平均计算指标值
        res_by_day = pd.concat(ray_res,axis=0)
        res_by_day = res_by_day.groupby([res_by_day.index]).mean()
        res_by_day["stock"]=stock
        print(stock+"done")
        # 2.3.4按票平均计算指标值
        res_by_stock = pd.concat([res_by_stock,res_by_day],axis=0)
        print("计算"+stock+f"多空收益率、盈亏比、胜率耗时: {elapsed_time} 秒")
    # 2.3.4按票平均计算指标值
#     df2 = res_by_stock.groupby([res_by_stock.index]).mean()
#     res=pd.merge(df,df2,left_index=True,right_index=True,how="inner")

    df_by_day["factor_name"]=df_by_day.index
    df_by_day.reset_index(drop=True, inplace=True)
    res_by_stock["factor_name"]=res_by_stock.index
    res_by_stock.reset_index(drop=True, inplace=True)
    res=pd.merge(df_by_day,res_by_stock,how="outer",on=["stock","factor_name"])
    res["lanel_name"]=label_name
    return res
