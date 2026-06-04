#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorCMO_timePeriod20 : public Factor<> {
  static const int TIME_PERIOD = 20;

public:
  FactorCMO_timePeriod20() { type_ = __func__; }

  Status caculate() override {
    auto table = get_market_data().get_prev_n_quote(TIME_PERIOD + 1);
    if (table.len() < TIME_PERIOD) {
      value() = 0;
      return Status::OK();
    }

    const auto *lastpx = table.item_address<QuoteSchema::Index::LAST_PX>();
    auto delta_lastpx = compute::diff<TIME_PERIOD + 1>(lastpx);
    auto loss = delta_lastpx;
    std::for_each(loss.begin(), loss.end(), [](auto &e) { e = e < 0 ? -e : 0; });
    auto gain = delta_lastpx;
    std::for_each(gain.begin(), gain.end(), [](auto &e) { e = e > 0 ? e : 0; });

    // alpha = 0.5
    auto loss_avg = compute::ewa(loss, 0.5);
    auto gain_avg = compute::ewa(gain, 0.5);
    auto gain_loss_avg = gain_avg + loss_avg;
    value() = gain_loss_avg == 0 ? 0 : (gain_avg - loss_avg) / gain_loss_avg;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor