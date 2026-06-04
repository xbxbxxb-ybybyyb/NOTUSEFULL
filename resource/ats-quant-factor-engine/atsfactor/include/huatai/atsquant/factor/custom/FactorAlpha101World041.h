#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {
class FactorAlpha101World041 : public Factor<> {
public:
  FactorAlpha101World041() { type_ = __func__; }

  Status caculate() override {
    // static int index = 0;
    // index++;

    auto market_prev2 = get_market_data().get_prev_n_quote(2);
    if (market_prev2.len() <= 1) {
      return Status::OK();
    }

    auto now = market_prev2[1];
    auto total_value_prev = market_prev2.item<QuoteSchema::Index::TOTAL_TURNOVER>();
    auto total_volume_prev = market_prev2.item<QuoteSchema::Index::TOTAL_VOLUME>();
    auto total_value_now = now.item<QuoteSchema::Index::TOTAL_TURNOVER>();
    auto total_volume_now = now.item<QuoteSchema::Index::TOTAL_VOLUME>();
    if (abs(total_value_now - total_value_prev) <= 1e-4 || abs(total_volume_now - total_volume_prev) <= 1e-4) {
      value() = 0;
      return Status::OK();
    }
    auto vwap = (total_value_now - total_value_prev) / (total_volume_now - total_volume_prev);
    auto highpx = now.item<QuoteSchema::Index::HIGH_PX>();
    auto lowpx = now.item<QuoteSchema::Index::LOW_PX>();
    auto lastpx = now.item<QuoteSchema::Index::LAST_PX>();
    auto sqrtpx = sqrt(highpx * lowpx);

    value() = 100 * (sqrtpx - vwap);

    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor