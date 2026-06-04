//
// Created by zhangtian on 2023/5/23.
//

#include "xdb/include/xdb.h"
#include <map>
#include <string>
#include <chrono>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>

bool compare_tick(huatai::strategy::xdb::Tick &my_tick, huatai::strategy::xdb::Tick &dfs_tick)
{
    for (int i = 0; i < 10; ++i)
    {
        if (my_tick.ask_price[i] != dfs_tick.ask_price[i])
        {
            printf("askprice not equal\n");
            return false;
        }

        if (my_tick.ask_qty[i] != dfs_tick.ask_qty[i])
        {
            printf("askqty not equal\n");
            return false;
        }

        if (my_tick.ask_order_nums[i] != dfs_tick.ask_order_nums[i])
        {
            printf("ask_order_nums not equal\n");
            return false;
        }

        if (my_tick.bid_price[i] != dfs_tick.bid_price[i])
        {
            printf("bidprice not equal\n");
            return false;
        }

        if (my_tick.bid_qty[i] != dfs_tick.bid_qty[i])
        {
            printf("bid_qty not equal\n");
            return false;
        }

        if (my_tick.bid_order_nums[i] != dfs_tick.bid_order_nums[i])
        {
            printf("bid_order_nums not equal\n");
            return false;
        }                
    }

    if (my_tick.open_px != dfs_tick.open_px)
    {
        printf("open_px not equal\n");
        return false;
    }

    if (my_tick.last_px != dfs_tick.last_px)
    {
        printf("last_px not equal\n");
    }

    if (my_tick.high_px != dfs_tick.high_px)
    {
        printf("high_px not equal\n");
        return false;
    }

    if (my_tick.low_px != dfs_tick.low_px)
    {
        printf("low_px not equal\n");
        return false;
    }

    if (my_tick.ask_order_qty != dfs_tick.ask_order_qty)
    {
        printf("ask_order_qty not equal\n");
        return false;
    }

    if (my_tick.bid_order_qty != dfs_tick.bid_order_qty)
    {
        printf("bid_order_qty not equal\n");
        return false;
    }

    if (my_tick.bid_order_qty != dfs_tick.bid_order_qty)
    {
        printf("bid_order_qty not equal\n");
        return false;
    }

    if (my_tick.ask_avg_px != dfs_tick.ask_avg_px)
    {
        printf("ask_avg_px not equal\n");
        return false;
    }

    if (my_tick.bid_avg_px != dfs_tick.bid_avg_px)
    {
        printf("bid_avg_px not equal\n");
        return false;
    }

    if (my_tick.md_time != dfs_tick.md_time)
    {
        printf("md_time not equal\n");
        return false;
    }

    if (my_tick.total_volume != dfs_tick.total_volume)
    {
        printf("total_volume not equal\n");
        return false;
    }

    if (my_tick.total_volume != dfs_tick.total_volume)
    {
        printf("total_volume not equal\n");
        return false;
    }

    if (my_tick.total_amount != dfs_tick.total_amount)
    {
        printf("total_amount not equal\n");
        return false;
    }

    if (my_tick.delta_qty != dfs_tick.delta_qty)
    {
        printf("delta_qty not equal\n");
        return false;
    }

    if (my_tick.num_trades != dfs_tick.num_trades)
    {
        printf("num_trades not equal\n");
        return false;
    }

    if (my_tick.trading_phase_code != dfs_tick.trading_phase_code)
    {
        printf("trading_phase_code not equal\n");
        return false;
    }

    return true;
}

bool compare_cancel(huatai::strategy::xdb::CancelOrder &my_cancel, huatai::strategy::xdb::CancelOrder &dfs_cancel)
{
    if (my_cancel.order_no != dfs_cancel.order_no)
    {
        printf("order no not equal");
        return false;
    }

    if (my_cancel.order_price != dfs_cancel.order_price)
    {
        printf("******************order price not equal***************");
        return false;
    }

    if (my_cancel.order_qty != dfs_cancel.order_qty)
    {
        printf("order_qty not equal");
        return false;
    }

    if (my_cancel.order_side != dfs_cancel.order_side)
    {
        printf("order_side not equal");
        return false;
    }

    if (my_cancel.transact_time != dfs_cancel.transact_time)
    {
        printf("transact_time not equal");
        return false;
    }

    return true;
}

bool compare_trade(huatai::strategy::xdb::Trade &my_trade, huatai::strategy::xdb::Trade &dfs_trade)
{
    if (my_trade.side != dfs_trade.side)
    {
        printf("trade side not equal\n");
        return false;
    }

    if (my_trade.trade_buy_no != dfs_trade.trade_buy_no)
    {
        printf("trade trade_buy_no not equal\n");
        return false;
    }

    if (my_trade.trade_price != dfs_trade.trade_price)
    {
        printf("trade trade_price not equal\n");
        return false;
    }

    if (my_trade.trade_qty != dfs_trade.trade_qty)
    {
        printf("trade trade_qty not equal\n");
        return false;
    }

    if (my_trade.trade_sell_no != dfs_trade.trade_sell_no)
    {
        printf("trade trade_sell_no not equal\n");
        return false;
    }

    if (my_trade.transact_time != dfs_trade.transact_time)
    {
        printf("trade transact_time not equal\n");
        return false;
    }

    return true;
}

bool compare_order(huatai::strategy::xdb::OrderRecord &my_order, huatai::strategy::xdb::OrderRecord &dfs_order)
{
    if (my_order.md_time != dfs_order.md_time)
    {
        printf("order md time not equal\n");
        return false;
    }

    if (my_order.order_no != dfs_order.order_no)
    {
        printf("order order_no not equal\n");
        return false;
    }

    if (my_order.order_price != dfs_order.order_price)
    {
        printf("order order_price not equal\n");
        return false;
    }

    if (my_order.order_qty != dfs_order.order_qty)
    {
        printf("order order_qty not equal\n");
        return false;
    }

    if (my_order.order_type != dfs_order.order_type)
    {
        printf("order order_type not equal\n");
        return false;
    }

    if (memcmp(my_order.security_id, dfs_order.security_id, 6) != 0)
    {
        printf("order security_id not equal\n");
        return false;
    }

    if (my_order.side != dfs_order.side)
    {
        printf("order side not equal\n");
        return false;
    }

    return true;
}

inline int64_t GetTimeSinceEpoch()
{
    timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    
    return ts.tv_nsec + ts.tv_sec  * 1000'000'000;
}

void write_file(const std::string& symbol, const std::string& date, huatai::strategy::xdb::DataPack<huatai::strategy::xdb::OrderRecord>& orders, huatai::strategy::xdb::DataPack<huatai::strategy::xdb::Trade>& trades,
    huatai::strategy::xdb::DataPack<huatai::strategy::xdb::Cancel>& cancels, huatai::strategy::xdb::DataPack<huatai::strategy::xdb::Tick>& tick1s, huatai::strategy::xdb::DataPack<huatai::strategy::xdb::Tick> &tickfull)
{
    std::string prefix = date + "_" + symbol + "_";

    std::string order_file = prefix + "order.csv";
    int fd = open(order_file.c_str(), O_CREAT|O_TRUNC|O_WRONLY, S_IRGRP|S_IROTH|S_IWUSR|S_IRUSR);
    char buff[1024]  = {"symbol,appl_seq_num,order_no,order_price,order_qty,md_time,local_index,side,order_type\n"};

    write(fd, buff, strlen(buff));
    for (int i = 0; i < orders.size; ++i)
    {
        auto& order = orders.data[i];
        memset(buff, 0, 1024);
        snprintf(buff, 1024, "%s,%ld,%ld,%f,%ld,%ld,%ld,%c,%c\n",symbol.c_str(), order.appl_seq_num, order.order_no, order.order_price, order.order_qty, order.md_time, order.local_index, order.side, order.order_type);
        write(fd, buff, strlen(buff));
    }
    close(fd);

    std::string trade_file = prefix + "trade.csv";
    fd = open(trade_file.c_str(), O_CREAT|O_TRUNC|O_WRONLY, S_IRGRP|S_IROTH|S_IWUSR|S_IRUSR);
    memset(buff, 0, 1024);
    memcpy(buff, "symbol,appl_seq_num,trade_buy_no,trade_sell_no,trade_price,trade_qty,md_time,local_index,side\n", 95);
    write(fd, buff, strlen(buff));
    for (int i = 0; i < trades.size; ++i)
    {
        auto& trade = trades.data[i];
        memset(buff, 0, 1024);
        snprintf(buff, 1024, "%s,%ld,%ld,%ld,%f,%ld,%ld,%ld,%c\n",symbol.c_str(), trade.appl_seq_num, trade.trade_buy_no, trade.trade_sell_no, trade.trade_price,
            trade.trade_qty, trade.transact_time, trade.local_index, trade.side);
        write(fd, buff, strlen(buff));
    }
    close(fd);

    std::string cancel_file = prefix + "cancel.csv";
    fd = open(cancel_file.c_str(), O_CREAT|O_TRUNC|O_WRONLY, S_IRGRP|S_IROTH|S_IWUSR|S_IRUSR);
    memset(buff, 0, 1024);
    memcpy(buff, "symbol,appl_seq_num,order_no,order_qty,md_time,local_index,side\n", 65);
    write(fd, buff, strlen(buff));
    for (int i = 0; i < cancels.size; ++i)
    {
        auto& cancel = cancels.data[i];
        memset(buff, 0, 1024);
        snprintf(buff, 1024, "%s,%ld,%ld,%ld,%ld,%ld,%c\n",symbol.c_str(), cancel.appl_seq_num, cancel.order_no, cancel.order_qty, cancel.transact_time, cancel.local_index, cancel.order_side);
        write(fd, buff, strlen(buff));
    }
    close(fd);
}

int main(int argc, char *argv[])
{
    std::string date = "20240529";
    huatai::strategy::xdb::Xdb xdb("/data/group/800445/test_sh");
    huatai::strategy::xdb::Xdb xdb_dfs("/dfs/group/900001/XDB");
    huatai::strategy::xdb::DataPack<huatai::strategy::xdb::CancelOrder> cancelOrder_dfs = xdb_dfs.loadCancel("000001.SZ", date);
    for (int i = 0 ; i < cancelOrder_dfs.size; ++i)
    {
        printf("appl=%ld, price=%.4f\n",  cancelOrder_dfs.data[i].appl_seq_num, cancelOrder_dfs.data[i].order_price);
        if (cancelOrder_dfs.data[i].order_price <= 1e-8 && cancelOrder_dfs.data[i].order_price >= -1e-8)
        {
            printf("*********************\n");
        }
    }

    /*auto symbol_set = xdb.get_all_symbol_by_type("SH", date, huatai::strategy::xdb::Market_Data_Type_Order);

    auto channel_map = xdb.get_all_symbol_by_channel("SH", date, huatai::strategy::xdb::Market_Data_Type_Order);

    for (auto &symbol : symbol_set)
    {
        if (not symbol.starts_with("6"))
        {
            continue;
        }
        std::string full_symbol = symbol;
        full_symbol.append(".SH");
        huatai::strategy::xdb::DataPack<huatai::strategy::xdb::OrderRecord> orders = xdb.loadOrder(full_symbol, date);
        huatai::strategy::xdb::DataPack<huatai::strategy::xdb::Trade> trade = xdb.loadTrade(full_symbol, date);
        huatai::strategy::xdb::DataPack<huatai::strategy::xdb::CancelOrder> cancelOrder = xdb.loadCancel(full_symbol, date);
        huatai::strategy::xdb::DataPack<huatai::strategy::xdb::Tick> fullTick = xdb.loadTickFull(full_symbol, date);
        huatai::strategy::xdb::DataPack<huatai::strategy::xdb::Tick> tick1s = xdb.loadTick1s(full_symbol, date);

        huatai::strategy::xdb::DataPack<huatai::strategy::xdb::OrderRecord> orders_dfs = xdb_dfs.loadOrder(full_symbol, date);
        huatai::strategy::xdb::DataPack<huatai::strategy::xdb::Trade> trade_dfs = xdb_dfs.loadTrade(full_symbol, date);
        huatai::strategy::xdb::DataPack<huatai::strategy::xdb::CancelOrder> cancelOrder_dfs = xdb_dfs.loadCancel(full_symbol, date);
        huatai::strategy::xdb::DataPack<huatai::strategy::xdb::Tick> fullTick_dfs = xdb_dfs.loadTickFull(full_symbol, date);
        huatai::strategy::xdb::DataPack<huatai::strategy::xdb::Tick> tick1s_dfs = xdb_dfs.loadTick1s(full_symbol, date);

        printf("begin to compare symbol=%s\n", symbol.c_str());
        if (orders.size != orders_dfs.size)
        {
            printf("order size not equal\n");
        }
        else
        {
            for (int i = 0; i < orders.size; ++i)
            {
                auto my_order = orders.data[i];
                auto dfs_order = orders_dfs.data[i];
                if (!compare_order(my_order, dfs_order))
                {
                    printf("order not equal, symbol=%s\n", symbol.c_str());
                    break;
                }
            }
        }

        if (trade.size != trade_dfs.size)
        {
            printf("trade size not equal\n");
        }
        else
        {
            for (int i = 0; i < trade.size; ++i)
            {
                auto my_trade = trade.data[i];
                auto dfs_trade = trade_dfs.data[i];

                if (!compare_trade(my_trade, dfs_trade))
                {
                    printf("trade not equal, symbol=%s\n", symbol.c_str());
                    break;
                }
            }
        }

        if (cancelOrder.size != cancelOrder_dfs.size)
        {
            printf("cancel size not equal\n");
        }
        else
        {
            for (int i = 0; i < cancelOrder.size; ++i)
            {
                auto my_cancel = cancelOrder.data[i];
                auto dfs_cancel = cancelOrder_dfs.data[i];

                if (!compare_cancel(my_cancel, dfs_cancel))
                {
                    printf("cancel not equal,symbol=%s\n", symbol.c_str());
                    break;
                }
            }
        }

        if (fullTick.size != fullTick_dfs.size)
        {
            printf("full tick not equal\n");
        }
        else
        {
            for (int i = 0; i < fullTick.size; ++i)
            {
                if (!compare_tick(fullTick.data[i], fullTick_dfs.data[i]))
                {
                    printf("full tick not equal,symbol=%s\n", symbol.c_str());
                    break;
                }
            }
        }

        if (tick1s_dfs.size != tick1s.size)
        {
            printf("tick1s size not equal\n");
        }
        else
        {
            for (int i = 0; i < tick1s.size; ++i)
            {
                if (!compare_tick(tick1s.data[i], tick1s_dfs.data[i]))
                {
                    printf("tick1s not equal, symbol=%s\n", symbol.c_str());
                    break;
                }
            }
        }
    }*/

    printf("finished\n");
    return 0;
}
