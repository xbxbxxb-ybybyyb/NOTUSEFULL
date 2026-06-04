#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorSkew1 : public Factor<> {
  static const int SECONDS = 30;
  TimeSlidingWindow<double> ret_list{SECONDS};

public:
  FactorSkew1() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(2);
    if (window.len() < 2) {
      return Status::OK();
    }

    auto now_time = window[1];
    auto prev_time = window[0];

    auto cur_lastpx = now_time.item<QuoteSchema::Index::LAST_PX>();
    auto prev_lastpx = prev_time.item<QuoteSchema::Index::LAST_PX>();
    auto cur_time = now_time.item<QuoteSchema::Index::TRIGGER_TIME>();

    auto ret = cur_lastpx / prev_lastpx - 1;

    ret_list.push(cur_time, ret);

    auto skew = compute::skewness(ret_list);
    value() = skew;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor