#pragma once

#include <arrow/api.h>

namespace huatai::atsquant::factor {

struct BaseSchema {
  enum class Index : int8_t {};
  using element_t = void;
  using arrow_array_t = void;
};

struct QuoteSchema : public BaseSchema {
  enum class Index : int8_t {
    LAST_PX = 0,
    HIGH_PX,
    LOW_PX,
    TOTAL_VOLUME,
    TOTAL_TURNOVER,
    TOTAL_ASK_QTY,
    TOTAL_BID_QTY,
    TRADES,
    TRIGGER_APPL_SEQ_NUM,
    TRIGGER_TIME,
    BID_QTY,
    BID_PRICE,
    BID_ORDER_NUMS,
    ASK_QTY,
    ASK_PRICE,
    ASK_ORDER_NUMS,
    AVG_BUY_PRICE,
    AVG_SELL_PRICE,
    SAMPLE_1S_FLAG,
  };

  template <Index I>
  using arrow_array_t = std::conditional_t<       //
      I == Index::LAST_PX ||                      //
          I == Index::HIGH_PX ||                  //
          I == Index::LOW_PX ||                   //
          I == Index::TOTAL_VOLUME ||             //
          I == Index::TOTAL_TURNOVER ||           //
          I == Index::TOTAL_ASK_QTY ||            //
          I == Index::TOTAL_BID_QTY ||            //
          I == Index::BID_QTY ||                  //
          I == Index::BID_PRICE ||                //
          I == Index::ASK_QTY ||                  //
          I == Index::ASK_PRICE ||                //
          I == Index::AVG_BUY_PRICE ||            //
          I == Index::AVG_SELL_PRICE,             //
      arrow::DoubleArray,                         //
      std::conditional_t<                         //
          I == Index::TRADES ||                   //
              I == Index::TRIGGER_APPL_SEQ_NUM || //
              I == Index::BID_ORDER_NUMS ||       //
              I == Index::ASK_ORDER_NUMS,         //
          arrow::UInt64Array,                     //
          std::conditional_t<                     //
              I == Index::TRIGGER_TIME,           //
              arrow::Int64Array,                  //
              std::conditional_t<                 //
                  I == Index::SAMPLE_1S_FLAG,     //
                  arrow::UInt8Array,              //
                  void>>>>;
  template <Index I> using element_t = arrow_array_t<I>::value_type;

  static std::shared_ptr<arrow::Schema> get() {
    static std::shared_ptr<arrow::Schema> schema;
    if (schema != nullptr) {
      return schema;
    }

    schema = arrow::schema({
        arrow::field("last_px", arrow::float64()),                          // 最新价
        arrow::field("high_px", arrow::float64()),                          // 最高价
        arrow::field("low_px", arrow::float64()),                           // 最低价
        arrow::field("total_volume", arrow::float64()),                     //  成交总量
        arrow::field("total_turnover", arrow::float64()),                   //  成交总金额
        arrow::field("total_ask_qty", arrow::float64()),                    //  卖方盘口总委托量
        arrow::field("total_bid_qty", arrow::float64()),                    //  买方盘口总委托量
        arrow::field("trades", arrow::uint64()),                            //  总成交笔数
        arrow::field("trigger_appl_seq_num", arrow::uint64()),              // 触发合成序号
        arrow::field("trigger_time", arrow::int64()),                       // 行情时间
        arrow::field("bid_qty", arrow::large_list(arrow::float64())),       // 买方档位--数量
        arrow::field("bid_price", arrow::large_list(arrow::float64())),     // 买方档位--价格
        arrow::field("bid_order_nums", arrow::large_list(arrow::uint64())), // 买方档位--笔数
        arrow::field("ask_qty", arrow::large_list(arrow::float64())),       // 卖方档位--数量
        arrow::field("ask_price", arrow::large_list(arrow::float64())),     // 卖方档位--价格
        arrow::field("ask_order_nums", arrow::large_list(arrow::uint64())), // 卖方档位--笔数
        arrow::field("avg_buy_price", arrow::float64()),                    // 买方平均价
        arrow::field("avg_sell_price", arrow::float64()),                   // 卖方平均价
        arrow::field("sample_1s_flag", arrow::uint8()),                     // 定时采样标志
    });

    return schema;
  }
};

struct TradeSchema : public BaseSchema {
  enum class Index : int8_t {
    TIMESTAMP = 0,
    SIDE,
    PRICE,
    QUANTITY,
    TURNOVER,
    APPL_SEQ_NUM,
    CHANNEL_NO,
  };

  template <Index I>
  using arrow_array_t = std::conditional_t< //
      I == Index::PRICE ||                  //
          I == Index::QUANTITY ||           //
          I == Index::TURNOVER,             //
      arrow::DoubleArray,                   //
      std::conditional_t<                   //
          I == Index::TIMESTAMP ||          //
              I == Index::APPL_SEQ_NUM ||   //
              I == Index::CHANNEL_NO,       //
          arrow::Int64Array,                //
          std::conditional_t<               //
              I == Index::SIDE,             //
              arrow::Int8Array,             //
              void>>>;
  template <Index I> using element_t = arrow_array_t<I>::value_type;

  static std::shared_ptr<arrow::Schema> get() {
    static std::shared_ptr<arrow::Schema> schema;
    if (schema != nullptr) {
      return schema;
    }

    schema = arrow::schema({
        arrow::field("timestamp", arrow::int64()),    // 交易所时间
        arrow::field("side", arrow::int8()),          // 成交方向
        arrow::field("price", arrow::float64()),      // 成交价格
        arrow::field("quantity", arrow::float64()),   // 成交数量
        arrow::field("turnover", arrow::float64()),   // 成交金额
        arrow::field("appl_seq_num", arrow::int64()), // 交易所原始消息记录号
        arrow::field("channel_no", arrow::int64()),   // 交易所原始频道代码
    });

    return schema;
  }
};

struct OrderSchema : public BaseSchema {
  enum class Index {
    TIMESTAMP = 0,
    SIDE,
    PRICE,
    QUANTITY,
    APPL_SEQ_NUM,
    CHANNEL_NO,
  };

  template <Index I>
  using arrow_array_t = std::conditional_t< //
      I == Index::PRICE ||                  //
          I == Index::QUANTITY,             //
      arrow::DoubleArray,                   //
      std::conditional_t<                   //
          I == Index::TIMESTAMP ||          //
              I == Index::APPL_SEQ_NUM ||   //
              I == Index::CHANNEL_NO,       //
          arrow::Int64Array,                //
          std::conditional_t<               //
              I == Index::SIDE,             //
              arrow::Int8Array,             //
              void>>>;
  template <Index I> using element_t = arrow_array_t<I>::value_type;

  static std::shared_ptr<arrow::Schema> get() {
    static std::shared_ptr<arrow::Schema> schema;
    if (schema != nullptr) {
      return schema;
    }

    schema = arrow::schema({
        arrow::field("timestamp", arrow::int64()),    // 交易所时间
        arrow::field("side", arrow::int8()),          // 买卖方向
        arrow::field("price", arrow::float64()),      // 委托价格
        arrow::field("quantity", arrow::float64()),   // 委托数量
        arrow::field("appl_seq_num", arrow::int64()), // 交易所原始消息记录号
        arrow::field("channel_no", arrow::int64()),   // 交易所原始频道代码
    });

    return schema;
  }
};

struct CancelSchema : public BaseSchema {
  enum class Index {
    TIMESTAMP = 0,
    SIDE,
    PRICE,
    QUANTITY,
    APPL_SEQ_NUM,
    CHANNEL_NO,
  };

  template <Index I>
  using arrow_array_t = std::conditional_t< //
      I == Index::PRICE ||                  //
          I == Index::QUANTITY,             //
      arrow::DoubleArray,                   //
      std::conditional_t<                   //
          I == Index::TIMESTAMP ||          //
              I == Index::APPL_SEQ_NUM ||   //
              I == Index::CHANNEL_NO,       //
          arrow::Int64Array,                //
          std::conditional_t<               //
              I == Index::SIDE,             //
              arrow::Int8Array,             //
              void>>>;
  template <Index I> using element_t = arrow_array_t<I>::value_type;

  static std::shared_ptr<arrow::Schema> get() {
    static std::shared_ptr<arrow::Schema> schema;
    if (schema != nullptr) {
      return schema;
    }

    schema = arrow::schema({
        arrow::field("timestamp", arrow::int64()),    // 交易所时间
        arrow::field("side", arrow::int8()),          // 买卖方向
        arrow::field("price", arrow::float64()),      // 委托价格
        arrow::field("quantity", arrow::float64()),   // 委托数量
        arrow::field("appl_seq_num", arrow::int64()), // 交易所原始消息记录号
        arrow::field("channel_no", arrow::int64()),   // 交易所原始频道代码
    });

    return schema;
  }
};

} // namespace huatai::atsquant::factor