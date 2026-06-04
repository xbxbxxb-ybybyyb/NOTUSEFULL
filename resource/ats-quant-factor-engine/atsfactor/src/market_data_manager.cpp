#include <arrow/io/api.h>
#include <filesystem>
#include <fmt/format.h>
#include <parquet/arrow/reader.h>

#include "huatai/atsquant/factor/market_data_manager.h"
#include "huatai/atsquant/factor/schema.h"
#include "huatai/atsquant/factor/util.h"

namespace huatai::atsquant::factor {
using fmt::format;
using huatai::atsquant::common::QuoteIndicator;
namespace fs = std::filesystem;
using json = nlohmann::json;

SingleMarketDataManager::SingleMarketDataManager(const MarketDataManagerOption &option) {
  auto r = make_zero_filled_record_batch(QuoteSchema::get(), option.quote_rows, 10);
  if (!r.ok()) {
    throw std::runtime_error(r.status().ToString());
  }
  quote_ = r.ValueUnsafe();

  r = make_zero_filled_record_batch(TradeSchema::get(), option.trade_rows, 10);
  if (!r.ok()) {
    throw std::runtime_error(r.status().ToString());
  }
  trade_ = r.ValueUnsafe();

  r = make_zero_filled_record_batch(OrderSchema::get(), option.order_rows, 10);
  if (!r.ok()) {
    throw std::runtime_error(r.status().ToString());
  }
  order_ = r.ValueUnsafe();

  r = make_zero_filled_record_batch(CancelSchema::get(), option.cancel_rows, 10);
  if (!r.ok()) {
    throw std::runtime_error(r.status().ToString());
  }
  cancel_ = r.ValueUnsafe();
}

int64_t SingleMarketDataManager::get_mdtime() const {
  auto table = get_prev_n_quote(1);
  return table.len() > 0 ? table.item<QuoteSchema::Index::TRIGGER_TIME>() : 0;
}

Status SingleMarketDataManager::on_quote(const QuoteIndicator &quote_indicator) {
  if (num_quote_ >= quote_->num_rows()) {
    return Status::IndexError(num_quote_, " >= ", quote_->num_rows());
  }

  if (quote_indicator.invalid) {
    num_quote_++;
    return Status::OK();
  }

  TableMutableView<QuoteSchema> view{quote_, num_quote_};
  view.mutable_item<QuoteSchema::Index::LAST_PX>() = quote_indicator.last_px;
  view.mutable_item<QuoteSchema::Index::HIGH_PX>() = quote_indicator.high_px;
  view.mutable_item<QuoteSchema::Index::LOW_PX>() = quote_indicator.low_px;
  view.mutable_item<QuoteSchema::Index::TOTAL_VOLUME>() = quote_indicator.total_volume;
  view.mutable_item<QuoteSchema::Index::TOTAL_TURNOVER>() = quote_indicator.total_turnover;
  view.mutable_item<QuoteSchema::Index::TOTAL_ASK_QTY>() = quote_indicator.total_ask_qty;
  view.mutable_item<QuoteSchema::Index::TOTAL_BID_QTY>() = quote_indicator.total_bid_qty;
  view.mutable_item<QuoteSchema::Index::TRADES>() = quote_indicator.trades;
  view.mutable_item<QuoteSchema::Index::TRIGGER_APPL_SEQ_NUM>() = quote_indicator.trigger_appl_seq_num;

  // triiger time / trigger time sample flag
  auto &trigger_time = view.mutable_item<QuoteSchema::Index::TRIGGER_TIME>();
  auto &sample_flag = view.mutable_item<QuoteSchema::Index::SAMPLE_1S_FLAG>();
  trigger_time = mdtime_millis_since_today(quote_indicator.trigger_time);
  if (num_quote_ > 0) {
    const auto &prev_trigger_time = *(&trigger_time - 1);
    if (prev_trigger_time / 1000 < trigger_time / 1000) {
      sample_flag = 1;
    }
  }

  // Use memcpy to copy the C-style array. maybe faster.
  auto *list_item1 = view.mutable_list_item<QuoteSchema::Index::BID_QTY>();
  std::memcpy(list_item1, quote_indicator.bid_qty, sizeof(quote_indicator.bid_qty));

  list_item1 = view.mutable_list_item<QuoteSchema::Index::BID_PRICE>();
  std::memcpy(list_item1, quote_indicator.bid_price, sizeof(quote_indicator.bid_price));

  auto *list_item2 = view.mutable_list_item<QuoteSchema::Index::BID_ORDER_NUMS>();
  std::memcpy(list_item2, quote_indicator.bid_order_nums, sizeof(quote_indicator.bid_order_nums));

  list_item1 = view.mutable_list_item<QuoteSchema::Index::ASK_QTY>();
  std::memcpy(list_item1, quote_indicator.ask_qty, sizeof(quote_indicator.ask_qty));

  list_item1 = view.mutable_list_item<QuoteSchema::Index::ASK_PRICE>();
  std::memcpy(list_item1, quote_indicator.ask_price, sizeof(quote_indicator.ask_price));

  list_item2 = view.mutable_list_item<QuoteSchema::Index::ASK_ORDER_NUMS>();
  std::memcpy(list_item2, quote_indicator.ask_order_nums, sizeof(quote_indicator.ask_order_nums));

  view.mutable_item<QuoteSchema::Index::AVG_BUY_PRICE>() = quote_indicator.avg_buy_price;
  view.mutable_item<QuoteSchema::Index::AVG_SELL_PRICE>() = quote_indicator.avg_sell_price;

  num_quote_++;

  if (quote_indicator.extension == 2) {
    const auto &order_cancel = static_cast<const QuoteIndicatorOrderCancel *>(&quote_indicator)->order_cancel;
    switch (order_cancel.market_data_type) {
    case 1: {
      ARROW_RETURN_NOT_OK(on_order(quote_indicator, trigger_time));
      ARROW_RETURN_NOT_OK(on_trade(quote_indicator, trigger_time));
      break;
    }

    case 2: {
      ARROW_RETURN_NOT_OK(on_cancel(quote_indicator, trigger_time));
      break;
    }

    default:
      break;
    }
  }

  return Status::OK();
}

Status SingleMarketDataManager::on_trade(const QuoteIndicator &quote_indicator, int64_t trigger_time) {
  if (num_trade_ >= trade_->num_rows()) {
    return Status::IndexError(num_trade_, ">=", trade_->num_rows());
  }

  if (num_quote_ < 2) {
    return Status::OK();
  }

  const auto &order_cancel = static_cast<const QuoteIndicatorOrderCancel *>(&quote_indicator)->order_cancel;
  auto prev_quote = get_prev_n_quote(2);
  auto volume = quote_indicator.total_volume - prev_quote.item<QuoteSchema::Index::TOTAL_VOLUME>();

  if (volume > 0) {
    auto turnover = quote_indicator.total_turnover - prev_quote.item<QuoteSchema::Index::TOTAL_TURNOVER>();
    auto price = turnover / volume;

    TableMutableView<TradeSchema> trade_view{trade_, num_trade_};
    trade_view.mutable_item<TradeSchema::Index::TIMESTAMP>() = trigger_time;
    trade_view.mutable_item<TradeSchema::Index::SIDE>() = order_cancel.side;
    trade_view.mutable_item<TradeSchema::Index::PRICE>() = price;
    trade_view.mutable_item<TradeSchema::Index::QUANTITY>() = volume;
    trade_view.mutable_item<TradeSchema::Index::TURNOVER>() = turnover;
    trade_view.mutable_item<TradeSchema::Index::CHANNEL_NO>() = order_cancel.channel_no;
    trade_view.mutable_item<TradeSchema::Index::APPL_SEQ_NUM>() = quote_indicator.trigger_appl_seq_num;
    num_trade_++;
  }

  return Status::OK();
}

Status SingleMarketDataManager::on_order(const QuoteIndicator &quote_indicator, int64_t trigger_time) {
  if (num_order_ >= order_->num_rows()) {
    return Status::IndexError(num_order_, ">=", order_->num_rows());
  }

  const auto &order_cancel = static_cast<const QuoteIndicatorOrderCancel *>(&quote_indicator)->order_cancel;
  TableMutableView<OrderSchema> order_view{order_, num_order_};
  order_view.mutable_item<OrderSchema::Index::TIMESTAMP>() = trigger_time;
  order_view.mutable_item<OrderSchema::Index::SIDE>() = order_cancel.side;
  order_view.mutable_item<OrderSchema::Index::PRICE>() = order_cancel.price;
  order_view.mutable_item<OrderSchema::Index::QUANTITY>() = order_cancel.quantity;
  order_view.mutable_item<OrderSchema::Index::APPL_SEQ_NUM>() = quote_indicator.trigger_appl_seq_num;
  order_view.mutable_item<OrderSchema::Index::CHANNEL_NO>() = order_cancel.channel_no;
  num_order_++;

  return Status::OK();
}

Status SingleMarketDataManager::on_cancel(const QuoteIndicator &quote_indicator, int64_t trigger_time) {
  if (num_cancel_ >= cancel_->num_rows()) {
    return Status::IndexError(num_cancel_, ">=", cancel_->num_rows());
  }

  const auto &order_cancel = static_cast<const QuoteIndicatorOrderCancel *>(&quote_indicator)->order_cancel;
  TableMutableView<CancelSchema> cancel_view{order_, num_cancel_};
  cancel_view.mutable_item<CancelSchema::Index::TIMESTAMP>() = trigger_time;
  cancel_view.mutable_item<CancelSchema::Index::SIDE>() = (int8_t)order_cancel.side;
  cancel_view.mutable_item<CancelSchema::Index::PRICE>() = order_cancel.price;
  cancel_view.mutable_item<CancelSchema::Index::QUANTITY>() = order_cancel.quantity;
  cancel_view.mutable_item<CancelSchema::Index::APPL_SEQ_NUM>() = quote_indicator.trigger_appl_seq_num;
  cancel_view.mutable_item<CancelSchema::Index::CHANNEL_NO>() = order_cancel.channel_no;
  num_cancel_++;

  return Status::OK();
}

std::string SingleMarketDataManager::to_string() const { return json(*this).dump(); }

std::shared_ptr<MarketDataManager> MarketDataManager::Instance(const MarketDataManagerOption &option) {
  static std::shared_ptr<MarketDataManager> mdm;
  if (mdm != nullptr) {
    return mdm;
  }

  switch (option.type) {
  case MarketDataManagerOption::MarketDataManagerType::DEFAULT: {
    mdm = std::make_shared<MarketDataManager>(option);
    break;
  }

  case MarketDataManagerOption::MarketDataManagerType::ARROW_TABLE: {
    mdm = std::make_shared<ArrowTableMarketDataManager>(option);
    break;
  }

  case MarketDataManagerOption::MarketDataManagerType::PARQUET_FILE: {
    mdm = std::make_shared<ParquetFileMarketDataManager>(option);
    break;
  }
  }

  return mdm;
}

void MarketDataManager::add_symbol(const std::string &symbol) {
  auto [it, inserted] = symbol_mdm_map_.try_emplace(symbol, nullptr);
  if (!inserted) {
    return;
  }

  it->second = std::make_shared<SingleMarketDataManager>(option_);
  default_mdm_ = it->second;
}

Status MarketDataManager::on_quote(const QuoteIndicator &quote) {
  if (symbol_mdm_map_.size() == 1) {
    ARROW_RETURN_NOT_OK(default_mdm_->on_quote(quote));
  } else if (auto it = symbol_mdm_map_.find(quote.symbol); it != symbol_mdm_map_.end()) {
    auto &[_, smdm] = *it;
    ARROW_RETURN_NOT_OK(smdm->on_quote(quote));
  } else {
    return Status::KeyError("Symbol not found: ", quote.symbol);
  }

  return Status::OK();
}

Result<int64_t> ArrowTableMarketDataManager::next() {
  auto quote = next_row();
  if (quote == std::nullopt) {
    return Status::IndexError("Data end: ", row_index_);
  }

  if (symbol_mdm_map_.empty()) {
    add_symbol({});
  }

  ARROW_RETURN_NOT_OK(on_quote(quote.value()));
  return row_index_ - 1;
}

std::optional<QuoteIndicatorOrderCancel> ArrowTableMarketDataManager::next_row() {
  if (data_record_batch_ == nullptr || row_index_ >= num_rows()) {
    return std::nullopt;
  }

  QuoteIndicatorOrderCancel quote{};
  auto &order_cancel = quote.order_cancel;

  // quote
  auto code_str = std::static_pointer_cast<arrow::StringArray>(data_record_batch_->GetColumnByName("code_str"));
  if (code_str != nullptr) {
    auto symbol = std::static_pointer_cast<arrow::StringScalar>(code_str->GetScalar(row_index_).ValueOrDie())->view();
    std::strncpy(quote.symbol, symbol.data(), std::min(sizeof(quote.symbol), symbol.size()));
  }

  auto mdtime = std::static_pointer_cast<arrow::Int64Array>(data_record_batch_->GetColumnByName("mdtime"));
  if (mdtime != nullptr) {
    quote.trigger_time = mdtime->Value(row_index_) % static_cast<uint32_t>(1e9);
  }

  auto last_px = std::static_pointer_cast<arrow::FloatArray>(data_record_batch_->GetColumnByName("last_price"));
  if (last_px != nullptr) {
    quote.last_px = last_px->Value(row_index_);
  }

  auto asks_price_column = extract_list<arrow::FloatArray>(data_record_batch_, "asks_price", row_index_);

  auto bids_price_column = extract_list<arrow::FloatArray>(data_record_batch_, "bids_price", row_index_);

  auto asks_qty_column = extract_list<arrow::Int32Array>(data_record_batch_, "asks_qty", row_index_);

  auto bids_qty_column = extract_list<arrow::Int32Array>(data_record_batch_, "bids_qty", row_index_);

  auto asks_count_column = extract_list<arrow::Int32Array>(data_record_batch_, "asks_count", row_index_);

  auto bids_count_column = extract_list<arrow::Int32Array>(data_record_batch_, "bids_count", row_index_);

  for (int i = 0; i < 10; i++) {
    asks_price_column != nullptr && (quote.ask_price[i] = asks_price_column->Value(i));
    bids_price_column != nullptr && (quote.bid_price[i] = bids_price_column->Value(i));
    asks_qty_column != nullptr && (quote.ask_qty[i] = asks_qty_column->Value(i));
    bids_qty_column != nullptr && (quote.bid_qty[i] = bids_qty_column->Value(i));
    asks_count_column != nullptr && (quote.ask_order_nums[i] = asks_count_column->Value(i));
    bids_count_column != nullptr && (quote.bid_order_nums[i] = bids_count_column->Value(i));
  }

  auto high_px = std::static_pointer_cast<arrow::FloatArray>(data_record_batch_->GetColumnByName("high_price"));
  if (high_px != nullptr) {
    quote.high_px = high_px->Value(row_index_);
  }

  auto low_px = std::static_pointer_cast<arrow::FloatArray>(data_record_batch_->GetColumnByName("low_price"));
  if (low_px != nullptr) {
    quote.low_px = low_px->Value(row_index_);
  }

  auto total_volume = std::static_pointer_cast<arrow::Int32Array>(data_record_batch_->GetColumnByName("ttl_volume"));
  if (total_volume != nullptr) {
    quote.total_volume = total_volume->Value(row_index_);
  }

  auto total_turnover =
      std::static_pointer_cast<arrow::DoubleArray>(data_record_batch_->GetColumnByName("ttl_turn_over"));
  if (total_turnover != nullptr) {
    quote.total_turnover = total_turnover->Value(row_index_);
  }

  auto trades = std::static_pointer_cast<arrow::Int32Array>(data_record_batch_->GetColumnByName("ttl_trade_num"));
  if (trades != nullptr) {
    quote.trades = trades->Value(row_index_);
  }

  auto last_seq_num = std::static_pointer_cast<arrow::Int64Array>(data_record_batch_->GetColumnByName("last_seq_num"));
  if (last_seq_num != nullptr) {
    quote.trigger_appl_seq_num = last_seq_num->Value(row_index_);
  }

  int64_t msg_trade_type = 1;
  auto trade_type = std::static_pointer_cast<arrow::Int32Array>(data_record_batch_->GetColumnByName("msg_trade_type"));
  if (trade_type != nullptr) {
    msg_trade_type = trade_type->Value(row_index_);
  }

  auto msg_order_type = 0;
  auto order_type = std::static_pointer_cast<arrow::Int32Array>(data_record_batch_->GetColumnByName("msg_order_type"));
  if (order_type != nullptr) {
    msg_order_type = order_type->Value(row_index_);
  }

  int64_t side = 0;
  auto msg_bsflag = std::static_pointer_cast<arrow::Int32Array>(data_record_batch_->GetColumnByName("msg_bsflag"));
  if (msg_bsflag != nullptr) {
    side = msg_bsflag->Value(row_index_);
  }

  double price = 0;
  auto msg_price = std::static_pointer_cast<arrow::FloatArray>(data_record_batch_->GetColumnByName("msg_price"));
  if (msg_price != nullptr) {
    price = msg_price->Value(row_index_);
  }

  double qty = 0;
  auto msg_qty = std::static_pointer_cast<arrow::Int32Array>(data_record_batch_->GetColumnByName("msg_qty"));
  if (msg_qty != nullptr) {
    qty = msg_qty->Value(row_index_);
  }

  double amt = 0;
  auto msg_amt = std::static_pointer_cast<arrow::FloatArray>(data_record_batch_->GetColumnByName("msg_amt"));
  if (msg_amt != nullptr) {
    amt = msg_amt->Value(row_index_);
  }

  uint64_t buy_no = 0;
  auto msg_buy_no = std::static_pointer_cast<arrow::Int64Array>(data_record_batch_->GetColumnByName("msg_buy_no"));
  if (msg_buy_no != nullptr) {
    buy_no = msg_buy_no->Value(row_index_);
  }

  uint64_t sell_no = 0;
  auto msg_sell_no = std::static_pointer_cast<arrow::Int64Array>(data_record_batch_->GetColumnByName("msg_sell_no"));
  if (msg_sell_no != nullptr) {
    sell_no = msg_sell_no->Value(row_index_);
  }

  if (std::string_view(quote.symbol).ends_with(".SH")) {
    if (msg_order_type == 10) {
      // cancel
      quote.extension = 2;
      order_cancel.market_data_type = 2;
      order_cancel.side = side;
      order_cancel.price = price;
      order_cancel.quantity = qty;
    } else if (msg_order_type != -1) {
      // order
      quote.extension = 2;
      order_cancel.market_data_type = 1;
      order_cancel.side = side;
      order_cancel.price = price;
      order_cancel.quantity = qty;
    }
  } else {
    if (msg_trade_type == 1) {
      // cancel
      quote.extension = 2;
      order_cancel.market_data_type = 2;
      order_cancel.side = side;
      order_cancel.price = price;
      order_cancel.quantity = qty;
    } else if (msg_order_type != -1) {
      // order
      quote.extension = 2;
      order_cancel.market_data_type = 1;
      order_cancel.side = side;
      order_cancel.price = price;
      order_cancel.quantity = qty;
    }
  }

  row_index_++;
  return quote;
}

Status ArrowTableMarketDataManager ::set_table(std::shared_ptr<arrow::Table> table) {
  if (table == nullptr) {
    return Status::OK();
  }

  ARROW_ASSIGN_OR_RAISE(data_record_batch_, table->CombineChunksToBatch());
  reset();
  return Status::OK();
}

std::string ArrowTableMarketDataManager::to_string() const {
  if (data_record_batch_ == nullptr) {
    return "Arrow table not loaded";
  }

  json j;
  j["type"] = option_.type;
  j["data"] = [this]() {
    json data;
    for (const auto &[symbol, smdm] : symbol_mdm_map_) {
      data[symbol] = json(*smdm);
    }
    return data;
  }();

  return j.dump();
}

Status ParquetFileMarketDataManager::load() {
  if (data_record_batch_ != nullptr || path_.empty()) {
    return Status::OK();
  }

  fs::path path(path_);
  ARROW_ASSIGN_OR_RAISE(std::shared_ptr<arrow::io::RandomAccessFile> input,
                        arrow::io::ReadableFile::Open(path.string()));

  std::unique_ptr<parquet::arrow::FileReader> arrow_reader;
  ARROW_RETURN_NOT_OK(parquet::arrow::OpenFile(input, MEMORY_POOL, &arrow_reader));

  std::shared_ptr<arrow::Table> table;
  ARROW_RETURN_NOT_OK(arrow_reader->ReadTable(&table));
  ARROW_ASSIGN_OR_RAISE(data_record_batch_, table->CombineChunksToBatch());

  return Status::OK();
}

Status ParquetFileMarketDataManager::set_path(const std::string &path) {
  path_ = path;
  ARROW_RETURN_NOT_OK(load());
  reset();
  return Status::OK();
}

std::string ParquetFileMarketDataManager::to_string() const {
  if (data_record_batch_ == nullptr) {
    return "Parquet file not loaded";
  }

  json j;
  j["path"] = path_;
  j["type"] = option_.type;
  j["data"] = [this]() {
    json data;
    for (const auto &[symbol, smdm] : symbol_mdm_map_) {
      data[symbol] = json(*smdm);
    }
    return data;
  }();

  return j.dump();
}

} // namespace huatai::atsquant::factor