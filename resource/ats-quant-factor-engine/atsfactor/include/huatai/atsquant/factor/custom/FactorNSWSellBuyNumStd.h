#pragma once

#include "arrow/status.h"
#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorNSWSellBuyNumStd : public Factor<> {
  static const int LAG = 20;
  SlidingWindow<uint64_t> sum_buy_num_queue{LAG};
  SlidingWindow<uint64_t> sum_sell_num_queue{LAG};

public:
  FactorNSWSellBuyNumStd() { type_ = __func__; }

  Status caculate() override {
    static int index = 0;
    index++;
    auto table = get_market_data().get_prev_n_quote(1);
    const auto *bid_order_nums = table.list_item<QuoteSchema::Index::BID_ORDER_NUMS>();
    const auto *ask_order_nums = table.list_item<QuoteSchema::Index::ASK_ORDER_NUMS>();
    auto sum_buy_num = compute::sum(bid_order_nums, 10);
    sum_buy_num_queue.push(sum_buy_num);
    auto sum_sell_num = compute::sum(ask_order_nums, 10);
    sum_sell_num_queue.push(sum_sell_num);
    if (sum_sell_num_queue.size() < LAG) {
      value() = 0;
      return Status::OK();
    }
    auto mstd_sum_buy_num = compute::std(sum_buy_num_queue);
    auto mstd_sum_sell_num = compute::std(sum_sell_num_queue);

    value() = mstd_sum_sell_num > 1e-6 ? mstd_sum_buy_num : 0;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor