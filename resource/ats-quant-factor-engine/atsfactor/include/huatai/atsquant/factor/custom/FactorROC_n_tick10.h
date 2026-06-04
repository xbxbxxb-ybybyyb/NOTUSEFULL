// ROC                  Rate of change : ((price/prevPrice)-1)*100
#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <arrow/status.h>

namespace huatai::atsquant::factor {

class FactorROC_n_tick10 : public Factor<> {
  static const int LAG = 11;
  TimeSlidingWindow<double> lag_window{LAG};

public:
  FactorROC_n_tick10() { type_ = __func__; }
  Status caculate() override {

    auto row_tick = get_market_data().get_prev_n_quote(1);
    auto last_px = row_tick.item<QuoteSchema::Index::LAST_PX>();
    auto now_time = row_tick.item<QuoteSchema::Index::TRIGGER_TIME>();
    lag_window.push(now_time, last_px);
    if (lag_window.size() < LAG) {
      value() = 0.0;
      return Status::OK();
    }
    auto temp1 = 100 * (last_px / lag_window.front() - 1);
    value() = temp1;

    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor