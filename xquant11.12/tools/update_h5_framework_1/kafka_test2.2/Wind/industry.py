# _*_ coding:utf-8 _*_

from Wind.utils import *

def industry_retriever(cdate_list, save_path):
    industry_code = ['b10100', 'b10200', 'b10300', 'b10400', 'b10500', 'b10600',
        'b10700', 'b10800', 'b10900', 'b10a00', 'b10b00', 'b10c00',
        'b10d00', 'b10e00', 'b10f00', 'b10g00', 'b10h00', 'b10i00',
        'b10j00', 'b10k00', 'b10l00', 'b10n00', 'b10o00', 'b10p00',
        'b10q00', 'b10r00', 'b10s00', 'b10t00','b10m01', 'b10m02', 'b10m03']

    industry_num = [i+1 for i in range(len(industry_code))]
    industry_dict = dict(zip(industry_code,industry_num))
    save_folder = save_path + 'industry_citiccode'+'\\'

    h5_path = '/app/data/wdb_h5/WIND'
    table_name = 'AShareIndustriesClassCITICS'
    table_path = h5_path +  table_name + '\\' + table_name + '.h5'
    for date in cdate_list:
        df = read_data([20090101, 20201231], columns=['CITICS_IND_CODE', 'ENTRY_DT','REMOVE_DT','CUR_SIGN'], alt = table_path)
        # df = df[df['CUR_SIGN'] == 1.0]
        df['REMOVE_DT'].fillna(20990101,inplace=True)
        df = df[df['ENTRY_DT']<=date]
        df = df[df['REMOVE_DT'] >= date]
        def industry_parser(ind_code):
            ind2 = ind_code[:6]
            if 'b10m' in ind2:
                ind_lv2_code = ind2
            else:
                ind_lv2_code = ind2[:4] + '00'
            return ind_lv2_code
        df['lv2_ind_code'] = df['CITICS_IND_CODE'].apply(industry_parser)
        df['lv2_ind_num'] = df['lv2_ind_code'].apply(lambda x:industry_dict[x])
        df.drop(['CITICS_IND_CODE', 'CUR_SIGN','ENTRY_DT','REMOVE_DT','lv2_ind_code', 'lv2_ind_code'], axis=1, inplace=True)
        df.reset_index('dt', inplace=True)
        df.drop('dt', axis=1, inplace=True)
        df.columns = ['industry_citiccode']
        df.to_csv(save_folder+str(date)+'.csv')

def cindustry_retriever(cdate_list,save_path):
    save_folder = save_path + 'KNN_I'+'\\'
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    source_path = 'Z:\\warehouse\\prod\\INDUSTRY\\CHINA_STOCK\\DAILY\\WIND\\INDUSTRY_CHINA_STOCK_DAILY_WIND.h5'
    # source_path = r'Z:\warehouse\prod\INDUSTRY\CHINA_STOCK\DAILY\WIND\tmp.h5'
    map_dict = {29:6,30:7,31:8,21:1,27:2,24:2,26:2,25:2,5:3,2:3,3:3,19:4,18:4,15:5,4:5,11:5,22:5,17:5,
    12:5,10:5,6:5,16:5,8:5,7:5,23:5,20:5,13:5,9:5,14:5,1:5,28:5}
    def helper(df,map_dict):
        x = df['CITIC_I']
        if not x in map_dict:
            return -1
        return map_dict[x]
        # else:
            # print(x)
            # return -1
    for date in cdate_list:
        print(date)
        df = read_data(date,alt= source_path)
        df.reset_index('dt', inplace=True)
        df.drop('dt', axis=1, inplace=True)
        # df.dropna(inplace=True)
        df['KNN_I'] = df.apply(lambda x : helper(x,map_dict),axis=1)
        print(df)
        df.drop(['CITIC_I'],axis=1,inplace=True)
        df.to_csv(save_folder+str(date)+'.csv')