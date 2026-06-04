import os
import pickle
import json
from multiprocessing import Pool
from datetime import datetime
from xquant.pyfile.ftp import pyfileFTP
import pandas as pd
import uuid






order_capacity_path = "/app/data/666888/OrderCapacity/"
trade_path = "/app/data/666888/TradeData/"
root_path = "/app/data/666888/BT_Trade_OrderCapacity/"



def get_bt_data(target_code, volume, para_split, combine_path, start_date, end_date):
    quantity = {}
    value = {}
    for index in para_split:
        c = target_code[index]
        order_capacity = {"OrderCapacity": {}}
        __fpath = order_capacity_path + "/" + c + '/OrderCapacity.json'
        if not os.path.exists(__fpath):
            print("order capacity not found", c)
            print(__fpath)
            continue
        with open(order_capacity_path + "/" + c + '/OrderCapacity.json', "r") as f:
            capacity = json.load(f)
        code = capacity["code"]
        order_capacity["code"] = code
        if 300000 <= int(code[0: 6]) <= 399999:
            order_capacity["Holo"] = "true"
        else:
            order_capacity["Holo"] = "false"
        dates = []
        for d in capacity["OrderCapacity"]:
            if d >= start_date and d <= end_date and d != '20190112':
                dates.append(d)
        if len(dates) == 0:
            print ("no trade dates", c)
            continue
        # print (c)
        dates.sort()
        for d in dates:
            order_capacity["OrderCapacity"][d] = capacity["OrderCapacity"][d] 
        tickData = []
        transactionData = []
        for i in range(len(dates)):
            d = dates[i]
            if not os.path.exists(trade_path + "/" + c + "/" + d + "/Data.pickle"):
                print (c, d, "not found")
                continue
            with open(trade_path + "/" + c + "/" + d + "/Data.pickle", 'rb') as f:
                data = pickle.load(f)   
            tickData.append(data[0])
            transactionData.append(data[1])
            if i == 0:
                preClose = data[0]['PreClose'][0]
        out_path = combine_path + '/' + c + "/"
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        with open(out_path + "/Data.pickle" , 'wb') as f:
            pickle.dump((tickData, transactionData), f)
            
        with open(out_path + '/OrderCapacity.json', "w") as f:
            json.dump(order_capacity, f)   
            
        with open(out_path + '/Dates.json', "w") as f:
            json.dump({"Dates": dates}, f) 
            
        quantity[c] = volume[index]
        value[c] = quantity[c] * preClose
    return quantity, value
    
def combine(target_code, volume, start_date, end_date, curr_date, combine_name): 
    bt_date_path = root_path + "/" + start_date + "-" + end_date + '_' + curr_date + "/"
    combine_path = bt_date_path + "/" + combine_name      
    if not os.path.exists(combine_path):
        os.makedirs(combine_path)
       
    quantity = {}
    value = {}
    processNum = 6
    para_split = []
            
    for index in range(processNum):
        para_split.append([])
        
    count = 0    
    for index in range(len(target_code)):
        para_split[count].append(index)
        count = count + 1
        if count >= processNum:
            count = 0
        
    pool = Pool(processes=processNum)
    multiProcessResult = []
    for ii in range(para_split.__len__()):
        result = pool.apply_async(get_bt_data, (target_code, volume, para_split[ii],combine_path, start_date, end_date))
        multiProcessResult.append(result)
    pool.close()
    pool.join()
    for kk in multiProcessResult:
        quantity.update(kk.get()[0])
    for vv in multiProcessResult:
        value.update(vv.get()[1])
    with open(combine_path + '/' + combine_name + '_quantity.json', "w") as f:
        json.dump({"Combine": combine_name, "quantity": quantity, "value": value}, f) 


def combine_trade_and_capacity(portfolio, start_date, end_date, curr_date):

    ftp = pyfileFTP()

    
    # file_name = "{}_5161101+alpha.xlsx".format(end_date)
    file_name = "{}.xlsx".format(portfolio)
    ftp.downloadFile("666888/AT/"+file_name, "/app/data/666888/ftp_uploads/"+file_name)
    df = pd.read_excel("/app/data/666888/ftp_uploads/"+file_name)
    print("combining {}'s trade and capacity".format(portfolio))
    codes = list([_code for _code in df.iloc[:, 0]] )
    volumes = list([int(_code) for _code in df.iloc[:, 3]] )
    combine(codes, volumes, start_date, end_date, curr_date, portfolio)  
       
      
def main():
    portfolio = 'AT500'
    start_date = "20190301"
    end_date = "20190430"
    curr_date = 'TEST'
    folder_temp_name = 'TEMP+{}'.format(str(uuid.uuid1()))
    combine_trade_and_capacity(portfolio, start_date, end_date, curr_date)
    from xquant.pyfile import Pyfile
    py = Pyfile()
    if py.exists(folder_temp_name):
        py.delete(folder_temp_name, recursive=True)
    py.upload('{}/{}-{}_{}/{}/'.format(folder_temp_name, start_date, end_date, curr_date, portfolio), '/app/data/666888/BT_Trade_OrderCapacity/{}-{}_{}/{}/'.format(start_date, end_date, curr_date, portfolio))
    py.copyToShare('$21/ModelProduction/20190101_48_end/bt_info/{}-{}_{}/{}/'.format(start_date, end_date, curr_date, portfolio), '{}/{}-{}_{}/{}/'.format(folder_temp_name, start_date, end_date, curr_date, portfolio))
    py.delete(folder_temp_name, recursive=True)

