#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <algorithm>

namespace huatai::atsquant::factor {

class FactorBookSellSumQtyLastPreRatio : public Factor<> {
  static const int SECONDS = 300;
  TimeSlidingWindow<double> sell_qty_value{SECONDS};

public:
  FactorBookSellSumQtyLastPreRatio() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(1);
    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
    const auto *sellqty_now = window.list_item<QuoteSchema::Index::ASK_QTY>();
    auto sum_sellqty = compute::sum(sellqty_now, 10);
    sell_qty_value.push(now_time, sum_sellqty);
    auto max_sum_qty = compute::max(sell_qty_value);
    value() = sum_sellqty / max_sum_qty;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor