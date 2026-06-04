#mport pandas as pd
import os
import pandas as pd
import random


def list2df(result_list, transpose=True):
    if transpose:
        return pd.DataFrame(result_list).T
    else:
        return pd.DataFrame(result_list)


def get_range_day(sdate, edate, dayType=1):
    """
        :param sdate:  开始日期
        :param edate: 结束日期
        dayType: 0为交易日，1为自然日
        :return:
        """
    if dayType == 0:
        from xquant.factordata import FactorData
        s = FactorData()
        days = s.tradingday(sdate, edate)
        return days
    elif dayType == 1:
        import pandas as pd
        days = pd.date_range(sdate, edate)
        days = [day.strftime("%Y%m%d") for day in days]
        return days

def get_relative_day(date, delta, dayType=0):
    """
    :param date:  原始日期
    :param delta: 转换日期，1表示后一天，-1表示前一天
    dayType: 0为交易日，1为自然日
    :return:
    """
    import datetime
    today = datetime.datetime.now().strftime("%Y%m%d")
    if dayType == 0:
        from xquant.factordata import FactorData
        s = FactorData()
        days = s.tradingday("20090101", today)
        try:
            idx = days.index(date)
        except:
            print(days)
            raise Exception("当前日期不在交易日内{}".format(date))
        return days[idx + delta]
    elif dayType == 1:
        import pandas as pd
        days = pd.date_range("20090101", today)
        days = [day.strftime("%Y%m%d") for day in days]
        try:
            idx = days.index(date)
        except:
            raise Exception("入参日期超出比较范围！")
        return days[idx + delta]


def get_relative_tradingday(date, delta):
    """
    :param date:  原始日期
    :param delta: 转换日期，1表示后一天，-1表示前一天
    :return:
    """
    from xquant.factordata import FactorData
    import datetime
    today = datetime.datetime.now().strftime("%Y%m%d")
    s = FactorData()
    days = s.tradingday("20090101", today)
    idx = days.find(date)
    return days[idx + delta]


def compare_series(s1, s2):
    s1 = s1.reset_index(drop=True)
    s2 = s2.reset_index(drop=True)
    c = s1 == s2
    if c.prod() == 1:
        return True
    else:
        return False


def compare(new_df, old_df, new_compare_col, new_value_col, old_compare_col, old_value_col, sample_ratio=1):
    """
    比较两个dataframe的值是否相同，
    df列共有两种类型，一种compare_col用于join，一种value_col用于比较列是否相等
    sample_ratio:抽样比例，如果比较的dataframe行数太多，抽样部分进行比较
    """
    if old_df.empty:
        old_df = old_df.reindex(columns=old_compare_col + old_value_col)
    if new_df.empty:
        new_df = new_df.reindex(columns=new_compare_col + new_value_col)

    new_df = new_df.loc[:, new_compare_col + new_value_col]
    old_df = old_df.loc[:, old_compare_col + old_value_col]
    old_df.columns = new_df.columns

    merge_df_outer = pd.merge(new_df, old_df, how="outer", left_on=new_compare_col,
                              right_on=new_compare_col, suffixes=("_new", "_old"))
    merge_df_outer = merge_df_outer.fillna(9999999999)

    sample_ids = random.sample(list(merge_df_outer.index),
                               max(1, int(len(merge_df_outer.index) * sample_ratio)))  # 抽样id
    sample_ids = sorted(sample_ids)

    new_value_col1 = [str(col) + "_new" for col in new_value_col]
    old_value_col1 = [str(col) + "_old" for col in new_value_col]

    if sample_ids == 0:
        return pd.DataFrame(columns=new_compare_col + new_value_col1 + old_value_col1 + ["result"])

    merge_df_outer = merge_df_outer.iloc[sample_ids]
    merge_df_outer["result"] = merge_df_outer.apply(
        lambda x: compare_series(x.loc[new_value_col1], x.loc[old_value_col1]), axis=1)

    # merge_df_diff = merge_df_outer[merge_df_outer.loc[:,"result"]==False]
    return merge_df_outer.reindex(columns=new_compare_col + new_value_col1 + old_value_col1 + ["result"])
