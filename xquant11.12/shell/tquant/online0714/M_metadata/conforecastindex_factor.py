
import pandas as pd

def get_conforecastindex_factor_info():
    data = pd.read_excel("conforecastindex_factor.xlsx", sheet_name=None, header=0, usecols=["因子名称", "中文释义", "来源表"])
    df = data['一致预期']
    df['来源表'] = df['来源表'].apply(lambda x: x.strip().lower())
    df['因子名称'] = df['因子名称'].apply(lambda x: x.strip().lower())
    df['中文释义'] = df['中文释义'].apply(lambda x: x.strip())
    df.rename(columns={'因子名称':'factor','来源表':'source_table','中文释义':'factor_name'},inplace=True)
    tables = list(set(df['source_table'].tolist()))
    factors_info = {}
    for table in tables:
        df_p = df[df['source_table'] == table]
        if isinstance(df_p, pd.Series):
            df_p = pd.DataFrame(df_p).T
        df_p.drop(['source_table'],axis=1,inplace=True)
        df_p.set_index('factor',inplace=True)
        factors_info[table] = df_p.to_dict()["factor_name"]
    return factors_info


if __name__ == "__main__":
    factors_info = get_conforecastindex_factor_info()
    print(factors_info)
