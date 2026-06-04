#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorSlicePressure : public Factor<> {

public:
  FactorSlicePressure() { type_ = __func__; }

  Status caculate() override {
    auto now_time = get_market_data().get_prev_n_quote(1);
    const auto *cur_bid_qty = now_time.list_item<QuoteSchema::Index::BID_QTY>();
    const auto *cur_ask_qty = now_time.list_item<QuoteSchema::Index::ASK_QTY>();
    auto temp = std::log(compute::sum(cur_bid_qty, 10) + 1) / std::log(compute::sum(cur_ask_qty, 10) + 1);
    value() = temp;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor