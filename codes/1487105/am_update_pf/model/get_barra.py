import matplotlib.pyplot as plt
def getStrValueFromLine(line, start_flag, end_flag):
    start_pos = line.find(start_flag)
    if start_pos == -1:
        # print("key:" + key + "not find in line:" + line)
        return None
    end_pos = line.find(end_flag, start_pos+1)
    value = line[start_pos+len(start_flag) : end_pos]
    return value

date = '20200107'
file = '/data/user/012965/Huatai Open Optimizer/ModelsDirect/CNTRD/CNTRD_100_Asset_Exposure.%s' % date

fin = open(file,'r')
stocks = []
values = []
start = 'CNTRD_SIZE|'
ends='|%s' % date
while True:
    line = fin.readline().strip()
    if len(line)==0:
        break
    value = getStrValueFromLine(line,start,ends)
    if value !=None:
        stock = line.split('|')[0]
        stocks.append(stock)        
        values.append(value)   

localid_map= pd.read_csv('/data/user/012620/Barra/CHN_LOCALID_Asset_ID.20200604', sep = '|', skiprows=1, skipfooter=1, engine='python')
localid_map.drop_duplicates(subset='AssetID', inplace=True)
localid_map = localid_map.reset_index(drop=True)
idmap = localid_map.set_index('AssetID')['!Barrid']
localid_map.drop_duplicates(subset='AssetID', inplace=True)

size = pd.DataFrame({'stock':stocks,'size':values})
size.columns=['!Barrid','size']
size = size.merge(localid_map,on='!Barrid')
size=size[['!Barrid','AssetID','size']]
size['stock'] = [i[2:]+ ('.SH' if i[2]=='6' else '.SZ') for i in size['AssetID'].values]


sizeO = pd.read_pickle('/data/user/012620/AlphaDataCenter/Factor/barra/Size.pkl')
size.index = size['stock']
size = size.loc[sizeO.loc[date].index]
size['our_size'] = sizeO.loc[date].values
size[['size','our_size']]=size[['size','our_size']].astype('float')
plt.figure(figsize=(10,3))
plt.plot(size['our_size'].values,size['size'].values,'.')
plt.show()