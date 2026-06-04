#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorBookSellMaxQtyPxPxRatio : public Factor<> {
  static const int SECONDS = 10;

public:
  FactorBookSellMaxQtyPxPxRatio() { type_ = __func__; }

  Status caculate() override {

    auto window = get_market_data().get_prev_n_quote(1);
    const auto *sellqty_now = window.list_item<QuoteSchema::Index::ASK_QTY>();
    const auto *sellprice_now = window.list_item<QuoteSchema::Index::ASK_PRICE>();
    auto max_index_sellqty_now = compute::imax(sellqty_now, 10);
    auto max_qty_price = sellprice_now[max_index_sellqty_now];
    value() =  max_qty_price/window.item<QuoteSchema::Index::LAST_PX>();
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor