from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
import pandas as pd
import datetime
import os
from xquant.factordata import FactorData
fd = FactorData()
fp = FactorProvider("016869")


def load_depend_data(target_securities, start_date, end_date):
    """

    :param target_securities:
    :param start_date:
    :param end_date:
    :return:
    """
    #df = fp.get_market_data(target_securities, start_date,  end_date, 'sh_stock_tick_enhanced')
    df = fp.get_market_data(target_securities, start_date,  end_date, 'sh_stock_tick')
    return df


def calc_label_data(target_securities, start_date, end_date, depend_df, custom_params):
    """

    :param target_securities: list 输入数据中包含的标的
    :param start_date: str 形如：20230626 输入数据中包含的开始时间
    :param end_date: str 形如：20230626 输入数据中包含的结束时间
    :param depend_df: pd.DataFrame 用于计算标签数据的行情输入数据
    :param custom_params: 用户自定义参数
    :return: df,一共三列，timestamp HTSCSecurityID,标签名称
    """
    # ???????????
    # ??????????it??????
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"../labels/InfoTech/star_tagger")))
    from src.tagger_calculator import TagCalculator
    from src.tagger_data import TaggerData
    triple_barrier_config_v2 = [
    {
        "class_name": "TripleBarrierTaggerV2",
        "param": {
            "base_name": "triplebarriertaggerv2",
            "label_coeff": 1000,
            "d_size": 120,
            "step_increment": 1,
            "price_type": "midprice",
            "volatility_px": "midprice",
            "num_diff_tick": 1,
            "barrier": 1,
        }
    }
]

    depend_df["timestamp"] = depend_df.apply(lambda x: datetime.datetime.combine(
            x['MDDate'], x['MDTime']),
            axis=1)
    depend_df.reset_index(drop=True, inplace=True)
    depend_df.set_index("timestamp", drop=True, inplace=True)
    depend_df["MDDate"] = depend_df.index.date

    calc_res_list = []
    for security in target_securities:

        data_config_dict_year = {
    			"symbol": [security],
    			"symboltype": 'stock',
    			"start_time": start_date,
    			"end_time": end_date,
    			"source": "xquant",
    			"raw_name_list": [
        			"Sell1Price","Buy1Price"
    			],
    			"n_job":32
    			}
        input_df = depend_df[depend_df['HTSCSecurityID']==security]
        tag_config = triple_barrier_config_v2
        tagger_data = TaggerData(input_df, data_config_dict_year)
        tag_calculator = TagCalculator(tag_config)
        res = tagger_data.get_labels_ready(tag_calculator)
        res['HTSCSecurityID'] = security
        res = res.reset_index()
        print(res)
        calc_res_list.append(res)
    calc_res = pd.concat(calc_res_list)
    return calc_res


def save_label_data(label_df):
    res = fp.save_public_data_to_dfs(label_df,'label','enhanced_tick')
    return res


def main(target_securities, start_date, end_date, **custom_params):
    depend_df = load_depend_data(target_securities, start_date, end_date)
    label_df = calc_label_data(target_securities, start_date, end_date, depend_df, **custom_params)
    save_label_data(label_df)


if __name__ == "__main__":
    cur_date = datetime.datetime.now().strftime("%Y%m%d")
    parse_date = fd.tradingday(cur_date, -1)
    target_securities = ['688599.SH','688012.SH']
    start_date, end_date = parse_date, parse_date
    start_date,end_date = "20230505","20230505"
    main(target_securities=target_securities, start_date=start_date, end_date=end_date)
