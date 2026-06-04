import xbrain as xb
from enum import Enum

class PriceMode(Enum):
    THIS_SIDE = 1 # 本方一档
    THIS_SIDE_DEVIATION = 0 # 本方最优加若干价差
    OTHER_SIDE = -1 # 对手方一档

def get_midprice(last_price_df):
    if not last_price_df.ask1price and not last_price_df.bid1price:
        curr_price = last_price_df.close
    elif not last_price_df.ask1price:
        curr_price = last_price_df.bid1price
    elif not last_price_df.bid1price:
        curr_price = last_price_df.bid1price
    else:
        curr_price = (last_price_df.ask1price + last_price_df.bid1price) / 2
    return curr_price


def calc_adjust_price(side, last_price_df, deviation, mode = PriceMode.THIS_SIDE_DEVIATION):
    #preference值越大，价格越保守，值越小，价格约激进
    if mode == PriceMode.OTHER_SIDE:
        #对手方最优
        if side == xb.Order.Buy:
            price = last_price_df.ask1price if last_price_df.ask1price else  round(last_price_df.bid1price*1.0002, 2)
        else:
            price = last_price_df.bid1price if last_price_df.bid1price else round(last_price_df.ask1price*0.9998, 2)
    elif mode == PriceMode.THIS_SIDE_DEVIATION:
        # 本方最优, 增加一个tick
        if side == xb.Order.Buy:
            # price = round(last_price_df.bid1price*1.0002, 2)
            price = min(last_price_df.bid1price+deviation, last_price_df.ask1price)
        else:
            # price = round(last_price_df.ask1price * 0.9998, 2)
            price = max(last_price_df.ask1price-deviation, last_price_df.bid1price)
            # price = last_price_df.bid1price - 0.01
    elif mode == PriceMode.THIS_SIDE:
        #本方最优
        if side == xb.Order.Buy:
            price = last_price_df.bid1price if last_price_df.bid1price else round(last_price_df.ask1price*0.9998, 2)
        else:
            price = last_price_df.ask1price if last_price_df.ask1price else round(last_price_df.bid1price*1.0002, 2)
    return price


def calc_adjust_price_wining(side, last_price_df, wining_price):
    # 根据止盈线靠档挂单
    if side == xb.Order.Buy:
        price_list = [last_price_df.bid1price, last_price_df.bid2price, last_price_df.bid3price,
                      last_price_df.bid4price, last_price_df.bid5price, last_price_df.bid6price,
                      last_price_df.bid7price, last_price_df.bid8price, last_price_df.bid9price, last_price_df.bid10price
                      ]
        price = wining_price
        for p in price_list:
            if wining_price <= p:
                # 挂靠最近一档价格
                price = p
            else:
                price = p
                break
    elif side == xb.Order.Sell:
        price_list = [last_price_df.ask1price, last_price_df.ask2price, last_price_df.ask3price,
                      last_price_df.ask4price, last_price_df.ask5price, last_price_df.ask6price,
                      last_price_df.ask7price, last_price_df.ask8price, last_price_df.ask9price,
                      last_price_df.ask10price]
        price = wining_price
        for p in price_list:
            if wining_price >= p:
                # 挂靠最近一档价格
                price = p
            else:
                price = p
                break
    else:
        raise Exception()
    return price


def get_up_down_limit(stock):
    # 获取涨跌停
    return 0.195 if stock.startswith('3') or stock.startswith('68') else 0.095

