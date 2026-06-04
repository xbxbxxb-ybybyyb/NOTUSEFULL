#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <arrow/status.h>

namespace huatai::atsquant::factor {

class FactorOrderQtyChangeEachLevelSell_n_tick20 : public Factor<> {
  static const int LAG = 60;

  TimeSlidingWindow<double> lag_window{LAG};

public:
  FactorOrderQtyChangeEachLevelSell_n_tick20() { type_ = __func__; }

  Status caculate() override {

    auto row_tick = get_market_data().get_prev_n_quote(2);
    if (row_tick.len() < 2) {
      return Status::OK();
    }

    auto now_tick = row_tick[1];
    auto prev_tick = row_tick[0];

    auto prev_ask_vol = prev_tick.list_item<QuoteSchema::Index::ASK_QTY>()[1];
    auto cur_ask_vol = now_tick.list_item<QuoteSchema::Index::ASK_QTY>()[1];
    auto cur_time = now_tick.item<QuoteSchema::Index::TRIGGER_TIME>();

    auto delta_ask_vol = cur_ask_vol - prev_ask_vol;
    lag_window.push(cur_time, delta_ask_vol);
    auto ask_speed = compute::sum(lag_window) / (lag_window.size());
    value() = ask_speed;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor