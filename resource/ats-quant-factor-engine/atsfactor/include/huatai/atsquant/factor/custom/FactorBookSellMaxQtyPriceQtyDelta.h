#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorBookSellMaxQtyPriceQtyDelta : public Factor<> {
  static const int SECONDS = 10;

public:
  FactorBookSellMaxQtyPriceQtyDelta() { type_ = __func__; }

  Status caculate() override {
    static auto index = 0;
    index++;

    auto window = get_market_data().get_prev_n_quote(2);
    if (window.len() < 2) {
      return Status::OK();
    }

    auto now = window[-1];
    auto pre = window[0];
    const auto *sellqty_pre = pre.list_item<QuoteSchema::Index::ASK_QTY>();
    const auto *sellqty_now = now.list_item<QuoteSchema::Index::ASK_QTY>();

    const auto *sellprice_now = now.list_item<QuoteSchema::Index::ASK_PRICE>();
    auto max_index_sellqty_pre = compute::imax(sellqty_pre, 10);
    auto max_sellprice_pre = pre.list_item<QuoteSchema::Index::ASK_PRICE>()[max_index_sellqty_pre];

    for (int i = 0; i < 10; i++) {
      if (sellprice_now[i] == max_sellprice_pre) {
        value() = sellqty_now[i] - compute::max(sellqty_pre, 10);
        return Status::OK();
      }
    }
    value() = (-1) * (compute::max(sellqty_pre, 10));
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor