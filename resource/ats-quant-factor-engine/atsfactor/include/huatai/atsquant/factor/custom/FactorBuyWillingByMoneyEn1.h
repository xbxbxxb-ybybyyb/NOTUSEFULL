#pragma once

#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"

namespace huatai::atsquant::factor {

class FactorBuyWillingByMoneyEn1 : public Factor<> {
public:
  TimeSlidingWindow<double> buy_amount_queue{1};  // 1s内的总成交量
  TimeSlidingWindow<double> sell_amount_queue{1}; //

  FactorBuyWillingByMoneyEn1() { type_ = __func__; }
  Status caculate() override {
    auto last_order = get_market_data().get_prev_n_order(1);
    auto last_ticks = get_market_data().get_prev_n_quote(2);
    auto last_tick = last_ticks[0];
    auto current_tick = last_ticks[1];
    auto order_seq_no = last_order.item<OrderSchema::Index::APPL_SEQ_NUM>();
    auto tick_seq_no = last_tick.item<QuoteSchema::Index::TRIGGER_APPL_SEQ_NUM>();
    value() = 0.5;

    if (order_seq_no == tick_seq_no) {
      auto last_qty = last_tick.item<QuoteSchema::Index::TOTAL_TURNOVER>();
      auto current_qty = current_tick.item<QuoteSchema::Index::TOTAL_TURNOVER>();
      auto time = current_tick.item<QuoteSchema::Index::TRIGGER_TIME>();
      auto side = last_order.item<OrderSchema::Index::SIDE>();

      if (current_qty > last_qty) {
        // 有成交时
        // todo: 少了buymoney和sell_money
        if (side == 1) { // Side::BID) {
          buy_amount_queue.push(time, current_qty - last_qty);
        } else {
          sell_amount_queue.push(time, current_qty - last_qty);
        }
        auto buy_amt = compute::sum(buy_amount_queue);
        auto sell_amt = compute::sum(sell_amount_queue);
        value() = buy_amt / (buy_amt + sell_amt);
      }
    }
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor
