#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorBuyOrderQtyStd_n_tick10 : public Factor<> {
  static const int SECONDS = 30;
  TimeSlidingWindow<double> orders_list{SECONDS};

public:
  FactorBuyOrderQtyStd_n_tick10() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(1);
    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();
    const auto *buy_num_orders = window.list_item<QuoteSchema::Index::BID_ORDER_NUMS>();
    auto buy_num_orders_sum = compute::sum(buy_num_orders, 10);
    orders_list.push(now_time, buy_num_orders_sum);
    auto orders_std = compute::std(orders_list);
    value() = orders_std;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor