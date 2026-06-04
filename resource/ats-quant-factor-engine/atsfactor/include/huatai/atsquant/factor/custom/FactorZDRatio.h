#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include <cmath> // 或者 #include <math.h>

namespace huatai::atsquant::factor {

class FactorZDRatio : public Factor<> {

public:
  FactorZDRatio() { type_ = __func__; }

  Status caculate() override {
    static int index = 0;
    index++;

    auto now_time = get_market_data().get_prev_n_quote(1);

    const auto *cur_sell_price = now_time.list_item<QuoteSchema::Index::ASK_PRICE>();
    const auto *cur_buy_price = now_time.list_item<QuoteSchema::Index::BID_PRICE>();
    const auto *cur_sell_qty = now_time.list_item<QuoteSchema::Index::ASK_QTY>();
    const auto *cur_buy_qty = now_time.list_item<QuoteSchema::Index::BID_QTY>();

    auto buy_amount = compute::mul_sum(cur_buy_price, cur_buy_qty, 10);
    auto sell_amount = compute::mul_sum(cur_sell_price, cur_sell_qty, 10);

    auto temp = (buy_amount - sell_amount) / (buy_amount + sell_amount);
    value() = temp;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor