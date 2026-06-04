import dolphindb as ddb
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from update_dol_market_sz_enhanced_tick_daily import main as update_sz_md_enhanced_tick
from update_dol_market_sh_enhanced_tick_daily import main as update_sh_md_enhanced_tick
from update_dol_market_all_tick_l2p_daily import calc_tick_persec_his_date as update_all_md_tick_l2p
from update_dol_factor_daily_enhanced_tick_norm import main as update_factor_enhanced_tick_norm
from update_dol_factor_daily_l2p import main as update_factor_tick_l2p
from update_dol_label_daily_enhanced_tick import main as update_label_enhanced_tick_norm
from update_dol_factor_daily_labels_l2p import main as update_label_tick_l2p 
from xquant.factordata import FactorData
import json
import datetime

def check(stocks_list, data_type, start_date):
    fp = FactorProvider()
    if data_type == 'enhanced_tick_norm':
        norm_res = fp.research_data_check(stocks_list,data_type='enhanced_tick_norm',check_start_date=start_date)
        import json
        with open("norm_lack_info.json","w") as f:
            f.write(json.dumps(norm_res))
        return "norm_lack_info.json"
    else:
        l2p_res = fp.research_data_check(stocks_list,data_type='tick_l2p',check_start_date=start_date)
        import json
        with open("l2p_lack_info.json","w") as f:
            f.write(json.dumps(l2p_res))
        return "l2p_lack_info.json"


def update_market_data(stock, lack_date_list, data_type='enhanced_tick_norm'):
    if stock.endswith(".SZ"):
        if data_type in ['enhanced_tick',"enhanced_tick_norm"]: 
            for date in lack_date_list:
                update_sz_md_enhanced_tick(date, date, stock)
        else:
            update_all_md_tick_l2p(lack_date_list,[stock],4)            
    elif stock.endswith(".SH"):
        if data_type in ['enhanced_tick',"enhanced_tick_norm"]: 
            for date in lack_date_list:
                update_sh_md_enhanced_tick(date, date, stock)
        else:
            update_all_md_tick_l2p(lack_date_list, [stock],4)            
    return

def update_factor_data(stock,lack_date_list,data_type):
    if data_type == 'enhanced_tick_norm':
        for date in lack_date_list:
            try:
                update_factor_enhanced_tick_norm(date,date,[stock])
            except:
                continue
    else:
        for date in lack_date_list:
            try:
                update_factor_tick_l2p(date,date,[stock])
            except:
                continue 
    return

def update_label_data(stock,lack_date_list,data_type):
    if data_type == 'enhanced_tick_norm':
        for date in lack_date_list:
            try:
                update_label_enhanced_tick_norm(date,date,[stock])
            except:
                continue
    else:
        for date in lack_date_list:
            try:
                update_label_tick_l2p([stock],date,date)
            except:
                continue

    return



def main(check_stocks, check_start_date, data_type='tick_l2p'):
    fd = FactorData()
    lack_file = check(check_stocks,data_type,check_start_date)
    lack_info = json.loads(open(lack_file).read())
    check_end_date = fd.tradingday(datetime.datetime.now().strftime("%Y%m%d"),-2)[0]
    for stock, lack_info_perstock in lack_info.items():
        
        market_lack_date = [i for i in lack_info_perstock['md_info'] if i >= check_start_date and i<=check_end_date]
        print("[CHECK DATE] md: {} {}".format(stock,str(market_lack_date)))
        if len(market_lack_date)>0:
            update_market_data(stock, market_lack_date, data_type)
        
        factor_lack_date = [i for i in lack_info_perstock['factor_info'] if i >= check_start_date and i<=check_end_date]
        print("[CHECK DATE] factor: {} {}".format(stock,str(factor_lack_date)))

        if len(set(factor_lack_date)-set(market_lack_date))>0:
            update_factor_data(stock, factor_lack_date, data_type)
        
        label_lack_date = [i for i in lack_info_perstock['label_info'] if i >= check_start_date and i<=check_end_date]
        print("[CHECK DATE] label: {} {}".format(stock,str(label_lack_date)))
        if len(set(label_lack_date)-set(market_lack_date))>0:
            update_label_data(stock, label_lack_date, data_type)

    return

def get_stock_list(data_type='enhanced_tick_norm'):
    s = ddb.session()
    if data_type in ['enhanced_tick','enhanced_tick_norm']:
        s.connect("168.17.250.49",8902,'admin','123456')
        dbname = "dfs://CustomData/sh_stock_tick_enhanced"
        tbname = "sh_stock_tick_enhanced"

    else:
        s.connect("168.17.249.173", 8902, 'admin', '123456')
        dbname="dfs://CustomData/sh_stock_tick_l2p_persec"
        tbname = "sh_stock_tick_l2p_persec"

    sh_stocks = s.run(f"""
    dbname = '{dbname}'
    tbname = `{tbname}
    stocks = exec distinct(M_HTSCSecurityID) from loadTable(dbname, tbname)
    stocks
    """)
    sh_stocks = list(sh_stocks)
    
    if data_type in ['enhanced_tick','enhanced_tick_norm']:
        dbname = "dfs://CustomData/sz_stock_tick_enhanced"
        tbname = "sz_stock_tick_enhanced"
    else:
        dbname="dfs://CustomData/sz_stock_tick_l2p_persec"
        tbname = "sz_stock_tick_l2p_persec"
    
    sz_stocks = s.run(f"""
    dbname = '{dbname}'
    tbname = `{tbname}
    stocks = exec distinct(M_HTSCSecurityID) from loadTable(dbname, tbname)
    stocks
    """)
    sz_stocks = list(sz_stocks)
    stocks = sh_stocks+sz_stocks
    return stocks




if __name__ == "__main__":
    from xquant.factordata import FactorData
    fd = FactorData()
    cur_date = datetime.datetime.now().strftime("%Y%m%d")
    parse_date = fd.tradingday(cur_date,-2)[0]
    data_type = "tick_l2p"
    all_stock_list = get_stock_list(data_type)
    print(len(all_stock_list))
    for stock in all_stock_list:
        check_start_date = "20240220"
        main([stock], check_start_date, data_type=data_type)
