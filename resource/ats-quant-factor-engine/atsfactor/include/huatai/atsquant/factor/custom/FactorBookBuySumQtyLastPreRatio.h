#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <algorithm>

namespace huatai::atsquant::factor {

class FactorBookBuySumQtyLastPreRatio : public Factor<> {
  static const int SECONDS = 100;
  TimeSlidingWindow<double> buy_qty_value{SECONDS};

public:
  FactorBookBuySumQtyLastPreRatio() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(1);

    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
    const auto *buyqty_now = window.list_item<QuoteSchema::Index::BID_QTY>();
    auto sum_buyqty = compute::sum(buyqty_now, 10);
    buy_qty_value.push(now_time, sum_buyqty);
    auto max_sum_qty = compute::max(buy_qty_value);
    value() = sum_buyqty / max_sum_qty;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor