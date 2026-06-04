from numba import jit

@jit(nopython = True)
def trade_field_agg(trade_qtys, trade_moneys, trade_sides):
    active_buy_money = 0.0
    active_sell_money = 0.0
    active_buy_num = 0.0
    active_sell_num = 0.0
    active_buy_volume = 0.0
    active_sell_volume = 0.0

    if len(trade_moneys)==0:
        pass
    for i in range(len(trade_moneys)):
        if trade_sides[i]==1:
            active_buy_money+=trade_moneys[i]
            active_buy_num += 1
            active_buy_volume+=trade_qtys[i]
        elif trade_sides[i]==2:
            active_sell_money+=trade_moneys[i]
            active_sell_num += 1
            active_sell_volume+=trade_qtys[i]
    return (active_buy_money, active_sell_money,
                active_buy_num, active_sell_num,
                active_buy_volume, active_sell_volume
                )
