#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorGtjaAlpha078 : public Factor<> {
  static const int SHORT_SECONDS = 9;
  static const int LONG_SECONDS = 36;

  TimeSlidingWindow<double> short_window_list{SHORT_SECONDS};
  TimeSlidingWindow<double> long_window_list{LONG_SECONDS};

public:
  FactorGtjaAlpha078() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(1);

    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto lastpx_now = window.item<QuoteSchema::Index::LAST_PX>();
    auto highpx_now = window.item<QuoteSchema::Index::HIGH_PX>();
    auto lowpx_now = window.item<QuoteSchema::Index::LOW_PX>();
    auto sumpx_now = lowpx_now + highpx_now + lastpx_now;

    short_window_list.push(now_time, sumpx_now);
    auto mean_sum_window = compute::mean(short_window_list);

    auto temp1 = sumpx_now - mean_sum_window;
    auto temp2 = std::abs(lastpx_now - mean_sum_window);
    long_window_list.push(now_time, temp2);
    auto temp = temp1/compute::mean(long_window_list);
    value() = temp;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor