#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorGuangFaTechIndicatorENV_n_tick20 : public Factor<> {
  static const int SHORT_SECONDS = 60;
  double threshold = 0.002;
  TimeSlidingWindow<double> short_window_list{SHORT_SECONDS};

public:
  FactorGuangFaTechIndicatorENV_n_tick20() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(1);
    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto lastpx_now = window.item<QuoteSchema::Index::LAST_PX>();
    short_window_list.push(now_time, lastpx_now);
    auto mean_lastpx_window = compute::mean(short_window_list);
    auto upper = mean_lastpx_window * (1 + threshold);
    auto lower = mean_lastpx_window * (1 - threshold);
    auto temp = ((lastpx_now - upper) > 0) - ((lastpx_now - lower) < 0);

    value() = temp;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor