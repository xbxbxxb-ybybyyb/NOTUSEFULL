#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorBearPower_n_tick10 : public Factor<> {
  static const int TIME_PERIOD = 30;

public:
  FactorBearPower_n_tick10() { type_ = __func__; }

  Status caculate() override {
    auto table = get_market_data().get_prev_n_sec_quote(TIME_PERIOD);
    auto lowpx = 0.0;
    if(table.len()==1){
      lowpx = table.item<QuoteSchema::Index::LOW_PX>();
    }
    else {
      lowpx = table[-1].item<QuoteSchema::Index::LOW_PX>();
    }
    auto *lastpx = table.item_address<QuoteSchema::Index::LAST_PX>();
    auto mean_lastpx = compute::mean(lastpx, table.len());


    value() = lowpx - mean_lastpx;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor