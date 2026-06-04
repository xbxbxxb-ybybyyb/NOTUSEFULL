#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorGtjaAlpha047_n_tick10 : public Factor<> {
  static const int SECONDS = 30;
  TimeSlidingWindow<double> high_window_list{SECONDS};
  TimeSlidingWindow<double> low_window_list{SECONDS};
  TimeSlidingWindow<double> distance_window_list{SECONDS};

public:
  FactorGtjaAlpha047_n_tick10() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(1);

    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto lastpx_now = window.item<QuoteSchema::Index::LAST_PX>();
    auto highpx_now = window.item<QuoteSchema::Index::HIGH_PX>();
    auto lowpx_now = window.item<QuoteSchema::Index::LOW_PX>();

    low_window_list.push(now_time, lowpx_now);
    high_window_list.push(now_time, highpx_now);
    auto max_high_window = compute::max(high_window_list);
    auto min_low_window = compute::min(low_window_list);
    auto distance = (max_high_window - lastpx_now) / (max_high_window - min_low_window);
    distance_window_list.push(now_time, distance);

    auto temp = compute::mean(distance_window_list);

    value() = temp;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor