//
// Created by zhangtian on 2023/5/23.
//

#pragma once

#include <cstdint>
#include <cstring>
#include <stdlib.h>

namespace huatai {
namespace strategy {
namespace xdb {

typedef struct _tag_tick_
{
    char security_id[8];        // 6位证券代码
    double ask_price[10];       // 十档盘口-卖价
    int64_t ask_qty[10];        // 十档盘口-卖量
    int64_t ask_order_nums[10]; // 十档盘口-卖单数
    double bid_price[10];       // 十档盘口-买价
    int64_t bid_qty[10];        // 十档盘口-买量
    int64_t bid_order_nums[10]; // 十档盘口-买单数
    double open_px;             // 开盘价
    double last_px;             // 最近价
    double high_px;             // 最高价
    double low_px;              // 最低价
    int64_t ask_order_qty;      // 全卖单委托量，含十档盘口以外订单
    int64_t bid_order_qty;      // 全买单委托量，含十档盘口以外订单
    double ask_avg_px;          // 卖均价
    double bid_avg_px;          // 买均价
    int64_t appl_seq_num;       // L2P专用，当前盘口涉及的最后一个逐笔的逐笔编号
    int64_t md_time;            // 行情时间, HHMMSSsss
    int64_t receive_time;       // 接收时间，Timestamp格式，精确到纳秒(ns)
    int64_t total_volume;       // 总成交量，开盘到现在的总成交量
    double total_amount;        // 总成交金额，开盘到现在的总成交金额
    int64_t delta_qty;          // 相邻两个tick之间的成交量
    int64_t num_trades;         // 总成交笔数，开盘到现在的总成交笔数
    int64_t local_index;   // 证投行情编号，该标的该tick涉及的最后一个逐笔的自编行情编号
    char trading_phase_code; // 产品阶段标志，'0'=盘前，启动；'1'=集合竞价；'2'=集合竞价结束到连续竞价开始之前；'3'=连续竞价；'4'=中午休市；'5'=收盘集合竞价；'6'=已闭市；'7'=盘后交易；'8'=临停；'9'='波动性中断'
    char source;            // 行情源标记：'u'=UDP, 'f'=Fast, 's'=秒级tick,'o'=逐笔tick
    char reserved[6];
} Tick;

typedef struct _order_tag_
{
    char security_id[8];  // 6位证券代码
    int64_t appl_seq_num; // 交易所原始数据中的应用顺序编号。针对上交所，如果该委托无委托剩余量，交易所不推送该笔委托的数据，则该字段值为0
    int64_t order_no;     // 订单编号
    double order_price;   // 委托价格，市价单价格无意义
    int64_t order_qty;    // 委托数量
    int64_t md_time;      // 委托时间，HHMMSSsss
    int64_t receive_time; // 接收时间，Timestamp格式，精确到纳秒(ns)
    int64_t order_index;  // 委托序号, SH：channel内按order发送顺序递增，SZ：无意义，填充为0
    int64_t local_index;  // 自编行情编号，按行情播放顺序递增，包含合成原始委托
    char side;            // 买卖方向，'1'=买;'2'=卖
    char order_type;      // 订单类别，'1'=市价，'2'=限价，'U'=本方最优（上交所只有'2'）
    char reserved[6];
} OrderRecord;

typedef struct _kline1min_tag_
{
    char security_id[8]; // 证券代码
    uint64_t md_time;    // 委托时间，YYYYMMDDHHMMSSsss
    double open_px;
    double close_px;
    double high_px;
    double low_px;
    int64_t numTrade;
    double turnover;
    int64_t volume;
} KLine1Min;

typedef struct _tag_trade_
{
    char security_id[8];   // 6位证券代码
    int64_t appl_seq_num;  // 交易所原始数据中的应用顺序编号。
    int64_t trade_buy_no;  // 买单编号，可以与Order中order_no进行匹配
    int64_t trade_sell_no; // 卖单编号，可以与Order中order_no进行匹配
    double trade_price;    // 成交价格
    int64_t trade_qty;     // 成交数量
    int64_t transact_time; // 成交时间, HHMMSSsss
    int64_t receive_time;  // 接收时间, Timestamp格式，精确到纳秒(ns)
    int64_t trade_index;   // 成交序号，SH：各channel按trade发送顺序逐一递增，SZ：无意义，填充为0
    int64_t local_index;   // 自编行情编号，按行情播放顺序递增，包含合成原始委托
    char side;             // 成交方向，'1'=买，'2'=卖
    char reserved[7];
} Trade, FilledTrade;




typedef struct _tag_cancel_order_
{
    char security_id[8];  // 6位证券代码
    int64_t appl_seq_num; // 交易所原始数据中的应用顺序编号。
    int64_t order_no;     // SH为原始订单号，SZ为对应方向的trade_buy_no或trade_sell_no
    double order_price;   // 委托价格
    int64_t order_qty;    // 委托数量
    int64_t transact_time;// 委托时间，HHMMSSsss
    int64_t receive_time; // 接收时间，Timestamp格式，精确到纳秒(ns)
    int64_t order_index;  // 委托序号, SH：channel内按order发送顺序递增，SZ：无意义，填充为0
    int64_t local_index;  // 自编行情编号，按行情播放顺序递增，包含合成原始委托
    char order_side;            // 买卖方向，'1'=买;'2'=卖
    char reserved[7];
} CancelOrder, Cancel;



typedef struct _tag_raw_status_
{
    char security_id[8];  // 6位证券代码
    int64_t appl_seq_num; // 交易所原始数据中的应用顺序编号。
    int64_t md_time;      // 委托时间，HHMMSSsss
    int64_t receive_time; // 接收时间，Timestamp格式，精确到纳秒(ns)
    int64_t local_index;  // 自编行情编号，按行情播放顺序递增，包含合成原始委托
    uint8_t security_status;
    char reserved[7];
} Status;

typedef struct _tag_quote_
{
    char security_id[8];        // 证券代码
    double ask_price[10];       // 卖10 价格
    int64_t ask_qty[10];        // 卖10 数量
    int64_t ask_order_nums[10]; // 卖盘1-10档委托笔数
    double bid_price[10];       // 买10 价格
    int64_t bid_qty[10];        // 买10 数量
    int64_t bid_order_nums[10]; // 买盘1-10档委托笔数
    double pre_close_px;        // 前收价
    double open_px;             // 开盘价
    double last_px;             // 最近价
    double high_px;             // 最高价
    double low_px;              // 最低价
    int64_t ask_order_qty;      // 卖委托量
    int64_t bid_order_qty;      // 买委托量
    double ask_avg_px;          // 卖均价
    double bid_avg_px;          // 买均价
    int64_t appl_seq_num;       // L2P专用，切盘口时对应的逐笔编号(Sappe策略为当前tick涉及的order的appseqnum)
    int64_t md_time;            // 行情时间
    int64_t total_volume;       // 总成交量
    double total_amount;        // 总成交金额
    int64_t num_trades;
    char trading_phase_code;
    char source;
    int8_t security_type;
    char reserved[5];
} Quote;

typedef struct _tag_daily_
{
    char date[8];
    char security_id[8];
    double preClose;
    double openPrice;
    double highPrice;
    double lowPrice;
    double closePrice;
    double vwap;
    double chg;
    double pctChg;
    double turn;
    double freeTurn;
    double volume;
    double amount;
    long dealNum;
    double swing;
    double reIpoChg;
    double relIpoPctChg;
    double mdcMaxPx;
    double mdcMinPx;
    char lastTradeDay[8];
    double adjFactor;
    double maxUpOrDown;
    double totalShares;
    double freeFloatShares;
    double floatAShrToday;
    double floatAShares;
    double shareTotalA;
    double preCloseBAdj;
    double openBAdj;
    double closeBAdj;
    double highBAdj;
    double lowBAdj;
    double reIpoChgBAdj;
    double relIpoPctChgBAdj;
    bool tradeStatus;
} Daily;

enum MarketDataType
{
    Market_Data_Type_Order = 1,
    Market_Data_Type_Trade = 2,
    Market_Data_Type_Cancel = 3,
    Market_Data_Type_Status = 4,
    Market_Data_Type_Tick_Full = 11,
    Market_Data_Type_Tick_1s = 12,
    Market_Data_Type_Tick_Ex = 13,
    Market_Data_Type_KLine1Min = 14,
    Market_Data_Type_Union = 4,
    Market_Data_Type_Order_And_Trade_Union = 5,
    Market_Data_Type_Daily = 15,
    Market_Data_Type_Factor = 99
};

struct OrderAndTradeUnion
{
    int64_t data_type;
    union
    {
        Trade trade;
        OrderRecord order;
        CancelOrder cancel_order;
    };
};

struct MarketData
{
    int64_t data_type;
    union
    {
        Trade trade;
        CancelOrder cancel_order;
        OrderRecord order;
        Tick tick;
    };
    inline uint64_t GetMDTime() const
    {
        if (data_type == Market_Data_Type_Order)
        {
            return order.md_time;
        }
        else if (data_type == Market_Data_Type_Trade)
        {
            return trade.transact_time;
        }
        else if (data_type == Market_Data_Type_Tick_1s)
        {
            return tick.md_time;
        }
        else if (data_type == Market_Data_Type_Cancel)
        {
            return cancel_order.transact_time;
        }
        abort();
    }
    inline uint64_t GetApplSeqNum() const
    {
        if (data_type == Market_Data_Type_Order)
        {
            return order.appl_seq_num;
        }
        else if (data_type == Market_Data_Type_Trade)
        {
            return trade.appl_seq_num;
        }
        else if (data_type == Market_Data_Type_Tick_1s)
        {
            return tick.appl_seq_num;
        }
        else if (data_type == Market_Data_Type_Cancel)
        {
            return cancel_order.appl_seq_num;
        }
        abort();
    }
    inline const char *GetSymbol() const
    {
        if (data_type == Market_Data_Type_Order)
        {
            return order.security_id;
        }
        else if (data_type == Market_Data_Type_Trade)
        {
            return trade.security_id;
        }
        else if (data_type == Market_Data_Type_Tick_1s)
        {
            return tick.security_id;
        }
        else if (data_type == Market_Data_Type_Cancel)
        {
            return cancel_order.security_id;
        }
        abort();
    }
};

struct OrderSide
{
    const static char kUnknown = '0'; // 未知
    const static char kBuy = '1';     // 买入
    const static char kSell = '2';    // 卖出
};

struct OrderType
{
    const static char kLimit = '2';  // 限价单
    const static char kMarket = '1'; // 市价单
    const static char kOOP = 'U';    // 本方最优单

    const static char kAdd = 'A';    // 增加 （委托剩余）
    const static char kDel = 'D';    // 删除（撤单）
    const static char kStatus = 'S'; // 状态变更消息
};

struct TradeType
{
    const static char kFill = 'F';
    const static char kCancel = '4';
};

struct MarketType
{
    const static char kSZSE = '1'; // 深交所
    const static char kSSE = '2';  // 上交所
    const static char kAll = 'A';  // 沪深市场
};

struct SymbolType
{
    const static char STOCK = '1'; // 主板
    const static char BOND = '2';  // 转债
};

/**
 * 优先对比mdTime，mdTime相同，目前再按照 order, trade, tick 的顺序比较大小，还相同，则根据 symbol 字节序
 * @param a
 * @param b
 * @return <0 表示 a < b; 0 表示相同； >0 表示 a > b
 */
int inline compare(const MarketData *a, const MarketData *b)
{
    int cmpa = a->GetMDTime() * 10 + a->data_type;
    int cmpb = b->GetMDTime() * 10 + b->data_type;
    int ret = cmpa - cmpb;
    if (ret == 0)
    {
        return memcmp(a->GetSymbol(), b->GetSymbol(), sizeof(a->GetSymbol()));
    }
    return ret;
}

} // namespace xdb
} // namespace strategy
} // namespace huatai
