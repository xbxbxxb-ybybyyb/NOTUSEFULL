// module Factors::FactorGtjaAlpha015_n_tick20

// @state

// def FactorGtjaAlpha015_n_tick20(M_MDTime, M_OpenPx, M_LastPx, n_tick='60s'){
//     n_tick_window = duration(n_tick)
//     temp = M_OpenPx/tmavg(M_MDTime, M_LastPx,n_tick_window) - 1
//     FactorGtjaAlpha015_n_tick20 = iif(temp.isNull(), 0.0, temp)
//     return FactorGtjaAlpha015_n_tick20

// }
#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorGtjaAlpha015_n_tick20 : public Factor<> {
  static const int SHORT_SECONDS = 10;

  TimeSlidingWindow<double> time_window_list{SHORT_SECONDS};

public:
  FactorGtjaAlpha015_n_tick20() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(1);

    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto lastpx_now = window.item<QuoteSchema::Index::LAST_PX>();
    auto highpx_now = window.item<QuoteSchema::Index::HIGH_PX>();

    time_window_list.push(now_time, lastpx_now);
    auto mean_lastpx_tag = compute::mean(time_window_list);
    auto temp = highpx_now / mean_lastpx_tag - 1;

    value() = temp;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor