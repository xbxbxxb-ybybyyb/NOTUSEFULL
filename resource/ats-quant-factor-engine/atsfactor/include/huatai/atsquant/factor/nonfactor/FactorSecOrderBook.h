#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include "huatai/atsquant/factor/schema.h"
#include "huatai/atsquant/factor/util.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorSecOrderBook : public Factor<> {
  static const int lag1 = 120;

public:
  FactorSecOrderBook() { type_ = __func__; }
  SlidingWindow<double> last_px_list{lag1};
  SlidingWindow<double> high_px_list{lag1};
  SlidingWindow<double> low_px_list{lag1};
  SlidingWindow<double> total_volume_list{lag1};
  SlidingWindow<double> total_turnover_list{lag1};
  SlidingWindow<double> total_ask_qty_list{lag1};
  SlidingWindow<double> total_bid_qty_list{lag1};
  SlidingWindow<double> trades_list{lag1};
  // SlidingWindow<int> trigger_appl_seq_num_list{lag1};
  SlidingWindow<uint64_t> trigger_time_list{lag1};
  SlidingWindow<const double *> bid_qty_list{lag1};
  SlidingWindow<const double *> bid_price_list{lag1};
  SlidingWindow<const uint64_t *> bid_order_nums_list{lag1};
  SlidingWindow<const double *> ask_qty_list{lag1};
  SlidingWindow<const double *> ask_price_list{lag1};
  SlidingWindow<const uint64_t *> ask_order_nums_list{lag1};

  Status caculate() override {
    auto current_quote = get_market_data().get_prev_n_quote(1);
    auto sample_1s_flag = current_quote.item<QuoteSchema::Index::SAMPLE_1S_FLAG>();
    if (!sample_1s_flag) {
      return Status::OK();
    }

    // 获取上一秒最后一根盘口数据
    auto last_quotes = get_market_data().get_prev_n_quote(2);
    if (last_quotes.len() < 2) {
      return Status::OK();
    }

    auto last_quote = last_quotes[0];
    last_px_list.push(last_quote.item<QuoteSchema::Index::LAST_PX>());
    high_px_list.push(last_quote.item<QuoteSchema::Index::HIGH_PX>());
    low_px_list.push(last_quote.item<QuoteSchema::Index::LOW_PX>());
    total_volume_list.push(last_quote.item<QuoteSchema::Index::TOTAL_VOLUME>());
    total_turnover_list.push(last_quote.item<QuoteSchema::Index::TOTAL_TURNOVER>());
    total_ask_qty_list.push(last_quote.item<QuoteSchema::Index::TOTAL_ASK_QTY>());
    total_bid_qty_list.push(last_quote.item<QuoteSchema::Index::TOTAL_BID_QTY>());
    trades_list.push(last_quote.item<QuoteSchema::Index::TRADES>());
    trigger_time_list.push(last_quote.item<QuoteSchema::Index::TRIGGER_TIME>());
    bid_qty_list.push(last_quote.list_item<QuoteSchema::Index::BID_QTY>());
    bid_price_list.push(last_quote.list_item<QuoteSchema::Index::BID_PRICE>());
    bid_order_nums_list.push(last_quote.list_item<QuoteSchema::Index::BID_ORDER_NUMS>());
    ask_qty_list.push(last_quote.list_item<QuoteSchema::Index::ASK_QTY>());
    ask_price_list.push(last_quote.list_item<QuoteSchema::Index::ASK_PRICE>());
    ask_order_nums_list.push(last_quote.list_item<QuoteSchema::Index::ASK_ORDER_NUMS>());
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor
