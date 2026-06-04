#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorBookBuy13MoveQtyDeltaSum : public Factor<> {

public:
  FactorBookBuy13MoveQtyDeltaSum() { type_ = __func__; }

  Status caculate() override {

    auto prev_value = value();
    auto table = get_market_data().get_prev_n_quote(2);
    if (table.len() <= 1) {
      return Status::OK();
    }
    auto *bidqty_now_list = table[1].list_item<QuoteSchema::Index::BID_QTY>();
    auto *bidqty_prev_list = table.list_item<QuoteSchema::Index::BID_QTY>();
    auto deltas = 0.0;
    for (int i = 0; i < 3; i++) {
      deltas += bidqty_now_list[i] - bidqty_prev_list[i];
    }
    value() = prev_value + deltas;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor