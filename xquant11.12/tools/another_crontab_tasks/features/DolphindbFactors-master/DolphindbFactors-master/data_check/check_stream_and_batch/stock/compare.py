import pandas as pd
import datetime as dt
from decimal import *
getcontext().rounding = "ROUND_HALF_UP"
pd.set_option('display.float_format',lambda x : '%.6f' % x)
pd.set_option('display.max_columns', 5000)
pd.set_option('display.max_rows', 3000)
pd.set_option('display.width', 10000)


def compare(path_batchFactor, path_replayFactor, path_result, precision=4):
    batchFactor = pd.read_csv(path_batchFactor)
    if "Unnamed: 0" in batchFactor.columns.to_list():
        del batchFactor["Unnamed: 0"]
    replayFactor = pd.read_csv(path_replayFactor)
    if "Unnamed: 0" in replayFactor.columns.to_list():
        del replayFactor["Unnamed: 0"]
    # replayFactor = pd.read_csv("/tmp/pycharm_project_609/data/rseEngineOutput_20221226.csv")
    batchFactor['timestamp'] = batchFactor['timestamp'].apply(lambda x: dt.datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
    replayFactor['timestamp'] = replayFactor['timestamp'].apply(lambda x: dt.datetime.strptime(x, '%Y.%m.%dT%H:%M:%S.000'))

    tmp = set(replayFactor.columns.to_list()) - set(batchFactor.columns.to_list())
    if len(tmp - {'HTSCSecurityID'}) > 0:
        print(f"回放有，跑批没有的因子 : {tmp - {'HTSCSecurityID'}}")
        print('-'*100)
    tmp = set(batchFactor.columns.to_list()) - set(replayFactor.columns.to_list())
    if len(tmp - {'R_HTSCSecurityID', 'M_HTSCSecurityID'}) > 0:
        print(f"跑批有，回放没有的因子 : {tmp - {'R_HTSCSecurityID', 'M_HTSCSecurityID'}}")
        print('-'*100)
    factors = sorted(list(set(batchFactor.columns.to_list()).intersection(set(replayFactor.columns.to_list())) - {"timestamp"}))
    # 可指定校验哪些因子
    # factors = ['FactorGuangFaTechIndicatorSROC']
    # print(f"共有因子 : {factors}")
    # print('-'*100)

    merge_df = pd.merge(batchFactor, replayFactor, left_on=['timestamp', 'M_HTSCSecurityID'],right_on=['timestamp','HTSCSecurityID'],
                        how='outer', suffixes=("_batch", "_replay"))
    columns_batch = [x + '_batch' for x in factors]
    columns_replay = [x + '_replay' for x in factors]
    extra = merge_df[merge_df[columns_batch].isna().all(1)]
    if len(extra) > 0:
        print(f"replay 比 batch 存在多的数据，如下：")
        #print(extra)
        print('-' * 50)
        merge_df.drop(extra.index, inplace=True)
    missing = merge_df[merge_df[columns_replay].isna().all(1)]
    if len(missing) > 0:
        print(f"replay 比 batch 存在缺少数据，如下：")
        #print(missing)
        print('-' * 50)
        merge_df.drop(missing.index, inplace=True)

    print(f"剔除多余和缺少的数据后，逐列对比...")
    columns_zip = list(zip(columns_batch, columns_replay))
    corr_all = pd.DataFrame()
    wrong_all = pd.DataFrame()
    for x, y in columns_zip:
        df_zip = merge_df[['timestamp', 'M_HTSCSecurityID', x, y]]
        #print(df_zip)
        # 2022.03.07T09:30:00.000
        df_zip['date'] = df_zip['timestamp'].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S").split(" ")[0].replace("-",""))
        corr_1 = df_zip.groupby('date')[[x,y]].corr()
        corr_1 = corr_1[corr_1.index.get_level_values(1)==y][[x]]
        corr_1 = corr_1.mean().values[0]
        print(corr_1)
        del df_zip['date']
        #corr_1 = df_zip[[x, y]].corr()
        #print(corr_1)
        #corr_1.columns = ['batch', 'real']
        #corr_1['factor'] = x.replace("_batch","")
        #print(corr_1)
        corr_all = corr_all.append(pd.DataFrame([[x.replace("_batch",""),corr_1]],columns=['factor','corr']))

        if df_zip[x].dtype == 'float64':
            # 保留4位小数校验
            df_zip_1 = df_zip.copy()
            df_zip_1.loc[:, x] = df_zip_1.loc[:, x].apply(lambda x: Decimal(x).quantize(Decimal('0.' + '0' * precision)))
            df_zip_1.loc[:, y] = df_zip_1.loc[:, y].apply(lambda x: Decimal(x).quantize(Decimal('0.' + '0' * precision)))
            df_zip_1.loc[:, 'comp'] = df_zip_1.loc[:, x] == df_zip_1.loc[:, y]
            df_zip_1 = df_zip_1[df_zip_1['comp'] == False]
            # 增加第五位小数校验，解决四舍五入问题，如0.1500与0.1499保留1位小数
            df_zip_2 = df_zip.loc[df_zip_1.index]
            df_zip_2.loc[:, x] = df_zip_2.loc[:, x].apply(lambda x: Decimal(x).quantize(Decimal('0.' + '0' * (precision + 1))))
            df_zip_2.loc[:, y] = df_zip_2.loc[:, y].apply(lambda x: Decimal(x).quantize(Decimal('0.' + '0' * (precision + 1))))
            df_zip_2.loc[:, 'comp'] = df_zip_2.loc[:, x] == df_zip_2.loc[:, y]
            wrong_col = df_zip_2[df_zip_2['comp'] == False].copy()
            wrong_col[[x, y]] = wrong_col[[x, y]].astype(float)
        else:
            wrong_col = df_zip[df_zip[x] != df_zip[y]]
            wrong_col.loc[:, 'comp'] = False
        wrong_col = wrong_col[~wrong_col[[x, y]].isna().all(1)]
        if len(wrong_col) > 0:
            #print(wrong_col.head(3))
            del wrong_col["comp"]
            wrong_col.columns = ["timestamp", "M_HTSCSecurityID", "batch", "replay"]
            wrong_col.insert(0, "factor", x.replace("_batch", ""))
            wrong_all = wrong_all.append(wrong_col)
        #     print(f"[{x}, {y}] 异常，打印了100-150行，小于100行打印所有，不一致数据量/总数据量：{len(wrong_col)} / {len(merge_df)}：")
        #     if len(wrong_col) <= 100:
        #         print(wrong_col)
        #     else:
        #         print(wrong_col.iloc[100:150, :])
        #     print('-'*50)
        # else:
        #     print(f"[{x}, {y}] 一致")
        #     pass

    print(corr_all)
    print(wrong_all)
    with pd.ExcelWriter(path_result) as writer:
        corr_all.to_excel(writer, sheet_name="corr_all")
        wrong_all.to_excel(writer, sheet_name="wrong_all")


if __name__ == '__main__':
    compare(path_batchFactor="./res_batch_688599.csv",
            path_replayFactor="./res_replay_688599.csv",
            path_result = "./aaa.xlsx",
            precision=4)

