#pragma once

#include "datetime.h"
#include "sliding_window.h"

#include <arrow/api.h>
#include <fmt/format.h>
#include <map>
#include <ranges>
#include <set>
#include <sys/time.h>

#ifndef FACTOR_EXPORT
#define FACTOR_EXPORT [[gnu::visibility("default")]]
#endif

namespace huatai::atsquant::factor {

using arrow::Result;
using arrow::Status;
using arrow::Type;

static arrow::MemoryPool *MEMORY_POOL = arrow::default_memory_pool();

inline arrow::Result<std::shared_ptr<arrow::RecordBatch>>
make_zero_filled_record_batch(const std::shared_ptr<arrow::Schema> &schema, int64_t num_rows, int64_t list_size = 0) {
  ARROW_ASSIGN_OR_RAISE(auto rb_builder, arrow::RecordBatchBuilder::Make(schema, MEMORY_POOL, num_rows));
  for (int i = 0; i < rb_builder->num_fields(); i++) {
    auto field = schema->field(i);
    auto field_builder = rb_builder->GetField(i);

    switch (field->type()->id()) {
    case Type::LIST:
    case Type::LARGE_LIST:
    case Type::FIXED_SIZE_LIST:
      // a list type field
      for (int j = 0; j < num_rows; j++) {
        ARROW_RETURN_NOT_OK(field_builder->AppendEmptyValue());
        auto *list_builder = dynamic_cast<arrow::LargeListBuilder *>(field_builder);
        if (list_builder == nullptr) {
          return arrow::Status::TypeError("Field \"", field->name(), "\" with type ", field->type()->name(),
                                          " is not compatitable with arrow::LargeListBuilder ");
        }
        ARROW_RETURN_NOT_OK(list_builder->value_builder()->AppendEmptyValues(list_size));
      }
      break;

    default:
      // a numeric type filed
      ARROW_RETURN_NOT_OK(field_builder->AppendEmptyValues(num_rows));
      break;
    }
  }

  ARROW_ASSIGN_OR_RAISE(auto rb, rb_builder->Flush());
  return rb;
}

template <typename ArrowArrayType>
std::shared_ptr<arrow::NumericArray<typename ArrowArrayType::TypeClass>>
extract_list(const std::shared_ptr<arrow::RecordBatch> &rb, const std::string &column_name, int64_t index) {
  auto column = rb->GetColumnByName(column_name);
  if (column == nullptr) {
    return nullptr;
  }

  if (column->type()->id() == arrow::ListArray::TypeClass::type_id) {
    return std::static_pointer_cast<ArrowArrayType>(
        std::static_pointer_cast<arrow::ListArray>(column)->value_slice(index));
  } else if (column->type()->id() == arrow::LargeListArray::TypeClass::type_id) {
    return std::static_pointer_cast<ArrowArrayType>(
        std::static_pointer_cast<arrow::LargeListArray>(column)->value_slice(index));
  }

  return nullptr;
}

template <typename SchemaType> struct RowView {
  using index_t = SchemaType::Index;
  template <index_t I> using element_t = SchemaType::template element_t<I>;
  template <index_t I> using arrow_array_t = SchemaType::template arrow_array_t<I>;

  template <index_t I> constexpr const element_t<I> &item() const {
    auto array_column = std::static_pointer_cast<arrow_array_t<I>>(rb->column(static_cast<int>(I)));
    return array_column->raw_values()[row_index];
  }

  template <index_t I> constexpr const element_t<I> *item_address() const { return &item<I>(); }

  template <index_t I, typename ListArrayType = arrow::LargeListArray> constexpr const element_t<I> *list_item() const {
    auto list_column = std::static_pointer_cast<ListArrayType>(rb->column(static_cast<int>(I)));
    auto array_item = std::static_pointer_cast<arrow_array_t<I>>(list_column->value_slice(row_index));
    return array_item->raw_values();
  }

  const std::shared_ptr<arrow::RecordBatch> &rb;
  const int64_t row_index = 0;
};

template <typename SchemaType> struct TableView {
  using index_t = SchemaType::Index;
  template <index_t I> using element_t = SchemaType::template element_t<I>;
  template <index_t I> using arrow_array_t = SchemaType::template arrow_array_t<I>;

  template <typename ArrayType, typename IndexType = index_t>
  const ArrayType::value_type &item(IndexType column_index) const {
    auto array_column = std::static_pointer_cast<ArrayType>(rb->column(static_cast<int>(column_index)));
    return array_column->raw_values()[row_index];
  }

  template <index_t I> constexpr const element_t<I> &item() const {
    auto array_column = std::static_pointer_cast<arrow_array_t<I>>(rb->column(static_cast<int>(I)));
    return array_column->raw_values()[row_index];
  }

  template <index_t I> constexpr const element_t<I> *item_address() const { return &item<I>(); }

  template <typename ArrayType, typename IndexType = index_t, typename ListArrayType = arrow::LargeListArray>
  const ArrayType::value_type *list_item(IndexType column_index) const {
    auto list_column = std::static_pointer_cast<ListArrayType>(rb->column(static_cast<int>(column_index)));
    auto array_item = std::static_pointer_cast<ArrayType>(list_column->value_slice(row_index));
    return array_item->raw_values();
  }

  template <index_t I, typename ListArrayType = arrow::LargeListArray> constexpr const element_t<I> *list_item() const {
    auto list_column = std::static_pointer_cast<ListArrayType>(rb->column(static_cast<int>(I)));
    auto array_item = std::static_pointer_cast<arrow_array_t<I>>(list_column->value_slice(row_index));
    return array_item->raw_values();
  }

  template <typename Func> void for_each(Func &&func) const {
    const auto tv = *this;
    for (auto &i = std::remove_const_t<int64_t &>(tv.row_index); i < end_index; i++) {
      std::invoke(std::forward<Func>(func), tv);
    }
  }

  template <index_t I, typename ListArrayType = arrow::LargeListArray>
  std::vector<double> level(int64_t n_level) const {
    std::vector<double> level_data;
    for_each([&level_data, n_level](const auto &row) {
      const auto *list_item = row.template list_item<I, ListArrayType>();
      level_data.emplace_back(list_item[n_level]);
    });
    return level_data;
  }

  RowView<SchemaType> operator[](int64_t offset) const {
    auto l = len();
    auto r = offset % l;
    if (r < 0) {
      r += l;
    }

    return {rb, row_index + r};
  }

  TableView<SchemaType> slice(int64_t start, int64_t end) const { return {rb, row_index + start, row_index + end}; }

  TableView<SchemaType> slice(int64_t start) const { return {rb, row_index + start, end_index}; }

  int64_t len() const { return end_index - row_index; }

  const std::shared_ptr<arrow::RecordBatch> &rb;
  const int64_t row_index = 0;
  const int64_t end_index = 0;
};

template <typename SchemaType> struct TableMutableView : public TableView<SchemaType> {
  using index_t = TableView<SchemaType>::index_t;
  template <index_t I> using element_t = TableView<SchemaType>::template element_t<I>;
  template <index_t I> using arrow_array_t = TableView<SchemaType>::template arrow_array_t<I>;

  template <typename ArrayType, typename IndexType> ArrayType::value_type &mutable_item(IndexType column_index) const {
    return std::remove_const_t<typename ArrayType::value_type &>(item<ArrayType>(column_index));
  }

  template <index_t I> constexpr element_t<I> &mutable_item() const {
    return std::remove_const_t<element_t<I> &>(this->template item<I>());
  }

  template <index_t I> constexpr element_t<I> *mutable_item_address() const {
    return std::remove_const_t<element_t<I> *>(this->template item_address<I>());
  }

  template <typename ArrayType, typename IndexType, typename ListArrayType = arrow::LargeListArray>
  ArrayType::value_type *mutable_list_item(IndexType column_index) const {
    return std::remove_const_t<typename ArrayType::value_type *>(list_item<ArrayType, ListArrayType>(column_index));
  }

  template <index_t I, typename ListArrayType = arrow::LargeListArray>
  constexpr element_t<I> *mutable_list_item() const {
    return std::remove_const_t<element_t<I> *>(this->template list_item<I, ListArrayType>());
  }
};

inline long now_in_milli() {
  timespec ts;
  clock_gettime(CLOCK_REALTIME, &ts);
  return ts.tv_sec * 1000 + ts.tv_nsec / 1000000;
}

inline int64_t now_in_nano() {
  timespec ts;
  clock_gettime(CLOCK_REALTIME, &ts);
  return ts.tv_sec * (int64_t)1e9 + ts.tv_nsec;
}

inline int64_t exchange_time_to_unix_timestamp(int64_t exchange_time) {
  // 20240116093703430
  std::tm timestamp_tm;
  auto d = std::lldiv(exchange_time, 1000);
  auto millis = d.rem;

  d = std::lldiv(d.quot, 100);
  timestamp_tm.tm_sec = d.rem;

  d = std::lldiv(d.quot, 100);
  timestamp_tm.tm_min = d.rem;

  d = std::lldiv(d.quot, 100);
  timestamp_tm.tm_hour = d.rem;

  d = std::lldiv(d.quot, 100);
  timestamp_tm.tm_mday = d.rem;

  d = std::lldiv(d.quot, 100);
  timestamp_tm.tm_mon = d.rem - 1;

  timestamp_tm.tm_year = d.quot - 1900;

  return std::mktime(&timestamp_tm) * 1000 + millis;
}

struct TopologicalSortPath {
  std::set<size_t> node_set;
  std::vector<size_t> node_path;

  void push(size_t n) {
    node_set.insert(n);
    node_path.emplace_back(n);
  }

  void pop() {
    if (!node_path.empty()) {
      node_set.erase(node_path.back());
      node_path.pop_back();
    }
  }

  bool contains(size_t n) const { return node_set.contains(n); }
};

template <typename G>
bool topological_sort_dfs(const G &graph, std::vector<size_t> &sorted, std::vector<bool> &visited,
                          TopologicalSortPath &path, size_t node) {
  if (path.contains(node)) {
    return true;
  }

  if (visited[node]) {
    return false;
  }

  visited[node] = true;
  path.push(node);
  for (auto n : graph.at(node)) {
    if (topological_sort_dfs(graph, sorted, visited, path, n)) {
      return true;
    }
  }

  sorted.emplace_back(node);
  path.pop();
  return false;
}

template <typename G> std::pair<std::vector<size_t>, bool> topological_sort(G graph) {
  std::vector<size_t> sorted;

  std::vector<bool> visited(graph.size());
  TopologicalSortPath path;
  for (size_t i = 0; i < graph.size(); i++) {
    if (topological_sort_dfs(graph, sorted, visited, path, i)) {
      return {path.node_path, false};
    }
  }

  return {sorted, true};
}

} // namespace huatai::atsquant::factor