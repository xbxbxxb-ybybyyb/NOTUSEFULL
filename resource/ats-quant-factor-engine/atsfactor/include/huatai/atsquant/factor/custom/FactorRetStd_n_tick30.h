#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <arrow/status.h>

namespace huatai::atsquant::factor {

class FactorRetStd_n_tick30 : public Factor<> {
  static const int LAG = 90;
  TimeSlidingWindow<double> lag_window{LAG};
  TimeSlidingWindow<double> std_window{LAG};

public:
  FactorRetStd_n_tick30() { type_ = __func__; }

  Status caculate() override {

    auto row_tick = get_market_data().get_prev_n_quote(1);
    auto last_px = row_tick.item<QuoteSchema::Index::LAST_PX>();
    auto cur_time = row_tick.item<QuoteSchema::Index::TRIGGER_TIME>();
    lag_window.push(cur_time, last_px);
    auto temp1 = last_px / lag_window[0];
    std_window.push(cur_time, temp1);
    value() = compute::std(std_window);

    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor