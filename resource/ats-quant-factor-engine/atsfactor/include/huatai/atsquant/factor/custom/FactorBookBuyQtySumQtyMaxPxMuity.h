#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorBookBuyQtySumQtyMaxPxMuity : public Factor<> {
  static const int LAG = 2;

public:
  FactorBookBuyQtySumQtyMaxPxMuity() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(LAG);
    if (window.len() < LAG) {
      return Status::OK();
    }

    auto before = window[0];
    auto now = window[-1];
    auto maxqtyindex_before = compute::imax(before.list_item<QuoteSchema::Index::BID_QTY>(), 10);
    auto maxqtypx_before = before.list_item<QuoteSchema::Index::BID_PRICE>()[maxqtyindex_before];
    const auto *bidqty_now = now.list_item<QuoteSchema::Index::BID_QTY>();
    auto sum_bidqty_now = compute::sum(bidqty_now, 10);
    value() = sum_bidqty_now*maxqtypx_before;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor