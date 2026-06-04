#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorBookBuySell15QtyRatiomaxsize : public Factor<> {
  static const int SECONDS = 300;
  TimeSlidingWindow<double> buy_sell_qty_ratio_list{SECONDS};

public:
  FactorBookBuySell15QtyRatiomaxsize() { type_ = __func__; }

  Status caculate() override {
    auto window = get_market_data().get_prev_n_sec_quote(1);
    auto now_time = window.item<QuoteSchema::Index::TRIGGER_TIME>();

    const auto *buyqty_part_now = window.list_item<QuoteSchema::Index::BID_QTY>();
    const auto *sellqty_part_now = window.list_item<QuoteSchema::Index::ASK_QTY>();
    auto sum_buyqty = compute::sum(buyqty_part_now, 5);
    auto sum_sellqty = compute::sum(sellqty_part_now, 5);
    auto buy_sell_qty_ratio = sum_sellqty == 0.0 ? 0.0 : sum_buyqty / sum_sellqty;
    buy_sell_qty_ratio_list.push(now_time, buy_sell_qty_ratio);
    auto max_index = compute::imax(buy_sell_qty_ratio_list);
    auto min_index = compute::imin(buy_sell_qty_ratio_list);
    value() = max_index > min_index ? max_index - min_index : min_index - max_index;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor