import os
import sys
import numpy as np
import pandas as pd
import scipy.io as spio
import sys
sys.path.insert(0,'am_update_pf/')
from pf_generator_helper import *
import config_path
from xquant.factordata import FactorData
from xquant.xqutils.helper import link
lm = link.LinkMessage()

s = FactorData()
import datetime
def update_portfolio(capital_fake,reb_path,today,time = '0930',pf_code = '5160803',reb = True,close_after_open = False,
            index_price = 0.,first_open = False,open_capital = 1e9,mode=1,benchmark='500'):
    result1 = s.tradingday(today,-2)
    last_dt = result1[-2]
    today_dt = result1[-1]
    print('time:',time,'last:',last_dt,'today',today_dt)
    model_list = config_path.model_name_map[benchmark][config_path.name_map[time]]
    excess_type = config_path.name_map[time]
    save_weight_path = config_path.weight_path + '/benchmark_'+benchmark+'/'+excess_type+'/'
    order_path = config_path.order_path
    all_name = 'All_'+benchmark
    act_path = config_path.act_path +excess_type+'/'+all_name+'/'
    if '0930' in time:
        get_act(last_dt,model_list,excess_type,all_name,mode=1)
        o32_path = config_path.o32_path + 'morning/综合信息查询_组合证券' + today_dt + '_516.xls'
    elif time == '1300':
        get_act(today_dt,model_list,excess_type,all_name,mode=1)
        o32_path = config_path.o32_path + 'noon/综合信息查询_组合证券_' + today_dt + '_1130.xls'
    o32_path_ = o32_path
    # prepare
    if not first_open:
        try:
            pf, long, short = load_pf(pf_code, o32_path)
        except FileNotFoundError:
            pf, long, short = load_pf(pf_code, o32_path_)
        # last_position, valid_position = (long['持仓'], long['持仓']) if time=='0930' else (long['持仓'], long['T日指令可用数量'])
        last_position, valid_position = (long['持仓'], long['T日指令可用数量'])
        close_price = long['最新价']
        if reb:
            if time[:4] == '0930':
                act = pd.read_csv(act_path + last_dt + '.csv', index_col=0, header=None).T
            else:
                act = pd.read_csv(act_path + today_dt + '.csv', index_col=0, header=None).T
            act.index = [pd.Timestamp(today_dt)]
    print(o32_path,pf_code,str(int(long['市值'].sum()/1e4)))
    # valid_stk = np.load('valid_stock/valid_stock_' + today_dt + '_' + time + '.npy').item()
    valid_stk_ = np.load(config_path.valid_stock_path+ 'valid_stock_' + today_dt + '_' + time[:4] + '.npy').item()
    valid_pre_close = valid_stk_['valid_pre_close']
    maxup_stk = valid_stk_['maxup_stk']
    maxdown_stk = valid_stk_['maxdown_stk']
    trade_stk = valid_stk_['trade_stk']

    # universe = spio.loadmat('/data/group/800020/AlphaDataCenter/PoolManagement/universe.mat', squeeze_me=True)['universe'].tolist()
    # trade_stk = sorted(set(trade_stk).intersection(universe))


    if pf_code=='5160304':
        pf_name = 'BeyondIndex'
        turn_ad = 0.2#0.4
        amt_limit = 0.025   
        single_stock_max_weight=0.005            
        hedge_index = 'HS300'
        barra_limit_dict = {
            'Beta'+hedge_index[-3:]: (0.05, 0.05), 
            'Momentum':              (0.05, 0.05), 
            'Size':                  (0.5, 0.5), #(0.5, 0.5),(0.25, 0.25),
            'Volatility':            (1000, 1000), 
            'EarningsYield':         (1000, 1000), 
            'Liquidity':             (1000, 1000), 
            'Leverage':              (1000, 1000), 
            'Value':                 (1000, 1000), 
            'Growth':                (1000, 1000)
        }
        industry_loose = 0.01
        dupl_industry = [6133,6134]#[6133,613401,613402,613403]
        split_fin = False
        contract_multiplier = 300
        index_w = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/HS300_data.pkl').iloc[-1]
        index_stk = index_w[index_w>0].index.tolist()
        valid_stk = sorted(set(trade_stk)-set(maxup_stk)-set(maxdown_stk))
       
        
    elif pf_code=='5160803':
        pf_name = 'AlphaHunter'
        print(pf_code,pf_name)
        turn_ad = 0.6
        amt_limit = 0.025
        single_stock_max_weight=0.005
        hedge_index = 'ZZ500'
        barra_limit_dict = {
            'Beta'+hedge_index[-3:]: (0.01, 0.01), 
            'Momentum':              (0.01, 0.01), 
            'Size':                  (1000, 1000), 
            'Volatility':            (1000, 1000), 
            'EarningsYield':         (1000, 1000), 
            'Liquidity':             (1000, 1000), 
            'Leverage':              (1000, 1000), 
            'Value':                 (1000, 1000), 
            'Growth':                (1000, 1000)
        }
        industry_loose = 0.05
        dupl_industry = None
        split_fin = False
        contract_multiplier = 200
        valid_stk = sorted(set(trade_stk)-set(maxup_stk)-set(maxdown_stk))


    elif pf_code=='5160503':
        pf_name = 'QuantMachine'
        print(pf_code,pf_name)
        turn_ad = 0.4
        amt_limit = 0.025
        single_stock_max_weight=0.0025
        hedge_index = 'ZZ500'
        barra_limit_dict = {
            'Beta'+hedge_index[-3:]: (0.01, 0.01), 
            'Momentum':              (0.01, 0.01), 
            'Size':                  (1000, 1000), 
            'Volatility':            (1000, 1000), 
            'EarningsYield':         (1000, 1000), 
            'Liquidity':             (1000, 1000), 
            'Leverage':              (1000, 1000), 
            'Value':                 (1000, 1000), 
            'Growth':                (1000, 1000)
        }
        industry_loose = 0.05
        dupl_industry = None
        split_fin = False
        contract_multiplier = 200
        valid_stk = sorted(set(trade_stk)-set(maxup_stk)-set(maxdown_stk))



    print('Opt Setting:',time,pf_code,amt_limit,single_stock_max_weight,industry_loose,barra_limit_dict)
    if not first_open:
        # last_stats = pd.read_excel('stats/' + last_dt + '_' + pf_code + '_组合收益.xlsx', index_col=0, sheet_name='汇总')
        # capital = last_stats.loc[last_dt, '期货规模']
        # # capital = last_stats.loc[last_dt, '现货规模']
        # long_capital = last_stats.loc[last_dt, '现货规模']
        cash = 0.
        # capital = long['市值'].sum()
        capital = short['市值'].sum() + cash
        # print('@ capital(wan):',capital/1e4)
        long_capital = long['市值'].sum()
        
    # close position settings
    # load real-time position and valid stocks if close position after open
    if close_after_open:
        print('close position after open')
        pf, long, short = load_pf(pf_code, '综合信息查询_组合证券_' + today_dt + '.xls') # temporal o32 stats file
        last_position = long['持仓']
        trade_stk = np.load('valid_stk_close_position_' + today_dt + '.npy').tolist()
        capital = long['市值'].sum()
    else:
        # index_price = pd.read_pickle('index_future_data/index_close.pkl').loc[last_dt, hedge_index]
        index_price = pd.read_pickle(config_path.basic_data_path + 'daily/close_000905SH.pkl').loc[last_dt].iloc[0]
        # index_price = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close_000300SH.pkl').loc[last_dt].iloc[0]

    # check the percentage of valid stocks
    is_valid_raw = pd.read_pickle(config_path.basic_data_path + 'daily/is_valid_raw.pkl').iloc[-1]
    print('\npercentage of valid stocks: ', len((set(is_valid_raw.index) & set(trade_stk)) - set(maxup_stk)) / is_valid_raw.shape[0])
    if not first_open:
        print('total asset(wan): ', capital/1e4)
        print('cash: ', cash)
        print('len of valid_stk:',len(valid_stk))   
        
    #rebalance
    # calculate short_capital accroding index close
    short_ = short[['证券名称','持仓','持仓多空标志']]

    label = []
    for i in short_['持仓多空标志'].values:
        if i == '空仓':
            label.append(1)
        else:
            label.append(-1)

    short_['label'] = label
    if time[:4] == '0930':
        close_df = get_index_price(time,last_dt)
    else:
        close_df = get_index_price(time, today_dt)

    multi = []
    price = []
    for i in short_['证券名称'].values:
        if i[:2] == 'IF' or i[:2] == 'IH':
            multi.append(300)
            if i[:2] == 'IF':
                price.append(close_df.loc['000300.SH']['S_DQ_CLOSE'])
            else:
                price.append(close_df.loc['000016.SH']['S_DQ_CLOSE'])
        elif i[:2] == 'IC':
            multi.append(200)
            price.append(close_df.loc['000905.SH']['S_DQ_CLOSE'])

    short_['multi'] = multi
    short_['price'] = price

    short_capital = (abs(short_['持仓'])*short_['label']*short_['multi']*short_['price']).sum()
    
    
    
    if reb:
        if mode == 1:
            capital_input = copy.deepcopy(capital_fake)
        else:
            capital_input = copy.deepcopy(capital)
        today_position, w, fw, asset = pf_generator(act, time, last_position, valid_position, valid_stk, pf_code, \
        turn_ad, hedge_index, capital_input, cash, barra_limit_dict, industry_loose, dupl_industry, split_fin,\
        amt_limit,single_stock_max_weight,short_capital,mode=mode,benchmark=benchmark)
        
        # save daily weight
        w.to_pickle(save_weight_path+'%s.pkl' % today_dt)                                        
        if time == '0930vwap':
            print('0930vwap last_position:',last_position)
            t0_position = cal_t0_position(last_position, today_position, valid_position, trade_stk)
            t0_xlsx = generate_t0_xlsx(t0_position, pf_code, today_dt, time)
            t0_xlsx.to_excel(order_path+'T0_file/'+'T0可用额度_' + pf_code + today_dt + '_' + time + '.xlsx')
        reb_position = cal_reb_position(last_position, today_position, valid_position, valid_stk)        
        reb_xlsx = generate_reb_xlsx(reb_position, pf_code, today_dt, time)
        reb_xlsx.to_excel(reb_path + pf_code + '_rebalance_' + today_dt + '_' + time + '.xlsx')
        reb_xlsx.to_excel(order_path+'Rebalance_file/' + pf_code + '_rebalance_' + today_dt + '_' + time + '.xlsx')
        print(reb_path + pf_code + '_rebalance_' + today_dt + '_' + time + '.xlsx')

        # calculate buy and sell amount
        if time[:4]=='0930':
            close = pd.read_pickle(config_path.basic_data_path + 'daily/close.pkl').loc[last_dt]
        else:
            close = pd.read_pickle(config_path.basic_data_path + 'minute/Close/' + today_dt + '.pkl').iloc[119]
        buy_stk = reb_xlsx[reb_xlsx['委托方向']==1].index.tolist()
        sell_stk = reb_xlsx[reb_xlsx['委托方向']==2].index.tolist()
        buy_amt = (close[buy_stk] * reb_xlsx.loc[buy_stk, '指令数量']).sum()
        sell_amt = (close[sell_stk] * reb_xlsx.loc[sell_stk, '指令数量']).sum()
        print('buy  amount(wan): ', buy_amt/1e4)
        print('sell amount(wan): ', sell_amt/1e4)
        print('reb stocks:',reb_xlsx.shape[0])

        # lm.sendMessage("Short (wan): {0},Long (wan):{1},   buy amount(wan):{2},sell amount(wan):{3},     reb stocks:{4}, {5}".\
        # format(str(int(capital/1e4)),str(int(asset/1e4)),str(int(buy_amt/1e4)),str(int(sell_amt/1e4)),str(reb_xlsx.shape[0]),str(pf_code)))
        if time == '0930vwap':        
            link_str = "{0} 调仓文件和T0文件已上传，调仓股票数量{1},T0股票数量{2}, 换手率{3}%,   空头 (万元): {4},多头 (万元):{5}, 买入金额(万元):{6},卖出金额(万元):{7},{8}".\
                format(str(pf_code),str(reb_xlsx.shape[0]),str(t0_xlsx.shape[0]),str(round(buy_amt/asset*100,2)),\
                    str(int(asset/1e4)),str(int(long['市值'].sum()/1e4)),str(int(buy_amt/1e4)),str(int(sell_amt/1e4)),today_dt)
            lm.sendMessage(link_str) 
        else:
            link_str = "{0} 调仓文件已上传，调仓股票数量{1}, 换手率{2}%,   空头 (万元): {3},多头 (万元):{4}, 买入金额(万元):{5},卖出金额(万元):{6},{7}"\
                .format(str(pf_code),str(reb_xlsx.shape[0]),str(round(buy_amt/asset*100,2)),\
                    str(int(asset/1e4)),str(int(long['市值'].sum()/1e4)),str(int(buy_amt/1e4)),str(int(sell_amt/1e4)),today_dt)
            lm.sendMessage(link_str) 
        print(link_str)
                
    else:
        pass

        
        
        