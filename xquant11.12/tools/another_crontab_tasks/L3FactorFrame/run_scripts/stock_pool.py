from xquant.factordata import FactorData
from datetime import datetime
import pandas as pd
import os
import json

def get_stock_pool(symbol_flag_list):
    base_dir = "/dfs/group/800657/exp_results/KG101_model/"
    fa = FactorData()
    date = datetime.now().strftime("%Y%m%d")
    date = fa.tradingday(date, -2)[0]
    print(date)
    symbol_flag_list = [symbol_flag_list] if type(symbol_flag_list)==str else symbol_flag_list
    symbol_flag_list = [i.upper() for i in symbol_flag_list]
    if "ALL".upper() in symbol_flag_list:
        symbol_flag_list.extend(["HS300", "ZZ500", "ZZ1000", "A500", "STAR", "GEM"])
        symbol_flag_list.remove("ALL")
    ####################################################################
    # 如HS_TICK2， HS_TICK2_add等
    online_models = os.listdir(base_dir)
    online_models_upper = [model.upper() for model in online_models]
    ####################################################################
    symbol_flag_list = set(symbol_flag_list)
    symbol_list_all = []
    for symbol_flag in symbol_flag_list:
        if symbol_flag.upper() == "HS300":
            stock_list2 = fa.hset("INDEX", date, "HS300")["stock"].tolist()
            symbols = sorted(stock_list2)
        elif symbol_flag.upper() == "ZZ500":
            stock_list2 = fa.hset("INDEX", date, "ZZ500")["stock"].tolist()
            symbols = sorted(stock_list2)
        elif symbol_flag.upper() == "ZZ1000":
            stock_list2 = fa.hset("INDEX", date, "ZZ1000")["stock"].tolist()
            symbols = sorted(stock_list2)
        elif symbol_flag.upper() == "A500":
            symbols = sorted(['600000.SH', '600004.SH', '600007.SH', '600008.SH', '600009.SH', '600010.SH', '600011.SH', '600018.SH', '600019.SH', '600026.SH', '600027.SH', '600028.SH', '600029.SH', '600030.SH', '600031.SH', '600036.SH', '600038.SH', '600039.SH', '600048.SH', '600050.SH', '600066.SH', '600085.SH', '600089.SH', '600096.SH', '600104.SH', '600111.SH', '600115.SH', '600118.SH', '600129.SH', '600131.SH', '600141.SH', '600143.SH', '600150.SH', '600153.SH', '600157.SH', '600160.SH', '600161.SH', '600166.SH', '600167.SH', '600170.SH', '600176.SH', '600177.SH', '600183.SH', '600188.SH', '600196.SH', '600219.SH', '600233.SH', '600256.SH', '600258.SH', '600276.SH', '600309.SH', '600316.SH', '600323.SH', '600325.SH', '600332.SH', '600346.SH', '600352.SH', '600362.SH', '600372.SH', '600392.SH', '600398.SH', '600399.SH', '600406.SH', '600415.SH', '600418.SH', '600426.SH', '600436.SH', '600438.SH', '600460.SH', '600482.SH', '600486.SH', '600489.SH', '600497.SH', '600498.SH', '600499.SH', '600515.SH', '600516.SH', '600519.SH', '600521.SH', '600529.SH', '600535.SH', '600547.SH', '600549.SH', '600563.SH', '600570.SH', '600584.SH', '600585.SH', '600588.SH', '600637.SH', '600655.SH', '600660.SH', '600667.SH', '600674.SH', '600690.SH', '600699.SH', '600704.SH', '600741.SH', '600745.SH', '600754.SH', '600755.SH', '600760.SH', '600763.SH', '600765.SH', '600771.SH', '600795.SH', '600803.SH', '600816.SH', '600820.SH', '600839.SH', '600845.SH', '600859.SH', '600862.SH', '600867.SH', '600879.SH', '600884.SH', '600885.SH', '600886.SH', '600887.SH', '600893.SH', '600895.SH', '600900.SH', '600905.SH', '600919.SH', '600938.SH', '600941.SH', '600959.SH', '600988.SH', '600989.SH', '600998.SH', '601006.SH', '601012.SH', '601021.SH', '601058.SH', '601088.SH', '601100.SH', '601111.SH', '601117.SH', '601155.SH', '601166.SH', '601168.SH', '601186.SH', '601216.SH', '601225.SH', '601233.SH', '601238.SH', '601288.SH', '601318.SH', '601319.SH', '601328.SH', '601360.SH', '601390.SH', '601398.SH', '601600.SH', '601601.SH', '601607.SH', '601615.SH', '601618.SH', '601628.SH', '601633.SH', '601636.SH', '601658.SH', '601668.SH', '601669.SH', '601677.SH', '601689.SH', '601727.SH', '601728.SH', '601766.SH', '601799.SH', '601800.SH', '601816.SH', '601857.SH', '601866.SH', '601868.SH', '601872.SH', '601877.SH', '601880.SH', '601888.SH', '601899.SH', '601919.SH', '601966.SH', '601985.SH', '601988.SH', '601989.SH', '603000.SH', '603019.SH', '603077.SH', '603129.SH', '603156.SH', '603236.SH', '603259.SH', '603260.SH', '603288.SH', '603290.SH', '603392.SH', '603444.SH', '603456.SH', '603486.SH', '603501.SH', '603568.SH', '603588.SH', '603596.SH', '603605.SH', '603606.SH', '603613.SH', '603650.SH', '603659.SH', '603688.SH', '603737.SH', '603799.SH', '603806.SH', '603816.SH', '603833.SH', '603882.SH', '603885.SH', '603899.SH', '603939.SH', '603986.SH', '603993.SH', '605117.SH', '605358.SH', '688002.SH', '688005.SH', '688008.SH', '688009.SH', '688012.SH', '688036.SH', '688041.SH', '688063.SH', '688072.SH', '688099.SH', '688111.SH', '688122.SH', '688126.SH', '688169.SH', '688188.SH', '688223.SH', '688271.SH', '688303.SH', '688390.SH', '688396.SH', '688536.SH', '688598.SH', '688599.SH', '688617.SH', '688777.SH', '688981.SH', '000001.SZ', '000002.SZ', '000009.SZ', '000034.SZ', '000035.SZ', '000039.SZ', '000063.SZ', '000066.SZ', '000069.SZ', '000100.SZ', '000157.SZ', '000301.SZ', '000333.SZ', '000338.SZ', '000400.SZ', '000408.SZ', '000423.SZ', '000425.SZ', '000519.SZ', '000538.SZ', '000547.SZ', '000568.SZ', '000591.SZ', '000617.SZ', '000623.SZ', '000625.SZ', '000629.SZ', '000630.SZ', '000651.SZ', '000661.SZ', '000683.SZ', '000690.SZ', '000708.SZ', '000725.SZ', '000733.SZ', '000738.SZ', '000768.SZ', '000786.SZ', '000792.SZ', '000807.SZ', '000818.SZ', '000830.SZ', '000831.SZ', '000858.SZ', '000878.SZ', '000887.SZ', '000932.SZ', '000933.SZ', '000938.SZ', '000960.SZ', '000963.SZ', '000967.SZ', '000975.SZ', '000977.SZ', '000988.SZ', '000998.SZ', '000999.SZ', '001914.SZ', '001979.SZ', '002001.SZ', '002007.SZ', '002008.SZ', '002025.SZ', '002027.SZ', '002028.SZ', '002044.SZ', '002049.SZ', '002050.SZ', '002064.SZ', '002065.SZ', '002074.SZ', '002078.SZ', '002080.SZ', '002081.SZ', '002085.SZ', '002091.SZ', '002120.SZ', '002123.SZ', '002129.SZ', '002131.SZ', '002138.SZ', '002145.SZ', '002151.SZ', '002152.SZ', '002156.SZ', '002176.SZ', '002179.SZ', '002180.SZ', '002185.SZ', '002192.SZ', '002195.SZ', '002202.SZ', '002212.SZ', '002223.SZ', '002230.SZ', '002236.SZ', '002240.SZ', '002241.SZ', '002245.SZ', '002252.SZ', '002266.SZ', '002268.SZ', '002271.SZ', '002273.SZ', '002281.SZ', '002292.SZ', '002294.SZ', '002304.SZ', '002312.SZ', '002340.SZ', '002352.SZ', '002353.SZ', '002368.SZ', '002371.SZ', '002372.SZ', '002384.SZ', '002389.SZ', '002396.SZ', '002405.SZ', '002407.SZ', '002409.SZ', '002410.SZ', '002414.SZ', '002415.SZ', '002422.SZ', '002432.SZ', '002436.SZ', '002439.SZ', '002444.SZ', '002456.SZ', '002459.SZ', '002460.SZ', '002463.SZ', '002465.SZ', '002466.SZ', '002472.SZ', '002475.SZ', '002493.SZ', '002497.SZ', '002508.SZ', '002511.SZ', '002517.SZ', '002532.SZ', '002541.SZ', '002544.SZ', '002555.SZ', '002558.SZ', '002572.SZ', '002594.SZ', '002601.SZ', '002602.SZ', '002603.SZ', '002607.SZ', '002624.SZ', '002625.SZ', '002648.SZ', '002709.SZ', '002714.SZ', '002738.SZ', '002739.SZ', '002756.SZ', '002791.SZ', '002812.SZ', '002821.SZ', '002831.SZ', '002841.SZ', '002916.SZ', '002920.SZ', '002938.SZ', '003816.SZ', '300001.SZ', '300002.SZ', '300003.SZ', '300012.SZ', '300014.SZ', '300015.SZ', '300017.SZ', '300024.SZ', '300033.SZ', '300037.SZ', '300054.SZ', '300058.SZ', '300059.SZ', '300068.SZ', '300070.SZ', '300073.SZ', '300088.SZ', '300118.SZ', '300122.SZ', '300124.SZ', '300133.SZ', '300136.SZ', '300142.SZ', '300144.SZ', '300182.SZ', '300207.SZ', '300212.SZ', '300223.SZ', '300251.SZ', '300253.SZ', '300274.SZ', '300285.SZ', '300296.SZ', '300308.SZ', '300315.SZ', '300316.SZ', '300339.SZ', '300346.SZ', '300347.SZ', '300383.SZ', '300390.SZ', '300394.SZ', '300395.SZ', '300408.SZ', '300413.SZ', '300418.SZ', '300433.SZ', '300438.SZ', '300450.SZ', '300454.SZ', '300457.SZ', '300459.SZ', '300474.SZ', '300496.SZ', '300502.SZ', '300529.SZ', '300558.SZ', '300567.SZ', '300568.SZ', '300573.SZ', '300595.SZ', '300601.SZ', '300604.SZ', '300627.SZ', '300628.SZ', '300661.SZ', '300676.SZ', '300699.SZ', '300724.SZ', '300750.SZ', '300751.SZ', '300759.SZ', '300760.SZ', '300763.SZ', '300769.SZ', '300782.SZ', '300832.SZ', '300866.SZ', '300896.SZ', '300919.SZ', '300999.SZ', '301236.SZ', '301558.SZ', '002996.SZ', '600969.SH', '600479.SH', '003003.SZ', '603080.SH', '600779.SH', '600548.SH', '601339.SH', '601127.SH', '600455.SH', '603886.SH', '600099.SH', '605189.SH', '600487.SH', '601136.SH','601298.SH', '000031.SZ', '001338.SZ', '002782.SZ', '002961.SZ', '603105.SH', '600496.SH', '603666.SH', '600985.SH', '603187.SH', '002549.SZ', '600732.SH', '001872.SZ', '600797.SH', '603718.SH', '600811.SH', '603071.SH', '603896.SH', '600610.SH', '600391.SH', '600400.SH', '600022.SH', '000016.SZ', '603938.SH', '002135.SZ', '603113.SH', '601011.SH', '603906.SH', '601077.SH', '002283.SZ', '603212.SH', '002865.SZ', '600691.SH', '002746.SZ', '002453.SZ', '603517.SH', '002646.SZ', '002467.SZ', '601828.SH', '603595.SH', '600340.SH', '002287.SZ', '002250.SZ', '603936.SH', '603170.SH', '600225.SH', '600481.SH', '603127.SH', '600491.SH', '603098.SH', '601825.SH', '603519.SH', '601018.SH'])
        elif symbol_flag.upper() == "GEM":
            stock_list2 = fa.hset("MARKET", date, "GEM")["stock"].tolist()
            symbols = sorted(stock_list2)
        elif symbol_flag.upper() == "STAR":
            stock_list6 = [i for i in fa.hset("MARKET", date, "ALLA")["stock"].tolist() if i.startswith("688")]
            symbols = sorted(stock_list6)
        elif symbol_flag.upper() in online_models_upper:
            model_name = online_models[online_models_upper.index(symbol_flag.upper())]
            symbol_list = list(json.load(
                open(os.path.join(base_dir, model_name, "saved_models/threshold.json"), "r")).keys())
            symbols = sorted(symbol_list)
        # elif symbol_flag.upper() == "HS_TICK2_EXCEPT_20240927110913_1":
        #     SYMBOL_LIST = list(json.load(
        #         open("/dfs/group/800657/exp_results/KG101_model/HS_tick2_new/saved_models/threshold.json", "r")).keys())
        #     symbols = sorted(SYMBOL_LIST)
        #     target_stock_list = pd.read_excel(os.path.join(base_dir, "20240927110913_1.xlsx"))["证券代码"].tolist()
        #     target_stock_list = [str(i).zfill(6) for i in target_stock_list]
        #     symbols_except = [i + ".SH" if i.startswith("6") else i + ".SZ" for i in target_stock_list]
        #     symbols_except = sorted(symbols_except)
        #     symbols = [i for i in symbols if i not in symbols_except]
        # elif symbol_flag.upper() == "20240927110913_1":
        #     target_stock_list = pd.read_excel(os.path.join(base_dir, "20240927110913_1.xlsx"))["证券代码"].tolist()
        #     target_stock_list = [str(i).zfill(6) for i in target_stock_list]
        #     symbols = [i + ".SH" if i.startswith("6") else i + ".SZ" for i in target_stock_list]
        #     symbols = sorted(symbols)
        else:
            raise  Exception(f"symbol_flag {symbol_flag} not valid!!")
        symbol_list_all.extend(symbols)
    symbols = list(sorted(set(symbol_list_all)))
    return symbols

if __name__ == "__main__":
    stocks = get_stock_pool(["ALL"])
    pd.DataFrame(stocks).to_csv('all.csv')
    print(len(stocks))
