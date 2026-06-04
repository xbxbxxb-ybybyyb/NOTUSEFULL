#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include "huatai/atsquant/factor/schema.h"
#include "huatai/atsquant/factor/util.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorSecBuySellNum : public Factor<> {
  static const int lag1 = 120;

public:
  FactorSecBuySellNum() { type_ = __func__; }
  SlidingWindow<int> num_bids_sec_list{lag1};
  SlidingWindow<int> num_asks_sec_list{lag1};

  Status caculate() override {
    auto current_quote = get_market_data().get_prev_n_quote(1);
    auto sample_1s_flag = current_quote.item<QuoteSchema::Index::SAMPLE_1S_FLAG>();
    if (sample_1s_flag) {
      auto current_order = get_market_data().get_prev_n_order(1);
      auto order_time = current_order.item<OrderSchema::Index::TIMESTAMP>();
      auto orders = get_market_data().get_prev_n_sec_order(1);
      auto num_bids = 0;
      auto num_asks = 0;
      orders.for_each([&num_bids, &num_asks](const TableView<OrderSchema> tv) {
        if (tv.item<OrderSchema::Index::SIDE>() == 1) {
          num_bids++;
        } else if (tv.item<OrderSchema::Index::SIDE>() == 2) {
          num_asks++;
        }
      });
      // for (auto &i = std::remove_const_t<int64_t &>(orders.row_index); i < orders.end_index - 1; i++) {
      //   if (orders[i].item<OrderSchema::Index::SIDE>() == 1) {
      //     num_bids += 1;
      //   } else if (orders[i].item<OrderSchema::Index::SIDE>() == 2) {
      //     num_asks += 1;
      //   }
      // }
      num_bids_sec_list.push(num_bids);
      num_asks_sec_list.push(num_asks);
    }
    value() = 0;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor