#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorBookSellQtySumQtyMaxPxMuity : public Factor<> {
  static const int LAG = 2;
  static const int SECOND = 30;
  TimeSlidingWindow<double> factor_value_list{SECOND};


public:
  FactorBookSellQtySumQtyMaxPxMuity() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_quote(LAG);
    if (window.len() < LAG) {
      return Status::OK();
    }

    auto before = window[0];
    auto now = window[-1];
    auto maxqtyindex_before = compute::imax(before.list_item<QuoteSchema::Index::ASK_QTY>(), 10);
    auto maxqtypx_before = before.list_item<QuoteSchema::Index::ASK_PRICE>()[maxqtyindex_before];
    const auto *askqty_now = now.list_item<QuoteSchema::Index::ASK_QTY>();
    auto now_time = now.item<QuoteSchema::Index::TRIGGER_TIME>();
    auto sum_askqty_now = compute::sum(askqty_now, 10);
    auto temp= sum_askqty_now*maxqtypx_before;
    factor_value_list.push(now_time, temp);
    value() = (temp - compute::mean(factor_value_list))/(compute::std(factor_value_list));
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor