/**
 * @file market_data_def.h
 * @brief 行情数据类型定义
 * @author 刘从文
 * @date 2023-02-11
 *
 * @copyright Copyright (c) 2023
 *
 * @par 修改日志:
 * <table>
 * <tr> <th>日期</th>       <th>作者</th> <th>修改说明</th> </tr>
 * <tr> <td>2023-02-11</td> <td>刘从文</td> <td>初始创建</td> </tr>
 * </table>
 */
#pragma once

#include "common_type_def.h"

namespace huatai::atsquant::common {
// 数量+价格+笔数
struct QtyPrice {
  double quantity = 0;
  double price = 0;
  double num = 0;
};

// 行情-快照
struct Quote {
  QuoteType type;                      // 行情类型
  char symbol[32];                     // 证券代码
  TradingPhaseCode trading_phase_code; // 产品阶段标志
  int64_t timestamp;                   // 交易所时间(单位:ms)
  double last_px;                      // 最新价
  double open_px;                      // 开盘价
  double high_px;                      // 最高价
  double low_px;                       // 最低价
  double total_volume;                 // 总成交数量
  double turnover;                     // 总成交金额
  double high_limited_px;              // 涨停价 指数无效
  double low_limited_px;               // 跌停价 指数无效
  double previous_closing_px;          // 昨收盘价 指数无效
  int64_t recv_time;                   // 接收时间(单位:ns)
  MdSource source;                     // 行情源
};

// 指数行情快照
struct MDCIndex : public Quote {
  /* data */
};

// 股票行情快照
struct MDCStock : public Quote {
  QtyPrice bids[10];        // 买入价格档位
  QtyPrice asks[10];        // 卖出价格档位
  int64_t trades;           // 成交笔数
  double bid_vol;           // 买入总量（市场委托单中买单的总量）
  double ask_vol;           // 卖出总量（市场委托单中卖单的总量）
  double bid;               // 买入加权平均价
  double ask;               // 卖出加权平均价
  int bid1_order[50] = {0}; // 买一委托数量列表
  int ask1_order[50] = {0}; // 卖一委托数量列表
};

// 基金行情快照
struct MDCFund : public Quote {
  QtyPrice bids[10];        // 买入价格档位
  QtyPrice asks[10];        // 卖出价格档位
  int64_t trades;           // 成交笔数
  double bid_vol;           // 买入总量（市场委托单中买单的总量）
  double ask_vol;           // 卖出总量（市场委托单中卖单的总量）
  double bid;               // 买入加权平均价
  double ask;               // 卖出加权平均价
  int bid1_order[50] = {0}; // 买一委托数量列表
  int ask1_order[50] = {0}; // 卖一委托数量列表
  double iopv;              // IOPV净值估值
};

// 债券行情快照
struct MDCBond : public Quote {
  QtyPrice bids[10];        // 买入价格档位
  QtyPrice asks[10];        // 卖出价格档位
  int64_t trades;           // 成交笔数
  double bid_vol;           // 买入总量（市场委托单中买单的总量）
  double ask_vol;           // 卖出总量（市场委托单中卖单的总量）
  double bid;               // 买入加权平均价
  double ask;               // 卖出加权平均价
  int bid1_order[50] = {0}; // 买一委托数量列表
  int ask1_order[50] = {0}; // 卖一委托数量列表
};

// 期货行情快照
struct MDCFuture : public Quote {
  QtyPrice bids[5];              // 买入价格档位
  QtyPrice asks[5];              // 卖出价格档位
  double previous_open_interest; // 昨持仓
  double previous_settlement_px; // 昨结算价
  double open_interest;          // 持仓总量
  double settlement_px;          // 今结算价
};

// 期权行情快照
struct MDCOption : public Quote {
  QtyPrice bids[10];             // 买入价格档位
  QtyPrice asks[10];             // 卖出价格档位
  int64_t trades;                // 成交笔数
  double bid_vol;                // 买入总量（市场委托单中买单的总量）
  double ask_vol;                // 卖出总量（市场委托单中卖单的总量）
  double bid;                    // 买入加权平均价
  double ask;                    // 卖出加权平均价
  double previous_open_interest; // 昨持仓
  double previous_settlement_px; // 昨结算价
  double open_interest;          // 持仓总量
  double settlement_px;          // 今结算价
};

// 外汇交易中心-外汇最优报价行情
struct MDCForexQuote : public Quote {
  ForexMarketType forex_quote_type; // 市场行情类型
  double best_rate_buy;             // 最优买报价
  double best_rate_sell;            // 最优卖报价
};

// 外汇交易中心-外汇市场行情
struct MDCForexSnapshot : public Quote {
  ForexMarketType forex_snapshot_type; // 市场行情类型
  double last_rate_buy;                // 最新交易买价
  double last_rate_sell;               // 最新交易卖价
  double last_allin_buy;               // 最新买方全价
  double last_allin_sell;              // 最新卖方全价
  Side rate_side;                      // 最新交易价买卖方向
  Side allin_side;                     // 最新交易全价买卖方向
};

// 逐笔委托
struct OrderRecord {
  char symbol[32];                // 证券代码
  int64_t timestamp;              // 交易所时间(单位:ms)
  OrderType order_type;           // 订单类型
  OrderSide order_side;           // 买卖方向
  double order_price;             // 委托价格
  double order_qty;               // 委托数量
  int64_t order_index;            // 委托编号
  SecurityStatus security_status; // 产品状态，仅orderType==STATUS时有效
  int64_t order_no;     // 原始订单号（上交所在新增、删除订单时用以标识订单的唯一编号）
  int64_t appl_seq_num; // 交易所原始消息记录号（同频道内自1开始计数）
  int32_t channel_no;   // 交易所原始频道代码
  int64_t recv_time;    // 接收时间(单位:ns)
  MdSource source;      // 行情源
};

// 逐笔成交
struct TradeRecord {
  char symbol[32];       // 证券代码
  int64_t timestamp;     // 交易所时间(单位:ms)
  Side side;             // 成交方向
  Type type;             // 成交类型
  double price;          // 成交价格
  double quantity;       // 成交数量
  double turnover;       // 成交金额
  int64_t trade_index;   // 成交编号
  int64_t trade_buy_no;  // 买方委托序号
  int64_t trade_sell_no; // 卖方委托序号
  int64_t appl_seq_num;  // 交易所原始消息记录号（同频道内自1开始计数）
  int64_t channel_no;    // 交易所原始频道代码
  int64_t recv_time;     // 接收时间(单位:ns)
  MdSource source;       // 行情源
};

} // namespace huatai::atsquant::common
