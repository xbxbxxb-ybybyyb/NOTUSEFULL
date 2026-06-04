#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorTechIndicatorForSAR_n_tick10 : public Factor<> {
  static const int SECONDS = 30;

  TimeSlidingWindow<double> last_px_win{SECONDS};

public:
  FactorTechIndicatorForSAR_n_tick10() { type_ = __func__; }

  Status caculate() override {
    auto table = get_market_data().get_prev_n_quote(2);
    if (table.len() < 2) {
      value() = 0;
      auto timestamp = table.item<QuoteSchema::Index::TRIGGER_TIME>();
      auto last_px = table.item<QuoteSchema::Index::LAST_PX>();
      last_px_win.push(timestamp, last_px);
      return Status::OK();
    }

    auto now = table[1];
    auto timestamp = now.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto last_px = now.item<QuoteSchema::Index::LAST_PX>();
    last_px_win.push(timestamp, last_px);
    auto px_max = compute::max(last_px_win);
    auto ret = (last_px - last_px_win.front()) / (last_px + 1e-10);
    auto last_px_div_px_max = last_px / px_max;
    value() = last_px_div_px_max * (ret > 0 ? 1 : ret == 0 ? 0 : -1);

    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor