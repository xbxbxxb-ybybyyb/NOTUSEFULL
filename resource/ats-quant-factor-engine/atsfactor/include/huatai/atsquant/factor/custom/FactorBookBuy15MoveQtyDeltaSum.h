#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorBookBuy15MoveQtyDeltaSum : public Factor<> {

public:
  FactorBookBuy15MoveQtyDeltaSum() { type_ = __func__; }

  Status caculate() override {
    static double cumsum_qty = 0.0;
    auto table = get_market_data().get_prev_n_quote(2);
    if (table.len() < 2) {
      value() = 0;

      return Status::OK();
    }
    const auto *bidqty_now_list = table[-1].list_item<QuoteSchema::Index::BID_QTY>();
    auto *bidqty_prev_list = table[0].list_item<QuoteSchema::Index::BID_QTY>();
    auto now_sum = compute::sum(bidqty_now_list, 5);
    auto prev_sum = compute::sum(bidqty_prev_list, 5);
    cumsum_qty = cumsum_qty + now_sum - prev_sum;
    auto ratios = cumsum_qty / now_sum;
    value() = ratios;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor