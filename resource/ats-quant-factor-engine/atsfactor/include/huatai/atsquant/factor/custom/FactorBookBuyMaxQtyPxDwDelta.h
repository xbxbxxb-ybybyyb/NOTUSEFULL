#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorBookBuyMaxQtyPxDwDelta : public Factor<> {

public:
  FactorBookBuyMaxQtyPxDwDelta() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(2);
    if (window.len() < 2) {
      return Status::OK();
    }

    auto before = window[0];
    auto now = window[-1];
    auto maxqtyindex_before = compute::imax(before.list_item<QuoteSchema::Index::BID_QTY>(), 10);
    auto maxqtypx_before = before.list_item<QuoteSchema::Index::BID_PRICE>()[maxqtyindex_before];
    const auto *bid_price_now = now.list_item<QuoteSchema::Index::BID_PRICE>();
    for (int i = 0; i < 10; i++) {
      if (bid_price_now[i] == maxqtypx_before) {
        value() = i - maxqtyindex_before;
        return Status::OK();
      }
    }

    value() = 0;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor