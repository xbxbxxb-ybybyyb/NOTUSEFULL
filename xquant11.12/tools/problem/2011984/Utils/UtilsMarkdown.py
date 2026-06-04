def md_dataframe(df, index=False):
    # 将DataFrame格式转换为markdown格式并输出
    def delete_link(list_):
        return [str(x) for x in list_]
        # return [f'<span>{x}<span>' if '.' in str(x) else str(x) for x in list_]

    print('|' + '|'.join(delete_link(list(df.columns))) + '|')
    print('|' + '|'.join([':---:'] * df.shape[1]) + '|')
    for _, row in df.iterrows():
        print('|' + '|'.join(delete_link(list(row))) + '|')
