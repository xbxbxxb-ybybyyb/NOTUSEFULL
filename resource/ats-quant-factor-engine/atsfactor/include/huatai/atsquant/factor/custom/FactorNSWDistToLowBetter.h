#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <arrow/status.h>

namespace huatai::atsquant::factor {

class FactorNSWDistToLowBetter : public Factor<> {
  static const int LAG = 10;
  SlidingWindow<double> mid_price_list{LAG};

public:
  FactorNSWDistToLowBetter() { type_ = __func__; }

  Status caculate() override {
    auto row_tick = get_market_data().get_prev_n_quote(1);

    const auto *current_tick_ask_p = row_tick.list_item<QuoteSchema::Index::ASK_PRICE>();
    const auto *current_tick_bid_p = row_tick.list_item<QuoteSchema::Index::BID_PRICE>();
    auto ask1_price = current_tick_ask_p[0];
    auto bid1_price = current_tick_bid_p[0];
    auto mid_price = (ask1_price + bid1_price) / 2;
    if (ask1_price == 0 || bid1_price == 0) {
      mid_price = ask1_price + bid1_price;
    }
    mid_price_list.push(mid_price);
    if(mid_price_list.size()<LAG){
      value()=0.0;
      return Status::OK();
    }
    auto low_px = compute::min(mid_price_list);
    if (low_px < 0.01) {
      value() = 0;
    } else {
      value() = 1000 * (mid_price / low_px - 1);
    }
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor