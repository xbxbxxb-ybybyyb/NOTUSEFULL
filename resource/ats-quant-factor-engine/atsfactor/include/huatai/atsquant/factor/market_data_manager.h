#pragma once

#include <arrow/api.h>
#include <string>

#include "huatai/atsquant/factor/common.h"
#include "huatai/atsquant/factor/schema.h"
#include "huatai/atsquant/factor/util.h"

namespace huatai::atsquant::factor {
using namespace huatai::atsquant::common;
using fmt::format;
using json = nlohmann::json;

struct FACTOR_EXPORT MarketDataManagerOption {
  enum class MarketDataManagerType {
    DEFAULT,
    PARQUET_FILE,
    ARROW_TABLE,
  };
  int64_t quote_rows = 1000000;
  int64_t trade_rows = 500000;
  int64_t order_rows = 500000;
  int64_t cancel_rows = 500000;
  MarketDataManagerType type = MarketDataManagerType::DEFAULT;
};
NLOHMANN_JSON_SERIALIZE_ENUM(MarketDataManagerOption::MarketDataManagerType,
                             {
                                 {MarketDataManagerOption::MarketDataManagerType::DEFAULT, "DEFAULT"},
                                 {MarketDataManagerOption::MarketDataManagerType::PARQUET_FILE, "PARQUET_FILE"},
                                 {MarketDataManagerOption::MarketDataManagerType::ARROW_TABLE, "ARROW_TABLE"},
                             })
NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(MarketDataManagerOption, quote_rows, trade_rows, order_rows, cancel_rows, type)

class FACTOR_EXPORT SingleMarketDataManager {
public:
  explicit SingleMarketDataManager(const MarketDataManagerOption &option);

  int64_t get_mdtime() const;

  Status on_quote(const QuoteIndicator &quote_indicator);

  int64_t get_num_quote() const { return num_quote_; }

  int64_t get_num_trade() const { return num_trade_; }

  int64_t get_num_order() const { return num_order_; }

  int64_t get_num_cancel() const { return num_cancel_; }

  std::shared_ptr<arrow::RecordBatch> get_quote() const { return quote_; };

  std::shared_ptr<arrow::RecordBatch> get_trade() const { return trade_; };

  std::shared_ptr<arrow::RecordBatch> get_order() const { return order_; };

  std::shared_ptr<arrow::RecordBatch> get_cancel() const { return cancel_; };

  int64_t get_prev_n(int64_t rb_num_rows, int64_t n) const { return std::max(rb_num_rows - n, (int64_t)0); }

  int64_t search_marketdata_ms(const int64_t *first, const int64_t *last, int64_t ts) const {
    if (first >= last) {
      return 0;
    }

    const auto *upper = std::upper_bound(first, last, ts);
    return upper - first;
  }

  template <typename SchemaType, int timestamp_index = (int)SchemaType::Index::TIMESTAMP>
  TableView<SchemaType> get_prev_n_ms(const std::shared_ptr<arrow::RecordBatch> &rb, int64_t rb_num_rows, int64_t n,
                                      int64_t end) const {
    const auto *column_time = std::static_pointer_cast<arrow::Int64Array>(rb->column(timestamp_index))->raw_values();
    auto row_index = search_marketdata_ms(column_time, column_time + rb_num_rows, end - n);
    auto end_index = search_marketdata_ms(column_time + row_index, column_time + rb_num_rows, end) + row_index;
    return {
        .rb = rb,
        .row_index = row_index,
        .end_index = end_index,
    };
  }

  template <typename SchemaType, int timestamp_index = (int)SchemaType::Index::TIMESTAMP>
  TableView<SchemaType> get_prev_n_ms(const std::shared_ptr<arrow::RecordBatch> &rb, int64_t rb_num_rows,
                                      int64_t n) const {
    if (rb_num_rows < 1) {
      return {
          .rb = rb,
          .row_index = 0,
          .end_index = 0,
      };
    }

    const auto *column_time = std::static_pointer_cast<arrow::Int64Array>(rb->column(timestamp_index))->raw_values();
    return {
        .rb = rb,
        .row_index = search_marketdata_ms(column_time, column_time + rb_num_rows, column_time[rb_num_rows - 1] - n),
        .end_index = rb_num_rows,
    };
  }

  TableView<QuoteSchema> get_prev_n_quote(int64_t n) const {
    return {quote_, get_prev_n(get_num_quote(), n), get_num_quote()};
  }

  TableView<TradeSchema> get_prev_n_trade(int64_t n) const {
    return {trade_, get_prev_n(get_num_trade(), n), get_num_trade()};
  }

  TableView<OrderSchema> get_prev_n_order(int64_t n) const {
    return {order_, get_prev_n(get_num_order(), n), get_num_order()};
  }

  TableView<CancelSchema> get_prev_n_cancel(int64_t n) const {
    return {cancel_, get_prev_n(get_num_cancel(), n), get_num_cancel()};
  }

  TableView<QuoteSchema> get_prev_n_sec_quote(int64_t n_seconds) const {
    return get_prev_n_ms<QuoteSchema, (int)QuoteSchema::Index::TRIGGER_TIME>(quote_, get_num_quote(), n_seconds * 1000);
  }

  TableView<TradeSchema> get_prev_n_sec_trade(int64_t n_seconds) const {
    return get_prev_n_ms<TradeSchema>(trade_, get_num_trade(), n_seconds * 1000);
  }

  TableView<OrderSchema> get_prev_n_sec_order(int64_t n_seconds) const {
    return get_prev_n_ms<OrderSchema>(order_, get_num_order(), n_seconds * 1000);
  }

  TableView<CancelSchema> get_prev_n_sec_cancel(int64_t n_seconds) const {
    return get_prev_n_ms<CancelSchema>(cancel_, get_num_cancel(), n_seconds * 1000);
  }

  TableView<QuoteSchema> get_prev_n_ms_quote(int64_t n_ms) const {
    return get_prev_n_ms<QuoteSchema, (int)QuoteSchema::Index::TRIGGER_TIME>(quote_, get_num_quote(), n_ms);
  }

  TableView<TradeSchema> get_prev_n_ms_trade(int64_t n_ms) const {
    return get_prev_n_ms<TradeSchema>(trade_, get_num_trade(), n_ms);
  }

  TableView<OrderSchema> get_prev_n_ms_order(int64_t n_ms) const {
    return get_prev_n_ms<OrderSchema>(order_, get_num_order(), n_ms);
  }

  TableView<CancelSchema> get_prev_n_ms_cancel(int64_t n_ms) const {
    return get_prev_n_ms<CancelSchema>(cancel_, get_num_cancel(), n_ms);
  }

  TableView<QuoteSchema> get_prev_n_ms_quote(int64_t n_ms, int64_t end_ms) const {
    return get_prev_n_ms<QuoteSchema, (int)QuoteSchema::Index::TRIGGER_TIME>(quote_, get_num_quote(), n_ms, end_ms);
  }

  TableView<TradeSchema> get_prev_n_ms_trade(int64_t n_ms, int64_t end_ms) const {
    return get_prev_n_ms<TradeSchema>(trade_, get_num_trade(), n_ms, end_ms);
  }

  TableView<OrderSchema> get_prev_n_ms_order(int64_t n_ms, int64_t end_ms) const {
    return get_prev_n_ms<OrderSchema>(order_, get_num_order(), n_ms, end_ms);
  }

  TableView<CancelSchema> get_prev_n_ms_cancel(int64_t n_ms, int64_t end_ms) const {
    return get_prev_n_ms<CancelSchema>(cancel_, get_num_cancel(), n_ms, end_ms);
  }

  std::string to_string() const;

  NLOHMANN_DEFINE_TYPE_INTRUSIVE(SingleMarketDataManager, num_quote_, num_trade_, num_order_, num_cancel_)

protected:
  Status on_trade(const QuoteIndicator &quote_indicator, int64_t trigger_time);
  Status on_order(const QuoteIndicator &quote_indicator, int64_t trigger_time);
  Status on_cancel(const QuoteIndicator &quote_indicator, int64_t trigger_time);

