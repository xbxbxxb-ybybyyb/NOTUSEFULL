#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <algorithm>

namespace huatai::atsquant::factor {

class FactorBidAskSpread_n_tick10 : public Factor<> {
  static const int TIME_PERIOD = 30;
  TimeSlidingWindow<double> time_window{TIME_PERIOD};


public:
  FactorBidAskSpread_n_tick10() { type_ = __func__; }

  Status caculate() override {

    auto now_tick = get_market_data().get_prev_n_quote(1);
    auto const *ask_price = now_tick.list_item<QuoteSchema::Index::ASK_PRICE>();
    auto const *bid_price = now_tick.list_item<QuoteSchema::Index::BID_PRICE>();
    auto now_time = now_tick.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto ask1_price = ask_price[0];
    auto bid1_price = bid_price[0];
    auto diff_price = ask1_price - bid1_price;
    time_window.push(now_time, diff_price);

    auto std_diff = compute::std(time_window);
    value() = std_diff;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor