#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorNSWBoll : public Factor<> {
  static const int boll_lag = 10;
  SlidingWindow<double> mid_price_window{boll_lag};
  SlidingWindow<double> delta_price_window{boll_lag};

public:
  FactorNSWBoll() { type_ = __func__; }

  Status caculate() override {
    auto row_tick = get_market_data().get_prev_n_quote(1);
    const auto *current_tick_ask_p = row_tick.list_item<QuoteSchema::Index::ASK_PRICE>();
    const auto *current_tick_bid_p = row_tick.list_item<QuoteSchema::Index::BID_PRICE>();

    auto sell1_price = current_tick_ask_p[0];
    auto buy1_price = current_tick_bid_p[0];
    auto mid_price = (sell1_price == 0 || buy1_price == 0) ? sell1_price + buy1_price : (sell1_price + buy1_price)/2;
    mid_price_window.push(mid_price);

    auto center_price = compute::mean(mid_price_window);

    delta_price_window.push(mid_price - center_price);

    auto md =
        (compute::max(mid_price_window) <= compute::min(mid_price_window)) ? 0.0 : compute::std(delta_price_window);
    auto up_boll = center_price + 2 * md;
    auto down_boll = center_price - 2 * md;

    if (up_boll - down_boll <= 1e-6) {
      value() = 0.5;
    } else {
      value() = (mid_price - down_boll) / (4 * md);
    }
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor