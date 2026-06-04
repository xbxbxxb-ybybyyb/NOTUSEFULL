#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorChangeSumLS : public Factor<> {
  static const int SHORT_SECONDS = 60;
  static const int LONG_SECONDS = 300;

  TimeSlidingWindow<double> long_list{LONG_SECONDS};
  TimeSlidingWindow<double> short_list{SHORT_SECONDS};

public:
  FactorChangeSumLS() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(2);
    if (window.len() < 2) {
      return Status::OK();
    }

    auto now = window[-1];
    auto pre = window[0];
    auto now_time = now.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto lastpx_now = now.item<QuoteSchema::Index::LAST_PX>();
    auto lastpx_pre = pre.item<QuoteSchema::Index::LAST_PX>();
    auto delta_laspx = std::abs(lastpx_now - lastpx_pre);

    long_list.push(now_time, delta_laspx);
    short_list.push(now_time, delta_laspx);
    auto short_sum_lastpx = compute::sum(short_list);
    auto long_sum_lastpx = compute::sum(long_list);
    value() = long_sum_lastpx == 0 ? 0.0 : short_sum_lastpx / long_sum_lastpx;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor