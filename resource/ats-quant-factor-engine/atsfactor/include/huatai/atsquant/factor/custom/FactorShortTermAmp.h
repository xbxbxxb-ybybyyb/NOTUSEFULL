#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorShortTermAmp : public Factor<> {
  static const int SECONDS = 30;
  TimeSlidingWindow<double> orders_list{SECONDS};

public:
  FactorShortTermAmp() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(1);
    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto lastpx = window.item<QuoteSchema::Index::LAST_PX>();
    orders_list.push(now_time, lastpx);
    auto max_px = compute::max(orders_list);
    auto min_px = compute::min(orders_list);
    auto temp = 1000*(max_px - min_px) / orders_list[0];
    value() = temp;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor