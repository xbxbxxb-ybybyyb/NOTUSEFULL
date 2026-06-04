// module Factors::FactorGtjaAlpha046
// @state
// def FactorGtjaAlpha046(M_MDTime, M_LastPx){
//     temp = (tmavg(M_MDTime, M_LastPx,9s) + tmavg(M_MDTime,M_LastPx,18s) + tmavg(M_MDTime,M_LastPx,27s) +
//     tmavg(M_MDTime,M_LastPx,36s)) * 0.25 \ M_LastPx FactorGtjaAlpha046 = iif(temp.isNull(), 0.0, temp) return
//     FactorGtjaAlpha046
// }

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

class FactorGtjaAlpha046 : public Factor<> {
  static const int SECONDS_1 = 9;
  static const int SECONDS_2 = 18;
  static const int SECONDS_3 = 27;
  static const int SECONDS_4 = 36;
  TimeSlidingWindow<double> time_window_list1{SECONDS_1};
  TimeSlidingWindow<double> time_window_list2{SECONDS_2};
  TimeSlidingWindow<double> time_window_list3{SECONDS_3};
  TimeSlidingWindow<double> time_window_list4{SECONDS_4};

public:
  FactorGtjaAlpha046() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(1);

    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto lastpx_now = window.item<QuoteSchema::Index::LAST_PX>();

    time_window_list1.push(now_time, lastpx_now);
    time_window_list2.push(now_time, lastpx_now);
    time_window_list3.push(now_time, lastpx_now);
    time_window_list4.push(now_time, lastpx_now);
    auto weighted_avg = (compute::mean(time_window_list1) + compute::mean(time_window_list2) +
                         compute::mean(time_window_list3) + compute::mean(time_window_list4)) *
                        0.25;
    auto temp = weighted_avg / lastpx_now;
    value() = temp;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor