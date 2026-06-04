import os
import json
import copy
from copy import deepcopy
import numpy as np
import pandas as pd
from pickle import load,dump
from config_path import * 
quarter_path = basic_data_path+'quarter/'
est_path = basic_data_path+'est/'
minute_path = basic_data_path+'minute/'
Minute_Status_path = minute_path

class AlphaFactor(object):


    def __init__(self, json_path):

        with open(json_path) as json_data:
            self.__info = json.load(json_data)
        self.__start_date = '20150101'
        self.__end_date = '20150101'
        self.__minute_date_list =[]
        self.__minute_map_reverse ={}
        self.__all_basic, self.__basic_catalog = self.__catalog_data(basic_data_path)
        self.__all_factor, self.__factor_catalog = self.__catalog_data(factor_data_path)
        self.__all_help = self.__catalog_help(factor_help_path)
        self.__all_quarter = self.__catalog_help(quarter_path)
        self.__all_est = self.__catalog_help(est_path)
        self.__minute_map = self.__get_minute_map()
        self.__hf_delta ={0:30,1:120,2:180}
        self.__hf_hour={0:10,1:13,2:14}
        self.__check_info()

        self.__data = self.__load_data()


    def __check_info(self):

        # check json file keys
        default_param = ['def_arg', 'prelength','type']
        most_param = ['def_arg', 'prelength', 'min_prelen','mode','type','hf_type']

        key_diff_default = list(set(self.__info.keys()).difference(most_param))
        default_diff_key = list(set(default_param).difference(self.__info.keys()))
        assert len(key_diff_default)==0, 'unnecessary param defined in json: %r' %key_diff_default
        assert len(default_diff_key)==0, 'missing param in json: %r' %default_diff_key

        # check def_arg

        for a in self.__info['def_arg']:
            if (a not in self.__all_basic and a not in self.__all_factor and a not in self.__all_help and a not in self.__all_quarter 
                and a not in self.__minute_map.keys() and not isinstance(a, (int, float)) and not os.path.exists(a)):
                raise AssertionError('wrong definition argument %s' %a)

        # check prelength
        if(self.__info['prelength']!='inf'):
            assert int(self.__info['prelength'])>=0, 'prelength less than 0 and not inf'
            
        # check minute prelength
        if('min_prelen' in self.__info.keys()):
            assert int(self.__info['min_prelen'])>=0, 'min_prelen less than 0 '
        else:
            self.__info['min_prelen'] = 0
        # check mode
        if('mode' in self.__info.keys()):
            assert int(self.__info['mode']) in [0,1], 'mode is only 0 or 1'
        else:
            self.__info['mode'] = 0
        # check type
        if('hf_type' in self.__info.keys()):
            assert int(self.__info['hf_type']) in [0,1,2], 'mode is only 0 or 1 or 2'
      
        factor_type = ['daily','minute','barra','est','call_auction','hf']
        assert self.__info['type'] in factor_type, 'wrong type, %s' %self.__info['type']


    def __catalog_data(self, catalog_path):

        all_data = []
        catalog = {}
        catalog_type = os.listdir(catalog_path)
        catalog_type = [type for type in catalog_type if os.path.isdir(catalog_path + type + '/')]
        for t in catalog_type:
            data_list = os.listdir(catalog_path + t + '/')
            data_list = [d[:-4] for d in data_list]
            all_data += data_list
            catalog[t] = data_list

        return all_data, catalog


    def __catalog_help(self,factor_help_path):

        data_list = os.listdir(factor_help_path)
        data_list = [d[:-4] for d in data_list]

        return data_list


    def __load_data(self):

        data = {}
        for a in self.__info['def_arg']:

            if a in self.__all_basic:
                for t in self.__basic_catalog.keys():
                    if a in self.__basic_catalog[t]:
                        data[a] = pd.read_pickle(basic_data_path + t + '/' + a + '.pkl')
                        break
            elif a in self.__all_factor:
                for t in self.__factor_catalog.keys():
                    if a in self.__factor_catalog[t]:
                        data[a] = pd.read_pickle(factor_data_path + t + '/' + a + '.pkl')
                        break
            elif a in self.__all_quarter:
                data[a] = pd.read_pickle(quarter_path + t + '/' + a + '.pkl')
            
            elif a in self.__all_help:
                file = open(factor_help_path + '/' + a + '.pkl','rb')
                data[a] = load(file)
                file.close()
        return data

    def __find_idx(self,df_factor,factor_name, type_factor='daily'):
        date_list = df_factor.index
        # print(start_date,date_list[0])
        # assert self.__start_date >= date_list[0], 'start date < first date in %s' %factor_name
        if factor_name in self.__all_est:
            is_valid = pd.read_pickle(basic_data_path + 'daily/is_valid.pkl')
#             is_valid.index = [self.trans_delta(idx) for idx in is_valid.index.tolist()]
            assert self.__end_date <= is_valid.index[-1], 'end date > last date in %s' %factor_name
            if is_valid.index[-1] != self.__data[factor_name].index[-1]:
                self.__data[factor_name] = deepcopy(pd.concat([self.__data[factor_name],is_valid[-1:]]))
            
                factor_check = deepcopy(self.__data[factor_name][~self.__data[factor_name].index.duplicated(keep='first')])
                assert len(factor_check) == len(self.__data[factor_name])
                self.__data[factor_name] = self.__data[factor_name].shift(1).iloc[1:] 
            date_list = self.__data[factor_name].index
#         print(self.__end_date,date_list[-1])
#         assert self.__end_date <= date_list[-1], 'end date > last date in %s' %factor_name
        assert len(date_list[date_list >= self.__start_date])>0,'no trading day in the input time interval '
        temp_start_date = date_list[date_list >= self.__start_date][0]
        if(self.__info['prelength'] == 'inf'):
            temp_start_idx=0
        elif(type_factor == 'minute'):
            if(self.__info['mode'] == 0):
                temp_start_idx = date_list.tolist().index(temp_start_date) - (self.__info['min_prelen']+2*self.__info['prelength'])
            elif(self.__info['mode']==1):
                temp_start_idx = date_list.tolist().index(temp_start_date) - (self.__info['min_prelen'])
        else:
            temp_start_idx = date_list.tolist().index(temp_start_date) - (self.__info['min_prelen']+2*self.__info['prelength'])
        
        # temp_start_idx = np.where(date_list == start_date)[0][0] - self.__info['prelength']
        if temp_start_idx < 0:
            temp_start_idx = 0
        start_idx = date_list[temp_start_idx]       
        end_idx = date_list[date_list <= self.__end_date][-1]
        return start_idx,end_idx
        
    def __parse_arg(self, start_date, end_date):

     
        assert start_date <= end_date, 'wrong start and end date: start date > end date'
        fmt ="%Y%m%d"
        def_arg = []
        start_idx = {}
        end_idx = {}
        minute_start_idx = {}
        minute_end_idx = {}
        dict_param_num=0
        for a in self.__info['def_arg']:
            if a in self.__data.keys():

                if isinstance(self.__data[a],dict):
                    dict_param_num+=1
                    dict_key =list(self.__data[a].keys())
                    assert len(dict_key)>0,'%s dict is null' %a
                    start_idx[a],end_idx[a] = self.__find_idx(self.__data[a][dict_key[0]],a)
                    
                    for f in dict_key:
                        self.__data[a][f] = self.__data[a][f].loc[start_idx[a]:end_idx[a]]
                    def_arg.append(self.__data[a] )
                    continue

                start_idx[a],end_idx[a] = self.__find_idx(self.__data[a],a)
                def_arg.append(deepcopy(self.__data[a].loc[start_idx[a]:end_idx[a]]))

            elif a in self.__minute_map.keys():
                is_valid = pd.read_pickle(basic_data_path + 'daily/is_valid.pkl')
#                 is_valid.index = [self.trans_delta(idx) for idx in is_valid.index.tolist()]
                minute_start_idx[a],minute_end_idx[a] = self.__find_idx(is_valid,a,'minute')
                date_list = is_valid.loc[minute_start_idx[a]:minute_end_idx[a]].index.tolist()
                self.__minute_date_list = date_list
                this_minute_date_list = self.__minute_date_list[0:self.__info['min_prelen']+1]
                
                df_minute_data = None
                for date in this_minute_date_list:
                    df_date_minute = pd.read_pickle(minute_path + self.__minute_map[a] + '/'+ date.strftime(fmt) + '.pkl')
                    if(df_minute_data is None):
                        df_minute_data = df_date_minute
                    else:
                        df_minute_data = df_minute_data.append(df_date_minute)
                def_arg.append(df_minute_data)
                self.__minute_map_reverse[a] = df_minute_data
            else:
                def_arg.append(a)
        if len(set(list(start_idx.values()))) > 1:

            for k,v in start_idx.items():
                print('start date: ', v, ' : ', k)

            raise AssertionError('inconsistent start date of definition factors due to inconsistent factor date list in db')
            
        if len(set(list(end_idx.values()))) > 1:

            for k,v in end_idx.items():
                print('end date: ', v, ' : ', k)

            raise AssertionError('inconsistent end date of definition factors due to inconsistent factor date list in db')
        if len(set(list(minute_start_idx.values()))) > 1:

            for k,v in minute_start_idx.items():
                print('start date: ', v, ' : ', __minute_map[k] )

            raise AssertionError('inconsistent start date of definition factors due to inconsistent factor date list in db')
            
        if len(set(list(minute_end_idx.values()))) > 1:

            for k,v in minute_end_idx.items():
                print('end date: ', v, ' : ', __minute_map[k] )

            raise AssertionError('inconsistent end date of definition factors due to inconsistent factor date list in db')
        return def_arg

    def __get_minute_map(self):
        origin_minute_name = ['Open','Close','High','Low','Volume','Amount']
        user_minute_name = ['MinuteOpen','MinuteClose','MinuteHigh','MinuteLow','MinuteVolume','MinuteTurnover']
        minute_map = {}
        for i in range(len(user_minute_name)):
            minute_map[user_minute_name[i]] = origin_minute_name[i]
        return minute_map
    def __check_not_full_null(self, factor,df_update):
        for i in range(len(df_update)):
            num_valid_entry = np.sum(pd.notnull(df_update.iloc[i]))
            if(num_valid_entry==0):
                print('warning: invalid update for ', factor+' in '+ df_update.index[i].strftime('%Y%m%d'))
    def __check_minute_status(self,help_update,origin_Minute_Status,min_prelen):
        
        Minute_Status = copy.deepcopy(origin_Minute_Status)

        arr = Minute_Status.values == 0
        Minute_Status = Minute_Status[pd.DataFrame(arr, columns=Minute_Status.columns, index=Minute_Status.index)]
        
        Minute_Status = Minute_Status.replace(np.nan,1)
        
        arr = 1-Minute_Status.values
        Minute_Status = pd.DataFrame(arr, columns=Minute_Status.columns, index=Minute_Status.index)
        
        Minute_Status = Minute_Status.loc[:help_update.index[-1]].iloc[-min_prelen-1:]
        Minute_Status = Minute_Status.rolling(min_prelen+1).mean()
        
        arr = Minute_Status.loc[help_update.index].values >= (1/2)
        help_update = help_update[pd.DataFrame(arr, columns=Minute_Status.columns, index=Minute_Status.loc[help_update.index].index)]
        return help_update
    def get_key (dic, value):

        return [k for k, v in dict.items() if v == value]
    
    def __concat_data(self,update_data):
        store_data=None
        factor = self.__class__.__name__
        if isinstance(update_data[0],dict):
            store_data= update_data[0]
            for f in store_data:
                list_data = [v[f].iloc[-1:] for v in update_data]   
                store_data[f] = pd.concat(list_data)
                store_data[f] = store_data[f].loc[~store_data[f].index.duplicated(keep='last')].sort_index()
                start_idx,end_idx = self.__find_idx(store_data[f],f) 
                store_data[f] = store_data[f].loc[start_idx:end_idx]
                self.__check_not_full_null(f,store_data[f])     
                
        elif isinstance(update_data[0],pd.DataFrame):
            update_data = [v.iloc[-1:] for v in update_data]
            store_data = pd.concat(update_data)
            store_data = store_data.loc[~store_data.index.duplicated(keep='last')].sort_index()
            start_idx,end_idx = self.__find_idx(store_data,factor)
            store_data = store_data.loc[start_idx:end_idx]

            self.__check_not_full_null(factor,store_data)
        return store_data
    
    def minute_help(self,func,help_factor,*args):
        fmtHMS = '%H%M%S'
        fmt = '%Y%m%d'
        factor = self.__class__.__name__
#         help_update = func(*args)
        store_data = []
        tmp_param_list=list(args)
        pre_param_list=list(args)
        origin_Minute_Status = pd.read_pickle(Minute_Status_path+'Minute_Status.pkl')
        for i in range(0,len(self.__minute_date_list)-self.__info['min_prelen'],1):
            this_minute_date = self.__minute_date_list[i+self.__info['min_prelen']]
            this_minute_date_list = self.__minute_date_list[i:i+self.__info['min_prelen']+1]
            str_func = 'func('
            if(len(args)>0):
                for j in range(len(args)):
                    if(isinstance(args[j],pd.DataFrame) and args[j].index[0].strftime(fmtHMS)=='093000'):
                        timeline = 240
                        if self.__info['type'] == 'hf':
                            timeline = self.__hf_delta[self.__info['hf_type']]
                        if(i == 0):
                            first_time = 240*self.__info['min_prelen']
                            tmp_param_list[j] = args[j].iloc[:first_time+timeline]
                        else:
                            min_value_list =list(self.__minute_map_reverse.values())
                            for m in range(len(min_value_list)):
                                if(min_value_list[m].equals(args[j])):
                                    min_key = list(self.__minute_map_reverse.keys())[m]
                                    break
                            fact_min_name = self.__minute_map[min_key]
                        
                            df_date_minute = pd.read_pickle(minute_path + fact_min_name + '/'+ this_minute_date.strftime(fmt) + '.pkl')
                        
                            tmp_data_minute = df_date_minute.iloc[:timeline]
                            if(len(args[j].index)>240):
                                tmp_param_list[j] = pd.concat([pre_param_list[j].iloc[240:],tmp_data_minute])
                                pre_param_list[j] = pd.concat([pre_param_list[j].iloc[240:],df_date_minute])
                            else:
                                tmp_param_list[j] = tmp_data_minute
                                pre_param_list[j] = df_date_minute
                    else:
                        if(self.__info['type']=='hf'):
                            tmp_param_list[j] = args[j].loc[this_minute_date_list[:-1]]
                        else:
                            tmp_param_list[j] = args[j].loc[this_minute_date_list]
                    str_func = str_func + 'tmp_param_list['+str(j)+']'
                
                    if(j!=len(args)-1):
                        str_func+=','
                    else:
                        str_func+=')'
            help_update = eval(str_func)
            if(isinstance(help_update,pd.DataFrame)):
                help_update = help_update.iloc[-1]
            if(isinstance(help_update,pd.Series)):
                help_update = help_update.to_frame().T
                help_update.index=[this_minute_date]
                help_update = self.__check_minute_status(help_update,origin_Minute_Status,self.__info['min_prelen'])
            if(isinstance(help_update,dict)):
                for k in help_update:
                    if(isinstance(help_update[k],pd.DataFrame)):
                        help_update[k] = help_update[k].iloc[-1]
                    help_update[k] = help_update[k].to_frame().T
                    help_update[k].index=[this_minute_date]
                    help_update[k] = self.__check_minute_status(help_update[k],origin_Minute_Status,self.__info['min_prelen'])         
            store_data.append(help_update)
        store_data = self.__concat_data(store_data)  
        return store_data
    def trans_hour(self,date):
        if(self.__info['type']=='hf'):
            return date + pd.Timedelta(hours = self.__hf_hour[self.__info['hf_type']])
        return date
    def calculate(self, start_date, end_date):
        is_valid = pd.read_pickle(basic_data_path+'daily/is_valid.pkl')

        if(isinstance(start_date,int)):
            start_date = str(start_date)
        if(isinstance(end_date,int)):
            end_date = str(end_date)
        start_date = is_valid.loc[start_date:].index[0]
        end_date = is_valid.loc[:end_date].index[-1]

#         start_date = self.trans_hour(start_date)
#         end_date = self.trans_hour(end_date)
        self.__start_date = start_date
        self.__end_date = end_date
        def_arg = self.__parse_arg(start_date, end_date)
        factor_data = self.definition(*def_arg)
        if isinstance(factor_data, dict):
            for k in factor_data.keys():
                factor_data[k] = factor_data[k].loc[start_date:end_date]
        elif isinstance(factor_data, pd.DataFrame):
            factor_data = factor_data.loc[start_date:end_date]
        else:
            raise AssertionError('wrong return type in factor definition')
        
        return factor_data


    def definition(self):
        raise NotImplementedError