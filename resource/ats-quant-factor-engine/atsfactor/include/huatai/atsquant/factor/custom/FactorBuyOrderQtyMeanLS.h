#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorBuyOrderQtyMeanLS : public Factor<> {
  static const int SHORT_SECONDS = 60;
  static const int LONG_SECONDS = 300;

  TimeSlidingWindow<double> long_list{LONG_SECONDS};
  TimeSlidingWindow<double> short_list{SHORT_SECONDS};

public:
  FactorBuyOrderQtyMeanLS() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(1);
    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();

    const auto *buy_num_orders = window.list_item<QuoteSchema::Index::BID_ORDER_NUMS>();
    auto buy_num_orders_sum = compute::sum(buy_num_orders, 10);
    long_list.push(now_time,buy_num_orders_sum);
    short_list.push(now_time,buy_num_orders_sum);
    auto avg_short_list = compute::mean(short_list);
    auto avg_long_list = compute::mean(long_list);
    value() = avg_short_list / avg_long_list;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor