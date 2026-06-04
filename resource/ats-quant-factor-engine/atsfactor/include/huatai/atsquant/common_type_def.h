/**
 * @file common_type_def.h
 * @brief 基本枚举类型定义
 * @author 刘从文
 * @date 2023-02-11
 *
 * @copyright Copyright (c) 2023
 *
 * @par 修改日志:
 * <table>
 * <tr> <th>日期</th>       <th>作者</th> <th>修改说明</th> </tr>
 * <tr> <td>2023-02-11</td> <td>刘从文</td> <td>初始创建</td> </tr>
 * </table>
 */
#pragma once

#include <cstdint>
#include <inttypes.h>
#include <iostream>
#include <nlohmann/json.hpp>
#include <string>
#include <vector>

namespace huatai::atsquant::common {
// 行情类型
enum class QuoteType {
  QT_INDEX,          // 指数
  QT_STOCK,          // 股票
  QT_FUND,           // 基金
  QT_BOND,           // 债券
  QT_FUTURE,         // 期货
  QT_OPTION,         // 期权
  QT_FOREX_SNAPSHOT, // 外汇市场
  QT_FOREX_QUOTE,    // 外汇报价
};

// 交易阶段
enum class TradingPhaseCode {
  UNKNOWN = -1,                 // 未知
  BEFORE_OPENING,               // 开盘前，启动
  OPENING_AUCTION,              // 开盘集合竞价
  AUCTION_TRADING_GAP,          // 开盘集合竞价至连续竞价
  TRADING,                      // 连续竞价
  BREAK,                        // 午间休市
  CLOSING_AUCTION,              // 收盘集合竞价
  CLOSED,                       // 已闭市
  POST_TRADING,                 // 盘后交易
  TEMP_HALT,                    // 临时停牌
  VOLATILITY_BREAKS,            // 波动性中断
  PRE_POST_FIXED_PRICE_TRADING, // 竞价交易收盘至盘后固定价格交易之前
  POST_FIXED_PRICE_TRADING,     // 盘后固定价格交易
};

// 订单类型
enum class OrderType {
  UNKNOWN,      // 未知
  MARKET,       // 市价
  LIMIT,        // 限价
  FORWARD_BEST, // 本方最优
  CANCEL,       // 撤销委托 仅上交所字段
  STATUS, // 产品状态（仅上交所字段（新债券交易系统引入），用以说明产品状态，实际并非委托）
};

// 委托方向
enum class OrderSide {
  UNKNOWN, // 未知
  BUY,     // 买入
  SELL     // 卖出
};

// 证券状态
enum class SecurityStatus {
  UNKNOWN, // 未知
  ADD,     // 产品未上市
  START,   // 启动
  OCALL,   // 开市集合竞价
  TRADE,   // 连续自动撮合
  SUSP,    // 停牌
  CLOSE,   // 闭市
  ENDTR    // 交易结束
};

// 成交方向
enum class Side {
  UNKNOWN, // 成交方向不明
  BID,     // 主买
  OFFER    // 主卖
};

// 成交类型
enum class Type {
  UNKNOWN, // 未知
  FILLED,  // 成交
  CANCELED // 撤单
};

enum class ExchangeType {
  UNKNOWN, // 未知
  SH,      // 上交所
  SZ,      // 深交所
  SHF,     // 上期所
  CFE,     // 银行间
  CF,      // 中金所
  DCE,     // 大商所
  ZCE,     // 郑商所
  SGE,     // 上金所
  INE,     // 上海国际能源交易中心
  HK,      // 港交所
  OTC,     // 场外
  BJ,      // 北交所
  UW,      // 纳斯达克
};

// 证券类型
enum class SecurityType {
  INDEX,  // Index
  CS,     // CS
  FUND,   // Fund
  BOND,   // Bond
  REPO,   // Repo
  WAR,    // WAR
  OPT,    // OPT
  FUT,    // FUT
  FOREX,  // Forex
  RATE,   // Rate
  NMETAL, // Nmetal
  OTHER,  // Other
};

// 订单状态
enum class OrdStatus {
  PENDING_NEW,                 // 未报
  NEW,                         // 已报
  PARTIALLY_FILLED,            // 部成
  FILLED,                      // 已成
  PENDING_CANCEL,              // 已报待撤
  PARTIALLY_FILLED_FOR_CANCEL, // 部成待撤
  PARTIALLY_CANCEL,            // 部撤
  CANCELED,                    // 已撤
  REJECTED,                    // 废单
  UNDEFINED = -1,              // 未定义
};

// 开平方向
enum class PositionEffect {
  OPEN = 1,          // 开
  CLOSE = 2,         // 平
  EXERCISE = 3,      // 行权
  AUTO_EXERCISE = 4, // 自动行权
};

// 委托类型
enum class EntrustType {
  NEW_ORDER = 0,          // 委托
  QUERY = 1,              // 查询
  CANCEL_ORDER = 2,       // 撤单
  COMMODITY = 5,          // 大宗
  FUND_LOAN = 6,          // 信用融资
  SECURITY_LOAN = 7,      // 信用融券
  CLOSE_POSITION = 8,     // 信用平仓
  CREDIT_TRANSACTION = 9, // 信用交易（担保品买卖/担保品划转/直接还券）
};

// 委托属性
enum class EntrustProp {
  TRADING,                          // 买卖
  ALLOTMENT,                        // 配股
  TRANSFER,                         // 转托
  PURCHASE,                         // 申购
  RE_PURCHASE,                      // 回购
  PLACING,                          // 配售
  ASSIGN,                           // 指定
  CONVERSION,                       // 转股
  BACK_TO_SALE,                     // 回售
  COVERED_TRANS,                    // 备兑划转
  EXERCISE,                         // 期权行权
  PRICE_ENTRUST,                    // 定价委托
  CONFIRM_ENTRUST,                  // 确认委托
  INTER_BANK_MARKET_BUY_SELL,       // 银行间市场现券买卖
  INTER_BANK_MARKET_IMPAWN,         // 银行间市场质押式回购
  MUTUAL_REPORT_CONFIRM_ENTRUST,    // 互报成交确认委托
  IMPAWN,                           // 质押出入库
  CONFIRM_QUOTE_ENTRUST,            // 确认报价申报
  CLICK_REPORT_ENTRUST,             // 点击成交申报
  DESIGNATE_OPPONENT_QUOTE_ENTRUST, // 指定对手方报价申报
  ETF_PURCHASE_REDEMPTION,          // ETF申赎
  COLLATERAL_TRANSFER,              // 担保证券提交与返还
  DIRECT_RETURN_SECURITIES,         // 融资融券的直接换券
  INTEND_ENTRUST,                   // 意向委托
};

// 投资类型
enum class InvestType {
  DEFAULT = 0,     // 默认
  SPECULATION = 1, // 投机
  HEDGE = 2,       // 套保
  ARBITRAGE = 3,   // 套利
};

// 策略状态
enum class StrategyStatus {
  READY = 3,     // 已就绪（策略创建成功，未启动）
  RUNNING = 0,   // 运行中
  PAUSING = 7,   // 正在暂停
  PAUSED = 1,    // 已暂停
  STOPPING = 8,  // 正在停止
  STOPPED = 2,   // 已停止
  RESUMING = 6,  // 正在恢复
  UNDEFINED = 4, // 未定义状态（异常情况下状态）
};

// 策略日志级别
enum class StrategyLogLevel { TRACE = 0, DEBUG, INFO, WARN, ERROR, FATAL };

// 行情源
enum class MdSource { UDP, FAST_SH_FPGA, TCP };

// 外汇市场行情数据类型
enum class ForexMarketType {
  SPT = 1,       // 即期市场行情数据
  FOW = 2,       // 远期市场行情数据
  NDF = 3,       // 无本金交割远期市场行情数据
  SWP = 4,       // 掉期市场行情数据
  UNDEFINED = 8, // 未定义市场行情数据类型
};

// 组合信息
struct Portfolio {
  std::string symbol;
  int32_t quantity = 0;      // T0组合参数时传递
  int32_t buy_quantity = 0;  // Alpha组合参数时传递
  int32_t sell_quantity = 0; // Alpha组合参数时传递
  std::string buy_sec_acc;
  std::string sell_sec_acc;
  std::string buy_trade_acc;
  std::string sell_trade_acc;
  std::string portfolio_name;
  std::string portfolio_no;
  std::string portfolio_type;
};

// 策略报告类型枚举
enum class StrategyReportType : uint32_t { BACKGROUND = 0, UI, AUDIO };

struct SubscribeTradeAccount {
  std::vector<std::string> accounts;
  std::string text;
};
NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(SubscribeTradeAccount, accounts, text);

// 行情复权类型
enum class EExrightsType : uint32_t { NoExrights = 10, ForwardExrights = 11, BackwardExrights = 12 };

} // namespace huatai::atsquant::common
