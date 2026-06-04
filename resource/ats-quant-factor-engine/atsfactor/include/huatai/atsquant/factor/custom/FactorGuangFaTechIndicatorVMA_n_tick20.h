#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorGuangFaTechIndicatorVMA_n_tick20 : public Factor<> {
  static const int SHORT_SECONDS = 60;
  TimeSlidingWindow<double> short_window_list{SHORT_SECONDS};

public:
  FactorGuangFaTechIndicatorVMA_n_tick20() { type_ = __func__; }

  Status caculate() override {
    static int index = 0;
    index++;
    auto window = get_market_data().get_prev_n_sec_quote(1);
    if (window.len() < 1) {
      return Status::OK();
    }

    auto now = window[-1];
    auto now_time = now.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto lastpx_now = now.item<QuoteSchema::Index::LAST_PX>();
    auto highpx_now = now.item<QuoteSchema::Index::HIGH_PX>();
    auto lowpx_now = now.item<QuoteSchema::Index::LOW_PX>();
    auto avg_price = (lastpx_now + highpx_now + lowpx_now) / 3.0;

    short_window_list.push(now_time, avg_price);

    auto vma = compute::mean(short_window_list);
    auto temp = (avg_price - vma) > 0;
    value() = temp;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor