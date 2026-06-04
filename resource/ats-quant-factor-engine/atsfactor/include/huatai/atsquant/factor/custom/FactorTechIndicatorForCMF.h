#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorTechIndicatorForCMF : public Factor<> {
  static const int SECONDS = 30;

public:
  FactorTechIndicatorForCMF() { type_ = __func__; }

  TimeSlidingWindow<double> volume_win{SECONDS};
  TimeSlidingWindow<double> mfv_win{SECONDS};

  Status caculate() override {
    auto table = get_market_data().get_prev_n_quote(2);
    if (table.len() < 2) {
      value() = 0;
      return Status::OK();
    }

    auto now = table[1];
    auto timestamp = now.item<QuoteSchema::Index::TRIGGER_TIME>();
    const auto *total_volume = table.item_address<QuoteSchema::Index::TOTAL_VOLUME>();
    auto volume = total_volume[1] - total_volume[0];
    volume_win.push(timestamp, volume);

    auto last_px = now.item<QuoteSchema::Index::LAST_PX>();
    auto bid1_price = now.list_item<QuoteSchema::Index::BID_PRICE>()[0];
    auto ask1_price = now.list_item<QuoteSchema::Index::ASK_PRICE>()[0];
    auto mfv = (2 * last_px - bid1_price - ask1_price) / (ask1_price - bid1_price) * volume;
    mfv_win.push(timestamp, mfv);

    auto a = compute::mean(mfv_win);
    auto b = compute::mean(volume_win);

    value() = a / b;

    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor