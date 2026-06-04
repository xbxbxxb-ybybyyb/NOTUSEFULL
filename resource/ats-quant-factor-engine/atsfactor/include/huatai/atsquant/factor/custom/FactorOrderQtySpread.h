#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <arrow/status.h>

namespace huatai::atsquant::factor {

class FactorOrderQtySpread : public Factor<> {

public:
  FactorOrderQtySpread() { type_ = __func__; }

  Status caculate() override {

    auto row_tick = get_market_data().get_prev_n_quote(1);

    const auto *cur_bid_vol = row_tick.list_item<QuoteSchema::Index::BID_QTY>();
    const auto *cur_ask_vol = row_tick.list_item<QuoteSchema::Index::ASK_QTY>();
    value() = (compute::sum(cur_bid_vol, 10) - compute::sum(cur_ask_vol, 10)) /
              (compute::sum(cur_bid_vol, 10) + compute::sum(cur_ask_vol, 10));

    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor