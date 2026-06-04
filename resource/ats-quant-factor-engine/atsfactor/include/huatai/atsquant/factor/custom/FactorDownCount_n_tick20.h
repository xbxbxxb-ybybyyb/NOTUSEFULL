#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorDownCount_n_tick20 : public Factor<> {
  static const int SHORT_SECONDS = 60;

  TimeSlidingWindow<double> time_window_list{SHORT_SECONDS};

public:
  FactorDownCount_n_tick20() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(2);
    if (window.len() < 2) {
      auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
      time_window_list.push(now_time, 1);
      value() = compute::mean(time_window_list);
      return Status::OK();
    }

    auto now = window[-1];
    auto pre = window[0];
    auto now_time = now.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto lastpx_now = now.item<QuoteSchema::Index::LAST_PX>();
    auto lastpx_pre = pre.item<QuoteSchema::Index::LAST_PX>();
    auto delta_laspx = lastpx_now - lastpx_pre;
    auto lastpx_tag = delta_laspx < 0 ? 1 : 0;

    time_window_list.push(now_time, lastpx_tag);
    auto mean_lastpx_tag = compute::mean(time_window_list);
    value() = mean_lastpx_tag;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor