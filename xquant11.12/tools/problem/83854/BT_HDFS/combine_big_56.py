import os
import pickle
import json
from multiprocessing import Pool
from datetime import datetime
from xquant.pyfile.ftp import pyfileFTP
import pandas as pd


import BT.Config as config
order_capacity_path = config.order_capacity_path
trade_path = config.trade_path
root_path = config.root_path



def get_bt_data(target_code, volume, para_split, combine_path, start_date, end_date):
    quantity = {}
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
            if d >= start_date and d <= end_date:
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
        for d in dates:
            if not os.path.exists(trade_path + "/" + c + "/" + d + "/Data.pickle"):
                print (c, d, "not found")
                continue
            with open(trade_path + "/" + c + "/" + d + "/Data.pickle", 'rb') as f:
                data = pickle.load(f)   
            tickData.append(data[0])
            transactionData.append(data[1])
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
    return quantity
    
def combine(target_code, volume, start_date, end_date, combine_name): 
    bt_date_path = root_path + "/" + start_date + "-" + end_date + "/" 
    combine_path = bt_date_path + "/" + combine_name      
    if not os.path.exists(combine_path):
        os.makedirs(combine_path)
       
    quantity = {}
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
        quantity.update(kk.get())   
    with open(combine_path + '/' + combine_name + '_quantity.json', "w") as f:
        json.dump({"Combine": combine_name, "quantity": quantity}, f) 


def combine_trade_and_capacity(start_date, end_date, portfolio="5161101+300", is_calc_portfoilo=True):
  
    ftp = pyfileFTP()
    if is_calc_portfoilo:
        # portfolio = "5161101+300"
        file_name = "{}_{}.xlsx".format(end_date, portfolio)

        # file_name = "{}_5161101+300.xlsx".format(end_date)
        # file_name = "20181224_5161101+alpha.xlsx"
        ftp.downloadFile("666888/"+file_name, "/app/data/666888/ftp_uploads/"+file_name)
        df = pd.read_excel("/app/data/666888/ftp_uploads/"+file_name)
        print(df)
        print("combining {}'s trade and capacity".format(portfolio))
        codes = list([_code for _code in df.iloc[:, 0]] )
        volumes = list([int(_code) for _code in df.iloc[:, 3]])
        combine(codes, volumes, start_date, end_date, portfolio)      
        
                   
      
def main():
    start_date = "20190430"
    end_date =   "20190430"
    # combine_trade_and_capacity(start_date, end_date, portfolio="BigNew")
    combine_trade_and_capacity(start_date, end_date, portfolio="BigOld")

    # from xquant.pyfile import Pyfile
    # py = Pyfile()
    # if py.exists('TEMP'):
        # py.delete('TEMP', recursive=True)
    # py.upload('TEMP/20181019-20181220/5161101+alpha/', '/app/data/666888/BT_Trade_OrderCapacity/20181019-20181220/5161101+alpha/')
    # py.copyToShare('$21/ModelProduction/20180901_end/bt_info/20181019-20181220/5161101+alpha/', 'TEMP/20181019-20181220/5161101+alpha/')
    # py.delete('TEMP', recursive=True)


       