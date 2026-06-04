#include "huatai/atsquant/factor.h"
#include "huatai/atsquant/factor/compute.h"

#include <arrow/python/pyarrow.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace PYBIND11_NAMESPACE {
namespace detail {

template <> struct type_caster<std::shared_ptr<arrow::Table>> {
public:
  PYBIND11_TYPE_CASTER(std::shared_ptr<arrow::Table>, _("pyarrow::Table"));

  bool load(handle src, bool) {
    PyObject *source = src.ptr();
    auto result = arrow::py::unwrap_table(source);
    if (!result.ok()) {
      return false;
    }

    value = result.ValueUnsafe();
    return true;
  }

  static handle cast(std::shared_ptr<arrow::Table> src, return_value_policy, handle) {
    return arrow::py::wrap_table(src);
  }
};

} // namespace detail
} // namespace PYBIND11_NAMESPACE

namespace huatai::atsquant::factor {

namespace py = pybind11;
using namespace pybind11::literals;
using json = nlohmann::json;

PYBIND11_MODULE(PROJECT_NAME_LOWER, m) {
  py::class_<MarketDataManagerOption, std::shared_ptr<MarketDataManagerOption>> mdm_option(m,
                                                                                           "MarketDataManagerOption");
  py::enum_<MarketDataManagerOption::MarketDataManagerType>(mdm_option, "MarketDataManagerType")
      .value("DEFAULT", MarketDataManagerOption::MarketDataManagerType::DEFAULT)
      .value("ARROW_TABLE", MarketDataManagerOption::MarketDataManagerType::ARROW_TABLE)
      .value("PARQUET_FILE", MarketDataManagerOption::MarketDataManagerType::PARQUET_FILE);

  mdm_option
      .def(py::init([](int64_t quote_rows, int64_t trade_rows, int64_t order_rows, int64_t cancel_rows) {
             auto option = std::make_shared<MarketDataManagerOption>();
             option->quote_rows = quote_rows;
             option->trade_rows = trade_rows;
             option->order_rows = order_rows;
             option->cancel_rows = cancel_rows;
             return option;
           }),
           "quote_rows"_a = 1000000, "trade_rows"_a = 500000, "order_rows"_a = 500000, "cancel_rows"_a = 500000)
      .def("__str__", [](const MarketDataManagerOption &option) { return json(option).dump(); })
      .def_readwrite("quote_rows", &MarketDataManagerOption::quote_rows)
      .def_readwrite("trade_rows", &MarketDataManagerOption::trade_rows)
      .def_readwrite("order_rows", &MarketDataManagerOption::order_rows)
      .def_readwrite("cancel_rows", &MarketDataManagerOption::cancel_rows)
      .def_readwrite("type", &MarketDataManagerOption::type);

  py::class_<MarketDataManager, std::shared_ptr<MarketDataManager>>(m, "MarketDataManager");

  py::class_<ArrowTableMarketDataManager, std::shared_ptr<ArrowTableMarketDataManager>>(m,
                                                                                        "ArrowTableMarketDataManager")
      .def(py::init([](std::shared_ptr<arrow::Table> table, MarketDataManagerOption option) {
             option.type = MarketDataManagerOption::MarketDataManagerType::ARROW_TABLE;
             auto mdm = std::dynamic_pointer_cast<ArrowTableMarketDataManager>(MarketDataManager::Instance(option));
             if (mdm == nullptr) {
               throw std::runtime_error("Can't convert to ArrowTableMarketDataManager");
             }

             auto st = mdm->set_table(table);
             if (!st.ok()) {
               throw std::runtime_error(st.ToString());
             }

             return mdm;
           }),
           "table"_a, "option"_a = MarketDataManagerOption{})
      .def("__str__", &ArrowTableMarketDataManager::to_string)
      .def("next",
           [](ArrowTableMarketDataManager &mdm) -> int64_t {
             auto re = mdm.next();
             if (!re.ok()) {
               return mdm.num_rows();
             }

             return re.ValueUnsafe();
           })
      .def("is_end", &ArrowTableMarketDataManager::is_end);

  py::class_<ParquetFileMarketDataManager, std::shared_ptr<ParquetFileMarketDataManager>>(
      m, "ParquetFileMarketDataManager")
      .def(py::init([](const std::string &path, MarketDataManagerOption option) {
             option.type = MarketDataManagerOption::MarketDataManagerType::PARQUET_FILE;
             auto mdm = std::dynamic_pointer_cast<ParquetFileMarketDataManager>(MarketDataManager::Instance(option));
             if (mdm == nullptr) {
               throw std::runtime_error("Can't convert to ParquetFileMarketDataManager");
             }

             auto st = mdm->set_path(path);
             if (!st.ok()) {
               throw std::runtime_error(st.ToString());
             }

             return mdm;
           }),
           "path"_a, "option"_a = MarketDataManagerOption{})
      .def("__str__", &ParquetFileMarketDataManager::to_string);

  py::class_<FactorManager, std::shared_ptr<FactorManager>>(m, "FactorManager")
      .def(py::init([](const std::string &param_json, MarketDataManagerOption option) {
             auto re = FactorManager::New(json::parse(param_json), option);
             if (!re.ok()) {
               throw std::runtime_error(re.status().ToString());
             }
             return re.ValueUnsafe();
           }),
           "param_json"_a, "option"_a = MarketDataManagerOption{})
      .def("__str__", &FactorManager::to_string)
      .def("set_param", [](FactorManager &fm, const std::string &param_json) { fm.set_param(json::parse(param_json)); })
      .def("caculate",
           [](FactorManager &fm) {
             auto st = fm.caculate();
             if (!st.ok()) {
               throw std::runtime_error(st.ToString());
             }
           })
      .def("values", &FactorManager::values)
      .def("dump_taskflow", &FactorManager::dump_taskflow);
}

} // namespace huatai::atsquant::factor