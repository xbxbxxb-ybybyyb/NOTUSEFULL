#pragma once

#include "fmt/core.h"
#include "huatai/atsquant/factor/base_factor.h"
#include "huatai/atsquant/factor/compute.h"
#include "huatai/atsquant/factor/schema.h"
#include "huatai/atsquant/factor/util.h"
#include <arrow/status.h>

namespace huatai::atsquant::factor {

class FactorSecTradeAgg : public Factor<> {
  static const int lag1 = 120;

public:
  FactorSecTradeAgg() { type_ = __func__; }
  SlidingWindow<double> trade_buy_money_list{lag1};
  SlidingWindow<double> trade_sell_money_list{lag1};
  SlidingWindow<double> trade_buy_num_list{lag1};
  SlidingWindow<double> trade_sell_num_list{lag1};
  SlidingWindow<double> trade_buy_volume_list{lag1};
  SlidingWindow<double> trade_sell_volume_list{lag1};

  Status caculate() override {
    auto quotes = get_market_data().get_prev_n_quote(2);
    if (quotes.len() < 2) {
      return Status::OK();
    }
    auto seq_no = get_market_data().get_prev_n_quote(1).item<QuoteSchema::Index::TRIGGER_APPL_SEQ_NUM>();

    auto sample_1s_flag = quotes.slice(1, 1).item<QuoteSchema::Index::SAMPLE_1S_FLAG>();
    // todo: 1s采样计算计算太多，可能导致耗时太集中？
    if (sample_1s_flag) {
      auto last_time = quotes.slice(0, 1).item<QuoteSchema::Index::TRIGGER_TIME>();
      auto now_time = quotes.slice(1, 1).item<QuoteSchema::Index::TRIGGER_TIME>();
      auto secs_elapse = now_time / 1000 - last_time / 1000;
      for (int i = 0; i < secs_elapse - 1; i++) {
        // 若两条数据间隔超过1s, 补齐每秒的数据
        trade_buy_money_list.push(0.0);
        trade_sell_money_list.push(0.0);
        trade_buy_num_list.push(0.0);
        trade_sell_num_list.push(0.0);
        trade_buy_volume_list.push(0.0);
        trade_sell_volume_list.push(0.0);
      }
      // if (seq_no == 412285) {
      //   fmt::println("{}", (now_time / 1000) * 1000);
      // }

      auto current_trade = get_market_data().get_prev_n_trade(1);
      auto current_time = current_trade.item<TradeSchema::Index::TIMESTAMP>();
      auto raw_trades = get_market_data().get_prev_n_ms_trade(1000, (now_time / 1000) * 1000);

      auto trade_len = raw_trades.len();
      if (trade_len > 0) {
        // 上一秒的成交数据，不包括当前这一条
        auto trades = raw_trades.slice(0, trade_len);
        const auto *trade_qtys = trades.item_address<TradeSchema::Index::QUANTITY>();
        const auto *trade_moneys = trades.item_address<TradeSchema::Index::TURNOVER>();
        const auto *trade_sides = trades.item_address<TradeSchema::Index::SIDE>();

        // std::span<const double> trade_qtys_span{trade_qtys, (size_t)trade_len - 5};

        auto active_buy_money = 0.0;
        auto active_sell_money = 0.0;
        auto active_buy_num = 0.0;
        auto active_sell_num = 0.0;
        auto active_buy_volume = 0.0;
        auto active_sell_volume = 0.0;

        trades.for_each([&](const TableView<TradeSchema> &tv) {
          // if (seq_no == 412285) {
          //   int a = 0;
          //   std::cout << tv.item<TradeSchema::Index::QUANTITY>() << "," << tv.item<TradeSchema::Index::TIMESTAMP>()
          //             << std::endl;
          // }
          if (tv.item<TradeSchema::Index::SIDE>() == 1) {
            active_buy_money += tv.item<TradeSchema::Index::TURNOVER>();
            active_buy_volume += tv.item<TradeSchema::Index::QUANTITY>();
            active_buy_num++;
          } else if (tv.item<TradeSchema::Index::SIDE>() == 2) {
            active_sell_money += tv.item<TradeSchema::Index::TURNOVER>();
            active_sell_volume += tv.item<TradeSchema::Index::QUANTITY>();
            active_sell_num++;
          }
        });

        trade_buy_money_list.push(active_buy_money);
        trade_sell_money_list.push(active_sell_money);
        trade_buy_num_list.push(active_buy_num);
        trade_sell_num_list.push(active_sell_num);
        trade_buy_volume_list.push(active_buy_volume);
        trade_sell_volume_list.push(active_sell_volume);
      } else {
        trade_buy_money_list.push(0.0);
        trade_sell_money_list.push(0.0);
        trade_buy_num_list.push(0.0);
        trade_sell_num_list.push(0.0);
        trade_buy_volume_list.push(0.0);
        trade_sell_volume_list.push(0.0);
      }
    }
    return Status::OK();
  }
};

} // namespace huatai::atsquant::factor
