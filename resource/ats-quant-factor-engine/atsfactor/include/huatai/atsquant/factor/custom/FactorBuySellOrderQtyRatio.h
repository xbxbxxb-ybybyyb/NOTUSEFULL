#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorBuySellOrderQtyRatio : public Factor<> {

public:
  FactorBuySellOrderQtyRatio() { type_ = __func__; }

  Status caculate() override {
    auto prev_value = value();
    auto window = get_market_data().get_prev_n_quote(1);

    const auto *buy_num_orders = window.list_item<QuoteSchema::Index::BID_ORDER_NUMS>();
    const auto *sell_num_orders = window.list_item<QuoteSchema::Index::ASK_ORDER_NUMS>();

    auto buy_num_orders_sum = compute::sum(buy_num_orders, 10);
    auto sell_num_orders_sum = compute::sum(sell_num_orders, 10);
    auto ratio = sell_num_orders_sum == 0 ? 0.0 : (double)buy_num_orders_sum / sell_num_orders_sum;
    auto log_ratio = ratio == 0 ? 0.0 : std::log(ratio);
    value() = log_ratio;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor