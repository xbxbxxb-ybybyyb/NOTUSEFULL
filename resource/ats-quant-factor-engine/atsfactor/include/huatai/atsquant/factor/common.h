#pragma once

#include <arrow/api.h>
#include <cstdint>

#include "huatai/atsquant/factor/util.h"

#if ATSFACTOR_DEVELOPMENT_MODE == 1
#include "huatai/atsquant/market_data_def.h"
#endif

namespace huatai::atsquant::common {

#if ATSFACTOR_DEVELOPMENT_MODE == 1
struct FACTOR_EXPORT OrderPosInfo {
  uint32_t level = 0;     // 订单档位，0表示在一档，以次类推
  uint64_t order_no = 0;  // 订单号,和行情中的订单号一致
  uint64_t order_pos = 0; // 该订单号处于所在的档位中的位置，0表示在第一位，以次类推
  uint64_t previous_order_count = 0; // 所处档位该订单号前的行情未成交数量
};

struct OrderCancel {
  uint32_t market_data_type; // 触发合成的行情类型，1 = 委托,2 = 撤单
  uint32_t channel_no;       // 通道号
  double price; // 委托数据时表示委托价格,如果完全是还原出来的委托，则取最新价。撤单时表示原委托价格
  double quantity; // 委托数据时表示原始委托数量。撤单时表示撤单数量
  uint32_t side; // 委托数据时表示买卖方向：1 = 买,2 = 卖。撤单时表示原委托方向：1 = 买,2 = 卖
  uint32_t order_type; // 订单类别,1=市价,2=限价,3=本方最优,上交所只有2，只在委托类型时有意义,撤单时统一设置为0。
};

struct FACTOR_EXPORT QuoteIndicator {
  char symbol[16];                   // 标的名称
  uint64_t indicator_time;           // 指标生成时间戳,纳秒单位
  bool invalid;                      // 指标数据是否有效,通道数据丢失,或者盘口不稳定,该值为true
  double last_px;                    // 最新价
  double high_px;                    // 最高价
  double low_px;                     // 最低价
  double total_volume;               // 成交总量
  double total_turnover;             // 成交总金额
  double total_ask_qty;              // 卖方盘口总委托量
  double total_bid_qty;              // 买方盘口总委托量
  uint64_t trades;                   // 总成交笔数
  uint64_t trigger_appl_seq_num;     // 触发合成的序列号
  uint32_t trigger_time;             // 逐笔触发模式时表示逐笔数据的行情时间
  double bid_qty[10] = {0};          // 买方档位--数量
  double bid_price[10] = {0};        // 买方档位--价格
  uint64_t bid_order_nums[10] = {0}; // 买方档位--笔数
  double ask_qty[10] = {0};          // 卖方档位--数量
  double ask_price[10] = {0};        // 卖方档位--价格
  uint64_t ask_order_nums[10] = {0}; // 卖方档位--笔数
  double avg_buy_price;              // 买方平均价
  double avg_sell_price;             // 卖方平均价
  uint32_t extension; // 扩展类型，0表示后面无扩展，1表示后面带订单位置信息，2表示后面带给dolphindb因子的委托数据信息
};

struct FACTOR_EXPORT QuoteIndicatorOrderCancel : public QuoteIndicator {
  OrderCancel order_cancel;
};
#else
struct OrderPosInfo;
struct OrderCancel;
struct QuoteIndicator;
struct QuoteIndicatorOrderCancel;
#endif

} // namespace huatai::atsquant::common