  std::shared_ptr<arrow::RecordBatch> quote_;
  std::shared_ptr<arrow::RecordBatch> trade_;
  std::shared_ptr<arrow::RecordBatch> order_;
  std::shared_ptr<arrow::RecordBatch> cancel_;

  int64_t num_quote_ = 0;
  int64_t num_trade_ = 0;
  int64_t num_order_ = 0;
  int64_t num_cancel_ = 0;

  friend class MarketDataManager;
  friend class ArrowTableMarketDataManager;
};

class FACTOR_EXPORT MarketDataManager {
public:
  static std::shared_ptr<MarketDataManager> Instance(const MarketDataManagerOption &option);

  explicit MarketDataManager(const MarketDataManagerOption &option) : option_(option) {}

  virtual ~MarketDataManager() {}

  Status on_quote(const QuoteIndicator &quote);

  size_t size() { return symbol_mdm_map_.size(); }

  std::shared_ptr<SingleMarketDataManager> default_manager() { return default_mdm_; };

  std::shared_ptr<SingleMarketDataManager> get_manager(const std::string &symbol) {
    auto it = symbol_mdm_map_.find(symbol);
    return it == symbol_mdm_map_.end() ? nullptr : it->second;
  }

protected:
  void add_symbol(const std::string &symbol);

  std::map<std::string, std::shared_ptr<SingleMarketDataManager>> symbol_mdm_map_;
  std::shared_ptr<SingleMarketDataManager> default_mdm_;
  MarketDataManagerOption option_;

  friend class FactorManager;
};

class FACTOR_EXPORT ArrowTableMarketDataManager : public MarketDataManager {
public:
  ArrowTableMarketDataManager(const MarketDataManagerOption &option, std::shared_ptr<arrow::Table> table = nullptr)
      : MarketDataManager(option) {
    auto st = set_table(table);
    if (!st.ok()) {
      throw std::runtime_error(st.ToString());
    }
  }

  Status set_table(std::shared_ptr<arrow::Table> table);

  int64_t num_rows() const {
    if (data_record_batch_ == nullptr) {
      return 0;
    }
    return data_record_batch_->num_rows();
  }

  void set_num_quote(int64_t n) {
    for (auto &[_, mdm] : symbol_mdm_map_) {
      mdm->num_quote_ = n;
    }
  }

  void set_num_trade(int64_t n) {
    for (auto &[_, mdm] : symbol_mdm_map_) {
      mdm->num_trade_ = n;
    }
  }

  void set_num_order(int64_t n) {
    for (auto &[_, mdm] : symbol_mdm_map_) {
      mdm->num_order_ = n;
    }
  }

  void set_num_cancel(int64_t n) {
    for (auto &[_, mdm] : symbol_mdm_map_) {
      mdm->num_cancel_ = n;
    }
  }

  void set_row_index(int64_t n) { row_index_ = n; }

  void reset() {
    set_num_quote(0);
    set_num_trade(0);
    set_num_order(0);
    set_num_cancel(0);
    set_row_index(0);
  }

  std::string to_string() const;

  Result<int64_t> next();

  bool is_end() { return row_index_ >= num_rows(); }

protected:
  std::optional<QuoteIndicatorOrderCancel> next_row();

  std::shared_ptr<arrow::RecordBatch> data_record_batch_;
  int64_t row_index_ = 0;
};

class FACTOR_EXPORT ParquetFileMarketDataManager : public ArrowTableMarketDataManager {
public:
  ParquetFileMarketDataManager(const MarketDataManagerOption &option, const std::string &path = "")
      : ArrowTableMarketDataManager(option), path_(path) {
    auto st = load();
    if (!st.ok()) {
      throw std::runtime_error(st.ToString());
    }
  }

  Status set_path(const std::string &path);

  std::string to_string() const;

protected:
  Status load();

  std::string path_;
};

} // namespace huatai::atsquant::factor