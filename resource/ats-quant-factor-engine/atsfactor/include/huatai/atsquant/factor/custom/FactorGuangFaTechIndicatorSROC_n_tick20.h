#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorGuangFaTechIndicatorSROC_n_tick20 : public Factor<> {
  static const int SHORT_SECONDS = 60;
  static const int LAG = 2;
  SlidingWindow<double> lag_list{LAG};
  TimeSlidingWindow<double> short_window_list{SHORT_SECONDS};
  TimeSlidingWindow<double> emap_list{SHORT_SECONDS};


public:
  FactorGuangFaTechIndicatorSROC_n_tick20() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(2);
    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto lastpx_now = window.item<QuoteSchema::Index::LAST_PX>();
    short_window_list.push(now_time, lastpx_now);
    auto emap = compute::mean(short_window_list);
    lag_list.push(emap);
    emap_list.push(now_time,emap);
    auto temp = (emap - emap_list.front()) / lag_list.front();
    value() = temp;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor