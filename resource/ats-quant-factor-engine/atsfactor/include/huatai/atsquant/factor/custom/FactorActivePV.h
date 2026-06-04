#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

using compute::filter;
using compute::sum;
using huatai::atsquant::common::OrderSide;

struct FactorActivePVParam {
  int64_t interval = 8;
  double price_spread = 0.05;
  int64_t active_volume = 3000;
};
NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE_WITH_DEFAULT(FactorActivePVParam, interval, price_spread, active_volume)

class FactorActivePV : public Factor<FactorActivePVParam> {
public:
  FactorActivePV() { type_ = __func__; }

  Status caculate() override {
    auto tick_data_index = get_market_data().get_prev_n_quote(1).item<QuoteSchema::Index::TRIGGER_APPL_SEQ_NUM>();
    auto trade_index = get_market_data().get_prev_n_trade(1).item<TradeSchema::Index::APPL_SEQ_NUM>();

    auto row_tick = get_market_data().get_prev_n_quote(1);
    auto row_trade = get_market_data().get_prev_n_sec_trade(param().interval);
    value() = 0;

    if (get_market_data().get_num_quote() < 2) {
      return Status::OK();
    }

    if (tick_data_index != trade_index) {
      return Status::OK();
    }

    auto current_tick_ask_p0 = row_tick.list_item<QuoteSchema::Index::ASK_PRICE>()[0];
    auto current_tick_bid_p0 = row_tick.list_item<QuoteSchema::Index::BID_PRICE>()[0];

    if (current_tick_ask_p0 - current_tick_bid_p0 <= param().price_spread) {
      return Status::OK();
    }

    const auto *trade_side_list = row_trade.item_address<TradeSchema::Index::SIDE>();
    const auto *trade_price_list = row_trade.item_address<TradeSchema::Index::PRICE>();
    auto active_buy_volume =
        sum(filter(row_trade.item_address<TradeSchema::Index::QUANTITY>(), row_trade.len(), [&](auto i, const auto &e) {
          return trade_side_list[i] == (int8_t)OrderSide::BUY && trade_price_list[i] >= current_tick_bid_p0 * 1.0008;
        }));
    auto active_sell_volume =
        sum(filter(row_trade.item_address<TradeSchema::Index::QUANTITY>(), row_trade.len(), [&](auto i, const auto &e) {
          return trade_side_list[i] == (int8_t)OrderSide::SELL && trade_price_list[i] <= current_tick_ask_p0 * 0.9992;
        }));

    value() = active_buy_volume > active_sell_volume ? 1 : -1;
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor