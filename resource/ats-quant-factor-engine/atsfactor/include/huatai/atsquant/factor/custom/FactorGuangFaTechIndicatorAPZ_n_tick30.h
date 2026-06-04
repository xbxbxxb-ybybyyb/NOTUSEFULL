#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorGuangFaTechIndicatorAPZ_n_tick30 : public Factor<> {
  static const int SHORT_SECONDS = 90;
  static const int LONG_SECONDS = 180;

  TimeSlidingWindow<double> short_window_list{SHORT_SECONDS};
  TimeSlidingWindow<double> long_window_list{LONG_SECONDS};

public:
  FactorGuangFaTechIndicatorAPZ_n_tick30() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(1);

    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto lastpx_now = window.item<QuoteSchema::Index::LAST_PX>();
    auto highpx_now = window.item<QuoteSchema::Index::HIGH_PX>();
    auto lowpx_now = window.item<QuoteSchema::Index::LOW_PX>();

    short_window_list.push(now_time, lastpx_now);
    long_window_list.push(now_time, lastpx_now);
    auto vol = compute::std(short_window_list);
    auto upper = compute::mean(long_window_list) + vol;
    auto lower = compute::mean(long_window_list) - vol;
    auto temp = ((lastpx_now - upper) > 0) - ((lastpx_now - lower) < 0);

    value() = temp;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor