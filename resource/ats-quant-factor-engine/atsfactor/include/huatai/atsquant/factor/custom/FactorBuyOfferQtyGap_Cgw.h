#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include "cmath"
namespace huatai::atsquant::factor {

struct FactorBuyOfferQtyGap_CgwParam {
  int LAG = 30;
};

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE_WITH_DEFAULT(FactorBuyOfferQtyGap_CgwParam, LAG)
class FactorBuyOfferQtyGap_Cgw : public Factor<FactorBuyOfferQtyGap_CgwParam> {
public:
  FactorBuyOfferQtyGap_Cgw() { type_ = __func__; }
  static const int LAG = 21;
  SlidingWindow<double> bid_vol_qty_queue{LAG};
  SlidingWindow<double> ask_vol_qty_queue{LAG};
  Status caculate() override {
    auto current_row_tick = get_market_data().get_prev_n_quote(1);

    const auto *current_tick_ask_v = current_row_tick.list_item<QuoteSchema::Index::ASK_QTY>();
    const auto *current_tick_bid_v = current_row_tick.list_item<QuoteSchema::Index::BID_QTY>();
    auto row_avg_buy_qty = compute::sum(current_tick_bid_v, 10) / 10;
    auto row_avg_sell_qty = compute::sum(current_tick_ask_v, 10) / 10;
    bid_vol_qty_queue.push(row_avg_buy_qty);
    ask_vol_qty_queue.push(row_avg_sell_qty);
    if (bid_vol_qty_queue.size()<21){
      value() = 0;
      return Status::OK();
    }

    auto bid_vol_qty = bid_vol_qty_queue.back() - bid_vol_qty_queue.front();
    auto ask_vol_qty = ask_vol_qty_queue.back() - ask_vol_qty_queue.front();

    if (bid_vol_qty + ask_vol_qty > 0.1) {
      value() = (bid_vol_qty - ask_vol_qty) / (bid_vol_qty + ask_vol_qty);
      if (std::abs(value()) >= 10) {
        value() = 0;
      }
    }
    else{
      value() = 0;
    }
    return Status::OK();
  }
};
} // namespace huatai::atsquant::factor