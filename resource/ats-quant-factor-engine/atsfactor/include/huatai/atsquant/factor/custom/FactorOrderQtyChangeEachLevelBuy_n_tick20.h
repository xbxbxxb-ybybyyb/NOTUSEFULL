#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <arrow/status.h>

namespace huatai::atsquant::factor {

class FactorOrderQtyChangeEachLevelBuy_n_tick20 : public Factor<> {
  static const int LAG = 60;

  TimeSlidingWindow<double> lag_window{LAG};

public:
  FactorOrderQtyChangeEachLevelBuy_n_tick20() { type_ = __func__; }

  Status caculate() override {

    auto row_tick = get_market_data().get_prev_n_quote(2);
    if (row_tick.len() < 2) {
      return Status::OK();
    }

    auto now_tick = row_tick[1];
    auto prev_tick = row_tick[0];

    auto prev_bid_vol = prev_tick.list_item<QuoteSchema::Index::BID_QTY>()[1];
    auto cur_bid_vol = now_tick.list_item<QuoteSchema::Index::BID_QTY>()[1];
    auto cur_time = now_tick.item<QuoteSchema::Index::TRIGGER_TIME>();

    auto delta_bid_vol = cur_bid_vol - prev_bid_vol;
    lag_window.push(cur_time, delta_bid_vol);
    auto bid_speed = compute::sum(lag_window) / (lag_window.size());
    value() = bid_speed;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor