#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorBuyVolumeAvgLS : public Factor<> {
  static const int SHORT_SECONDS = 60;
  static const int LONG_SECONDS = 300;

  TimeSlidingWindow<double> long_list{LONG_SECONDS};
  TimeSlidingWindow<double> short_list{SHORT_SECONDS};

public:
  FactorBuyVolumeAvgLS() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(1);

    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();

    const auto *buy_qty = window.list_item<QuoteSchema::Index::BID_QTY>();
    auto buy_qty_mean = compute::sum(buy_qty, 10);
    long_list.push(now_time, buy_qty_mean);
    short_list.push(now_time, buy_qty_mean);
    auto short_mean_bidqty = compute::mean(short_list);
    auto long_mean_bidqty = compute::mean(long_list);
    value() = long_mean_bidqty == 0 ? 0.0 : short_mean_bidqty / long_mean_bidqty;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor