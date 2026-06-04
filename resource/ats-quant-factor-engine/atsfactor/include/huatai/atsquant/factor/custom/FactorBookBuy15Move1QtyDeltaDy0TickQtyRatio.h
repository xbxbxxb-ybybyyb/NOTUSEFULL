#pragma once

#include "arrow/status.h"
#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {
class FactorBookBuy15Move1QtyDeltaDy0TickQtyRatio : public Factor<> {
public:
  FactorBookBuy15Move1QtyDeltaDy0TickQtyRatio() { type_ = __func__; }
  static const int SECONDS = 300;

  TimeSlidingWindow<double> bigger_bid_vol_qty_queue{SECONDS};
  TimeSlidingWindow<double> bid_vol_qty_queue{SECONDS};

  Status caculate() override {
    value() = 0;
    const auto row_ticks = get_market_data().get_prev_n_quote(2);
    if(row_ticks.len()<2){
      value() = 0;
      auto current_t = row_ticks.item<QuoteSchema::Index::TRIGGER_TIME>();
      bigger_bid_vol_qty_queue.push(current_t,0);
      bid_vol_qty_queue.push(current_t,compute::sum(row_ticks.list_item<QuoteSchema::Index::BID_QTY>(), 10));
      return Status::OK();
    }

    const auto last_tick = row_ticks[0];
    const auto current_tick = row_ticks[-1];
    auto last_bid_v = compute::sum(last_tick.list_item<QuoteSchema::Index::BID_QTY>(), 5);
    auto current_bid_v = compute::sum(current_tick.list_item<QuoteSchema::Index::BID_QTY>(), 5);
    auto last_t = current_tick.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto current_t = current_tick.item<QuoteSchema::Index::TRIGGER_TIME>();
    // todo 获取秒，如果到下一秒才计算

    if (current_bid_v - last_bid_v > 0) {
      bigger_bid_vol_qty_queue.push(current_t,compute::sum(current_tick.list_item<QuoteSchema::Index::BID_QTY>(), 10));
    } else {
      bigger_bid_vol_qty_queue.push(current_t,0);
    }
    bid_vol_qty_queue.push(current_t,compute::sum(current_tick.list_item<QuoteSchema::Index::BID_QTY>(), 10));

    value() = compute::sum(bigger_bid_vol_qty_queue) / compute::sum(bid_vol_qty_queue);

    return Status::OK();
  }
};
} // namespace huatai::atsquant::factor