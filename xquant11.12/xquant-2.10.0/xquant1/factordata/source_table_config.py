from enum import Enum, unique


@unique
class SQLTYPE(Enum):
    ST = 'stock_code as tradingcode,tdate,'
    SRT = 'stock_code as tradingcode,tdate,rpt_date,'
    SST = 'stock_code as tradingcode,stock_type,tdate,'
    SSRT = 'stock_code as tradingcode,stock_type,tdate,rpt_date,'
    BBT = 'block_code as tradingcode,block_type,tdate,'
    BBRT = 'block_code as tradingcode,block_type,tdate,rpt_date,'


conforecast_config = {"schema": "xquant_gogoal",
                      "factor_info": {"rating_up_number7": ["rating_up_number7", "stock_report_adjustment2"],
                                      "rating_down_number7": ["rating_down_number7", "stock_report_adjustment2"],
                                      "rating_down_number30": ["rating_down_number30", "stock_report_adjustment2"],
                                      "report_number30": ["report_number30", "stock_report_number"],
                                      "author_number7": ["author_number7", "stock_report_number"],
                                      "author_number90": ["author_number90", "stock_report_number"],
                                      "organ_number30": ["organ_number30", "stock_report_number"],
                                      "buy_number7": ["buy_number7", "stock_report_number"],
                                      "buy_number90": ["buy_number90", "stock_report_number"],
                                      "overweight_number30": ["overweight_number30", "stock_report_number"],
                                      "neutral_number7": ["neutral_number7", "stock_report_number"],
                                      "underweight_number7": ["underweight_number7", "stock_report_number"],
                                      "underweight_number30": ["underweight_number30", "stock_report_number"],
                                      "sell_number30": ["sell_number30", "stock_report_number"],
                                      "sell_number90": ["sell_number90", "stock_report_number"],
                                      "csd_forward_pe_deviation5": ["forward_pe_deviation5", "con_stock_deviation3"],
                                      "csd_forward_pe_deviation75": ["forward_pe_deviation75", "con_stock_deviation3"],
                                      "csd_forward_pb_deviation25": ["forward_pb_deviation25", "con_stock_deviation3"],
                                      "relative_report_number25": ["relative_report_number25", "stock_concern_level"],
                                      "organ_number25": ["organ_number25", "stock_concern_level"],
                                      "organ_number75": ["organ_number75", "stock_concern_level"],
                                      "cfs_target_price_type": ["target_price_type", "con_forecast_schedule"],
                                      "cfs_score": ["score", "con_forecast_schedule"],
                                      "cfs_target_price": ["target_price", "con_forecast_schedule"],
                                      "cfs_score_type": ["score_type", "con_forecast_schedule"],
                                      "rating_up_number30": ["rating_up_number30", "stock_report_adjustment2"],
                                      "rating_up_number90": ["rating_up_number90", "stock_report_adjustment2"],
                                      "rating_down_number90": ["rating_down_number90", "stock_report_adjustment2"],
                                      "report_number7": ["report_number7", "stock_report_number"],
                                      "report_number90": ["report_number90", "stock_report_number"],
                                      "author_number30": ["author_number30", "stock_report_number"],
                                      "organ_number7": ["organ_number7", "stock_report_number"],
                                      "organ_number90": ["organ_number90", "stock_report_number"],
                                      "buy_number30": ["buy_number30", "stock_report_number"],
                                      "overweight_number7": ["overweight_number7", "stock_report_number"],
                                      "overweight_number90": ["overweight_number90", "stock_report_number"],
                                      "neutral_number30": ["neutral_number30", "stock_report_number"],
                                      "neutral_number90": ["neutral_number90", "stock_report_number"],
                                      "underweight_number90": ["underweight_number90", "stock_report_number"],
                                      "sell_number7": ["sell_number7", "stock_report_number"],
                                      "csd_forward_pe_deviation25": ["forward_pe_deviation25", "con_stock_deviation3"],
                                      "csd_forward_pb_deviation5": ["forward_pb_deviation5", "con_stock_deviation3"],
                                      "csd_forward_pb_deviation75": ["forward_pb_deviation75", "con_stock_deviation3"],
                                      "relative_report_number10": ["relative_report_number10", "stock_concern_level"],
                                      "relative_report_number75": ["relative_report_number75", "stock_concern_level"],
                                      "organ_number10": ["organ_number10", "stock_concern_level"],
                                      "cfc2s_tdate": ["tdate", "con_forecast_c2_stk"],
                                      "cfc2s_c9": ["c9", "con_forecast_c2_stk"],
                                      "cfc2i_c13": ["c13", "con_forecast_c2_idx"],
                                      "cfc2sw_tdate": ["tdate", "con_forecast_c2_sw"],
                                      "cfc2gics_tdate": ["tdate", "con_forecast_c2_gics"],
                                      "cfc2gics_c9": ["c9", "con_forecast_c2_gics"],
                                      "cfc2zx_c13": ["c13", "con_forecast_c2_zx"],
                                      "cfc3s_cgb": ["cgb", "con_forecast_c3_stk"],
                                      "cfc3s_cgg": ["cgg", "con_forecast_c3_stk"],
                                      "cfc3sw_cgb": ["cgb", "con_forecast_c3_sw"],
                                      "cfc3sw_cgg": ["cgg", "con_forecast_c3_sw"],
                                      "cfc3gics_cgb": ["cgb", "con_forecast_c3_gics"],
                                      "cfc3gics_cgpeg": ["cgpeg", "con_forecast_c3_gics"],
                                      "cfc3zx_cgpb": ["cgpb", "con_forecast_c3_zx"],
                                      "cfc3zx_cgpeg": ["cgpeg", "con_forecast_c3_zx"],
                                      "cfc3cs_cgb": ["cgb", "con_forecast_c3_cgb_stk"],
                                      "cfc3ci_tdate": ["tdate", "con_forecast_c3_cgb_idx"],
                                      "cfc3ci_cgpb": ["cgpb", "con_forecast_c3_cgb_idx"],
                                      "cfc3csw_cgb": ["cgb", "con_forecast_c3_cgb_sw"],
                                      "cfc3cg_cgpb": ["cgpb", "con_forecast_c3_cgb_gics"],
                                      "cfc2s_c2": ["c2", "con_forecast_c2_stk"],
                                      "cfc2s_c13": ["c13", "con_forecast_c2_stk"],
                                      "cfc2i_tdate": ["tdate", "con_forecast_c2_idx"],
                                      "cfc2i_c9": ["c9", "con_forecast_c2_idx"],
                                      "cfc2sw_c13": ["c13", "con_forecast_c2_sw"],
                                      "cfc2sw_c9": ["c9", "con_forecast_c2_sw"],
                                      "cfc2gics_c13": ["c13", "con_forecast_c2_gics"],
                                      "cfc2zx_tdate": ["tdate", "con_forecast_c2_zx"],
                                      "cfc2zx_c9": ["c9", "con_forecast_c2_zx"],
                                      "cfc3s_tdate": ["tdate", "con_forecast_c3_stk"],
                                      "cfc3s_cgpb": ["cgpb", "con_forecast_c3_stk"],
                                      "cfc3s_cgpeg": ["cgpeg", "con_forecast_c3_stk"],
                                      "cfc3sw_tdate": ["tdate", "con_forecast_c3_sw"],
                                      "cfc3sw_cgpb": ["cgpb", "con_forecast_c3_sw"],
                                      "cfc3sw_cgpeg": ["cgpeg", "con_forecast_c3_sw"],
                                      "cfc3gics_tdate": ["tdate", "con_forecast_c3_gics"],
                                      "cfc3gics_cgpb": ["cgpb", "con_forecast_c3_gics"],
                                      "cfc3gics_cgg": ["cgg", "con_forecast_c3_gics"],
                                      "cfc3zx_tdate": ["tdate", "con_forecast_c3_zx"],
                                      "cfc3zx_cgb": ["cgb", "con_forecast_c3_zx"],
                                      "cfc3zx_cgg": ["cgg", "con_forecast_c3_zx"],
                                      "cfc3cs_tdate": ["tdate", "con_forecast_c3_cgb_stk"],
                                      "cfc3cs_cgpb": ["cgpb", "con_forecast_c3_cgb_stk"],
                                      "cfc3ci_cgb": ["cgb", "con_forecast_c3_cgb_idx"],
                                      "cfc3csw_tdate": ["tdate", "con_forecast_c3_cgb_sw"],
                                      "cfc3csw_cgpb": ["cgpb", "con_forecast_c3_cgb_sw"],
                                      "cfc3cg_tdate": ["tdate", "con_forecast_c3_cgb_gics"],
                                      "cfc3cg_cgb": ["cgb", "con_forecast_c3_cgb_gics"],
                                      "up_number90": ["up_number90", "stock_report_adjustment"],
                                      "down_number30": ["down_number30", "stock_report_adjustment"],
                                      "eps_deviation5": ["eps_deviation5", "con_stock_deviation"],
                                      "eps_deviation75": ["eps_deviation75", "con_stock_deviation"],
                                      "ni_deviation25": ["ni_deviation25", "con_stock_deviation"],
                                      "eps_stdev25": ["eps_stdev25", "con_stock_deviation"],
                                      "ni_stdev25": ["ni_stdev25", "con_stock_deviation"],
                                      "csd_pe_deviation5": ["pe_deviation5", "con_stock_deviation2"],
                                      "csd_pb_deviation5": ["pb_deviation5", "con_stock_deviation2"],
                                      "consensus_confidence10": [" consensus_confidence10", "stock_emotion"],
                                      "consensus_confidence25": [" consensus_confidence25", "stock_emotion"],
                                      "optimism_confidence5": [" optimism_confidence5", "stock_emotion"],
                                      "optimism_confidence15": [" optimism_confidence15", "stock_emotion"],
                                      "pessimism_confidence5": [" pessimism_confidence5", "stock_emotion"],
                                      "pessimism_confidence15": [" pessimism_confidence15", "stock_emotion"],
                                      "pessimism_confidence75": [" pessimism_confidence75", "stock_emotion"],
                                      "eps_stdev5": ["eps_stdev5", "con_stock_deviation"],
                                      "ni_stdev75": ["ni_stdev75", "con_stock_deviation"],
                                      "csd_pb_deviation75": ["pb_deviation75", "con_stock_deviation2"],
                                      "up_number7": ["up_number7", "stock_report_adjustment"],
                                      "up_number30": ["up_number30", "stock_report_adjustment"],
                                      "down_number7": ["down_number7", "stock_report_adjustment"],
                                      "down_number90": ["down_number90", "stock_report_adjustment"],
                                      "eps_deviation25": ["eps_deviation25", "con_stock_deviation"],
                                      "ni_deviation5": ["ni_deviation5", "con_stock_deviation"],
                                      "ni_deviation75": ["ni_deviation75", "con_stock_deviation"],
                                      "eps_stdev75": ["eps_stdev75", "con_stock_deviation"],
                                      "ni_stdev5": ["ni_stdev5", "con_stock_deviation"],
                                      "csd_pe_deviation25": ["pe_deviation25", "con_stock_deviation2"],
                                      "csd_pe_deviation75": ["pe_deviation75", "con_stock_deviation2"],
                                      "csd_pb_deviation25": ["pb_deviation25", "con_stock_deviation2"],
                                      "degree": ["degree", "STOCK_DIVERSITY"],
                                      "consensus_confidence5": [" consensus_confidence5", "stock_emotion"],
                                      "consensus_confidence15": [" consensus_confidence15", "stock_emotion"],
                                      "consensus_confidence75": [" consensus_confidence75", "stock_emotion"],
                                      "optimism_confidence10": [" optimism_confidence10", "stock_emotion"],
                                      "optimism_confidence25": [" optimism_confidence25", "stock_emotion"],
                                      "optimism_confidence75": [" optimism_confidence75", "stock_emotion"],
                                      "pessimism_confidence10": [" pessimism_confidence10", "stock_emotion"],
                                      "pessimism_confidence25": [" pessimism_confidence25", "stock_emotion"],
                                      "cfs_c1": ["c1", "con_forecast_stk"], "cfs_c4": ["c4", "con_forecast_stk"],
                                      "cfs_c7": ["c7", "con_forecast_stk"], "cfs_c82": ["c82", "con_forecast_stk"],
                                      "cfs_c84": ["c84", "con_forecast_stk"],
                                      "cfi_tdate": ["tdate", "con_forecast_idx"], "cfi_c1": ["c1", "con_forecast_idx"],
                                      "cfi_c6": ["c6", "con_forecast_idx"], "cfi_c12": ["c12", "CON_FORECAST_IDX"],
                                      "cfi_cpb": ["cpb", "con_forecast_idx"], "cfsw_c3": ["c3", "con_forecast_sw"],
                                      "cfsw_c6": ["c6", "con_forecast_sw"], "cfsw_cb": ["cb", "con_forecast_sw"],
                                      "cfgics_tdate": ["tdate", "con_forecast_gics"],
                                      "cfgics_c3": ["c3", "con_forecast_gics"],
                                      "cfgics_c5": ["c5", "con_forecast_gics"],
                                      "cfgics_c12": ["c12", "con_forecast_gics"],
                                      "cfgics_cpb": ["cpb", "con_forecast_gics"],
                                      "cfzx_c4_type": ["c4_type", "con_forecast_zx"],
                                      "cfzx_c4": ["c4", "con_forecast_zx"], "cfzx_c6": ["c6", "con_forecast_zx"],
                                      "cfzx_cb": ["cb", "con_forecast_zx"], "cfcbs_cb": ["cb", "con_forecast_cb_stk"],
                                      "cfcbi_cpb": ["cpb", "con_forecast_cb_idx"],
                                      "cfcbsw_cb": ["cb", "CON_FORECAST_CB_SW"],
                                      "cfcbgics_cb": ["cb", "con_forecast_cb_gics"], "cpi_pei": ["pei", "con_per_idx"],
                                      "cps_pei": ["pei", "con_per_sw"], "cfs_c80": ["c80", "con_forecast_stk"],
                                      "cfs_cpb": ["cpb", "con_forecast_stk"], "cfi_c5": ["c5", "con_forecast_idx"],
                                      "cfsw_tdate": ["tdate", "con_forecast_sw"],
                                      "cpg_rpt_date": ["rpt_date", "con_per_gics"],
                                      "cfsw_c1": ["c1", "con_forecast_sw"], "cfsw_c4": ["c4", "con_forecast_sw"],
                                      "cfsw_c5": ["c5", "con_forecast_sw"], "cfsw_c7": ["c7", "con_forecast_sw"],
                                      "cfsw_cpb": ["cPB", "CON_FORECAST_SW"],
                                      "cfgics_c4_type": ["c4_type", "con_forecast_gics"],
                                      "cfgics_c1": ["c1", "con_forecast_gics"],
                                      "cfgics_c4": ["c4", "con_forecast_gics"],
                                      "cfgics_c6": ["c6", "con_forecast_gics"],
                                      "cfgics_c7": ["c7", "con_forecast_gics"],
                                      "cfgics_cb": ["cb", "con_forecast_gics"],
                                      "cfzx_tdate": ["tdate", "con_forecast_zx"], "cfzx_c1": ["c1", "CON_FORECAST_ZX"],
                                      "cfzx_c3": ["c3", "con_forecast_zx"], "cfzx_c5": ["c5", "con_forecast_zx"],
                                      "cfzx_c7": ["c7", "con_forecast_zx"], "cfzx_c12": ["c12", "con_forecast_zx"],
                                      "cfzx_cpb": ["cpb", "con_forecast_zx"],
                                      "cpi_rpt_date": ["rpt_date", "con_per_idx"],
                                      "cps_rpt_date": ["rpt_date", "con_per_sw"], "cpg_pei": ["pei", "con_per_gics"],
                                      "cfcbs_tdate": ["tdate", "con_forecast_cb_stk"],
                                      "cfcbs_cpb": ["cpb", "con_forecast_cb_stk"],
                                      "cfcbi_tdate": ["tdate", "con_forecast_cb_idx"],
                                      "cfcbi_cb": ["cb", "con_forecast_cb_idx"],
                                      "cfcbsw_tdate": ["TDATE", "CON_FORECAST_CB_SW"],
                                      "cfcbsw_cpb": ["cpb", "con_forecast_cb_sw"],
                                      "cfcbgics_tdate": ["tdate", "con_forecast_cb_gics"],
                                      "cfcbgics_cpb": ["cpb", "con_forecast_cb_gics"],
                                      "cfs_tdate": ["tdate", "con_forecast_stk"],
                                      "cfs_c4_type": ["c4_type", "con_forecast_stk"],
                                      "cfs_c3": ["c3", "con_forecast_stk"], "cfs_c5": ["c5", "con_forecast_stk"],
                                      "cfs_c6": ["c6", "con_forecast_stk"], "cfs_c81": ["c81", "con_forecast_stk"],
                                      "cfs_c83": ["c83", "con_forecast_stk"], "cfs_c12": ["c12", "con_forecast_stk"],
                                      "cfs_cb": ["cb", "con_forecast_stk"],
                                      "cfi_c4_type": ["c4_type", "con_forecast_idx"],
                                      "cfi_c3": ["c3", "con_forecast_idx"], "cfi_c4": ["c4", "con_forecast_idx"],
                                      "cfi_c7": ["c7", "con_forecast_idx"], "cfi_cb": ["cb", "con_forecast_idx"],
                                      "cfsw_c4_type": ["c4_type", "con_forecast_sw"],
                                      "forward_pe_deviation5": ["forward_pe_deviation5", "block_deviation3"],
                                      "forward_pb_deviation5": ["forward_pb_deviation5", "block_deviation3"],
                                      "forward_pb_deviation25": ["forward_pb_deviation25", "block_deviation3"],
                                      "forward_pe_deviation25": ["forward_pe_deviation25", "block_deviation3"],
                                      "forward_pe_deviation75": ["forward_pe_deviation75", "block_deviation3"],
                                      "forward_pb_deviation75": ["forward_pb_deviation75", "block_deviation3"],
                                      "pe_deviation75": ["pe_deviation75", "block_deviation2"],
                                      "pb_deviation25": ["pb_deviation25", "block_deviation2"],
                                      "pe_deviation5": ["pe_deviation5", "block_deviation2"],
                                      "pe_deviation25": ["pe_deviation25", "block_deviation2"],
                                      "pb_deviation5": ["pb_deviation5", "block_deviation2"],
                                      "pb_deviation75": ["pb_deviation75", "block_deviation2"],
                                      "diversity": ["diversity", "block_diversity"]},
                      "table_index": {"con_forecast_schedule": "stock_code as tradingcode,tdate,",
                                      "stock_report_number": "stock_code as tradingcode,tdate,",
                                      "con_stock_deviation3": "stock_code as tradingcode,tdate,",
                                      "stock_concern_level": "stock_code as tradingcode,tdate,",
                                      "stock_report_adjustment2": "stock_code as tradingcode,tdate,",
                                      "con_forecast_c2_idx": "stock_code as tradingcode,stock_type,tdate,",
                                      "con_forecast_c3_cgb_stk": "stock_code as tradingcode,stock_type,tdate,",
                                      "con_forecast_c2_zx": "stock_code as tradingcode,stock_type,tdate,",
                                      "con_forecast_c3_cgb_gics": "stock_code as tradingcode,stock_type,tdate,",
                                      "con_forecast_c3_stk": "stock_code as tradingcode,stock_type,tdate,",
                                      "con_forecast_c3_cgb_idx": "stock_code as tradingcode,stock_type,tdate,",
                                      "con_forecast_c2_gics": "stock_code as tradingcode,stock_type,tdate,",
                                      "con_forecast_c3_gics": "stock_code as tradingcode,stock_type,tdate,",
                                      "con_forecast_c2_stk": "stock_code as tradingcode,stock_type,tdate,",
                                      "con_forecast_c3_sw": "stock_code as tradingcode,stock_type,tdate,",
                                      "con_forecast_c2_sw": "stock_code as tradingcode,stock_type,tdate,",
                                      "con_forecast_c3_cgb_sw": "stock_code as tradingcode,stock_type,tdate,",
                                      "con_forecast_c3_zx": "stock_code as tradingcode,stock_type,tdate,",
                                      "STOCK_DIVERSITY": "stock_code as tradingcode,tdate,rpt_date,",
                                      "stock_report_adjustment": "stock_code as tradingcode,tdate,rpt_date,",
                                      "con_stock_deviation2": "stock_code as tradingcode,tdate,rpt_date,",
                                      "stock_emotion": "stock_code as tradingcode,tdate,rpt_date,",
                                      "con_stock_deviation": "stock_code as tradingcode,tdate,rpt_date,",
                                      "con_forecast_cb_sw": "stock_code as tradingcode,stock_type,tdate,rpt_date,",
                                      "con_forecast_sw": "stock_code as tradingcode,stock_type,tdate,rpt_date,",
                                      "CON_FORECAST_ZX": "stock_code as tradingcode,stock_type,tdate,rpt_date,",
                                      "con_per_gics": "stock_code as tradingcode,stock_type,tdate,rpt_date,",
                                      "con_per_sw": "stock_code as tradingcode,stock_type,tdate,rpt_date,",
                                      "con_per_idx": "stock_code as tradingcode,stock_type,tdate,rpt_date,",
                                      "CON_FORECAST_SW": "stock_code as tradingcode,stock_type,tdate,rpt_date,",
                                      "CON_FORECAST_IDX": "stock_code as tradingcode,stock_type,tdate,rpt_date,",
                                      "con_forecast_stk": "stock_code as tradingcode,stock_type,tdate,rpt_date,",
                                      "con_forecast_gics": "stock_code as tradingcode,stock_type,tdate,rpt_date,",
                                      "con_forecast_idx": "stock_code as tradingcode,stock_type,tdate,rpt_date,",
                                      "con_forecast_zx": "stock_code as tradingcode,stock_type,tdate,rpt_date,",
                                      "con_forecast_cb_stk": "stock_code as tradingcode,stock_type,tdate,rpt_date,",
                                      "CON_FORECAST_CB_SW": "stock_code as tradingcode,stock_type,tdate,rpt_date,",
                                      "con_forecast_cb_idx": "stock_code as tradingcode,stock_type,tdate,rpt_date,",
                                      "con_forecast_cb_gics": "stock_code as tradingcode,stock_type,tdate,rpt_date,",
                                      "block_deviation3": "block_code as tradingcode,block_type,tdate,",
                                      "block_diversity": "block_code as tradingcode,block_type,tdate,rpt_date,",
                                      "block_deviation2": "block_code as tradingcode,block_type,tdate,rpt_date,"}
                      }

table_map_factors = {
    "eps_basic": ["factor_vip_financialanalysis_part1", "rptDate"],  # 每股收益EPS-基本 currencyType原始币种
    "roe_basic": ["factor_vip_financialanalysis_part1", "rptDate"],  # 净资产收益率ROE(加权)
    "roa2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 总资产报酬率ROA
    "roa": ["factor_vip_financialanalysis_part1", "rptDate"],  # 总资产净利率ROA
    "roic": ["factor_vip_financialanalysis_part1", "rptDate"],  # 投入资本回报率ROIC
    "grossprofitmargin": ["factor_vip_financialanalysis_part1", "rptDate"],  # 销售毛利率
    "optoebt": ["factor_vip_financialanalysis_part1", "rptDate"],  # 主营业务比率
    "profittogr": ["factor_vip_financialanalysis_part1", "rptDate"],  # 净利润/营业总收入
    "optogr": ["factor_vip_financialanalysis_part1", "rptDate"],  # 营业利润/营业总收入
    "operateexpensetogr": ["factor_vip_financialanalysis_part1", "rptDate"],  # 销售费用/营业总收入
    "operateincometoebt": ["factor_vip_financialanalysis_part1", "rptDate"],  # 经营活动净收益/利润总额
    "investincometoebt": ["factor_vip_financialanalysis_part1", "rptDate"],  # 价值变动净收益/利润总额
    "nonoperateprofittoebt": ["factor_vip_financialanalysis_part1", "rptDate"],  # 营业外收支净额/利润总额
    "ocftosales": ["factor_vip_financialanalysis_part1", "rptDate"],  # 经营性现金净流量/营业总收入
    "debttoassets": ["factor_vip_financialanalysis_part1", "rptDate"],  # 资产负债率
    "assetstoequity": ["factor_vip_financialanalysis_part1", "rptDate"],  # 权益乘数
    "catoassets": ["factor_vip_financialanalysis_part1", "rptDate"],  # 流动资产／总资产
    "intdebttototalcap": ["factor_vip_financialanalysis_part1", "rptDate"],  # 带息负债／全部投入资本
    "currentdebttodebt": ["factor_vip_financialanalysis_part1", "rptDate"],  # 流动负债／负债合计
    "current": ["factor_vip_financialanalysis_part1", "rptDate"],  # 流动比率
    "quick": ["factor_vip_financialanalysis_part1", "rptDate"],  # 速动比率
    "ocftodebt": ["factor_vip_financialanalysis_part1", "rptDate"],  # 经营活动产生的现金流量净额／负债合计
    "invturn": ["factor_vip_financialanalysis_part1", "rptDate"],  # 存货周转率
    "arturn": ["factor_vip_financialanalysis_part1", "rptDate"],  # 应收账款周转率
    "caturn": ["factor_vip_financialanalysis_part1", "rptDate"],  # 流动资产周转率
    "faturn": ["factor_vip_financialanalysis_part1", "rptDate"],  # 固定资产周转率
    "assetsturn1": ["factor_vip_financialanalysis_part1", "rptDate"],  # 总资产周转率
    "roe_ttm2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 净资产收益率(TTM)
    "roa2_ttm2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 总资产报酬率(TTM)
    "netprofittoassets": ["factor_vip_financialanalysis_part1", "rptDate"],  # 总资产净利率-不含少数股东损益(TTM)
    "roic_ttm2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 投入资本回报率ROIC(TTM)
    "netprofitmargin_ttm2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 销售净利率(TTM)
    "grossprofitmargin_ttm2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 销售毛利率(TTM)
    "profittogr_ttm2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 净利润(TTM)／营业总收入(TTM)
    "optogr_ttm2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 营业利润(TTM)／营业总收入(TTM)
    "gctogr_ttm2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 营业总成本(TTM)／营业总收入(TTM)
    "netprofittoor_ttm": ["factor_vip_financialanalysis_part1", "rptDate"],  # 归属母公司股东的净利润（TTM)/营业收入(TTM)
    "operateincometoebt_ttm2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 经营活动净收益(TTM)／利润总额(TTM)
    "ebttoor_ttm": ["factor_vip_financialanalysis_part1", "rptDate"],  # 利润总额(TTM)/营业收入(TTM)
    "ocftoor_ttm2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 经营活动产生的现金流量净额(TTM)／营业收入(TTM)
    "gr_ttm2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 营业总收入(TTM)  单位：元
    "gc_ttm2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 营业总成本(TTM)    单位：元
    "grossmargin_ttm2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 毛利(TTM)     单位：元
    "interestexpense_ttm": ["factor_vip_financialanalysis_part1", "rptDate"],  # 利息支出(TTM)     单位：元
    "profit_ttm2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 净利润(TTM)        单位：元
    "operatecashflow_ttm2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 经营活动现金静流量(TTM)        单位：元
    "cashflow_ttm2": ["factor_vip_financialanalysis_part1", "rptDate"],  # 现金净流量(TTM)   单位：元

    "fcff": ["factor_vip_financialanalysis_part2", "rptDate"],  # 企业自由现金流量FCFF       单位：元
    "fcfe": ["factor_vip_financialanalysis_part2", "rptDate"],  # 股权自由现金流量FCFE          单位：元
    "qfa_operateincome": ["factor_vip_financialanalysis_part2", "rptDate"],  # 单季度.经营活动净收益  单位：元
    "qfa_roe": ["factor_vip_financialanalysis_part2", "rptDate"],  # 单季度.净资产收益率ROE
    "qfa_roa": ["factor_vip_financialanalysis_part2", "rptDate"],  # 单季度.总资产净利率ROA
    "qfa_netprofitmargin": ["factor_vip_financialanalysis_part2", "rptDate"],  # 单季度.销售净利率
    "qfa_grossprofitmargin": ["factor_vip_financialanalysis_part2", "rptDate"],  # 单季度.销售毛利率
    "qfa_profittogr": ["factor_vip_financialanalysis_part2", "rptDate"],  # 单季度.净利润/营业总收入
    "qfa_operateincometoebt": ["factor_vip_financialanalysis_part2", "rptDate"],  # 单季度.经营活动净收益/利润总额
    "qfa_ocftosales": ["factor_vip_financialanalysis_part2", "rptDate"],  # 单季度.经营活动产生的现金流量净额/营业收入
    "qfa_ocftoor": ["factor_vip_financialanalysis_part2", "rptDate"],  # 单季度.经营活动产生的现金流量净额/经营活动净收益
    "qfa_yoygr": ["factor_vip_financialanalysis_part2", "rptDate"],  # 单季度.营业总收入同比增长率
    "qfa_yoysales": ["factor_vip_financialanalysis_part2", "rptDate"],  # 单季度.营业收入同比增长率
    "qfa_yoyop": ["factor_vip_financialanalysis_part2", "rptDate"],  # 单季度.营业利润同比增长率
    "qfa_yoyprofit": ["factor_vip_financialanalysis_part2", "rptDate"],  # 单季度.净利润同比增长率
    "yoy_equity": ["factor_vip_financialanalysis_part2", "rptDate"],  # 净资产(同比增长率)
    "yoy_tr": ["factor_vip_financialanalysis_part2", "rptDate"],  # 营业总收入(同比增长率)
    "yoycf": ["factor_vip_financialanalysis_part2", "rptDate"],  # 现金净流量(同比增长率)
    "yoyeps_basic": ["factor_vip_financialanalysis_part2", "rptDate"],  # 基本每股收益(同比增长率)
    "yoynetprofit": ["factor_vip_financialanalysis_part2", "rptDate"],  # 归属母公司股东的净利润(同比增长率)
    "yoyocf": ["factor_vip_financialanalysis_part2", "rptDate"],  # 经营活动产生的现金流量净额(同比增长率)
    "yoyocfps": ["factor_vip_financialanalysis_part2", "rptDate"],  # 每股经营活动产生的现金流量净额(同比增长率)
    "yoyop": ["factor_vip_financialanalysis_part2", "rptDate"],  # 营业利润(同比增长率)
    "yoyroe": ["factor_vip_financialanalysis_part2", "rptDate"],  # 净资产收益率(摊薄)(同比增长率)
    "stm_issuingdate": ["factor_vip_financialanalysis_part2", "rptDate"],  # 定期报告披露日期
    "yoyprofit": ["factor_vip_financialanalysis_part2", "rptDate"],  # 净利润(同比增长率)
    "ebitdatosales": ["factor_vip_financialanalysis_part2", "rptDate"],  # EBITDA（反推法）/营业总收入
    "ocftocf": ["factor_vip_financialanalysis_part2", "rptDate"],  # 经营活动产生的现金流量净额占比
    "fcftocf": ["factor_vip_financialanalysis_part2", "rptDate"],  # 筹资活动产生的现金流量净额占比
    "ocftoop": ["factor_vip_financialanalysis_part2", "rptDate"],  # 现金营运指数
    "ocftoassets": ["factor_vip_financialanalysis_part2", "rptDate"],  # 全部资产现金回收率
    "longdebttolongcaptial": ["factor_vip_financialanalysis_part2", "rptDate"],  # 长期资本负债率
    "longcapitaltoinvestment": ["factor_vip_financialanalysis_part2", "rptDate"],  # 长期资产适合率
    "currentdebttoequity": ["factor_vip_financialanalysis_part2", "rptDate"],  # 流动负债权益比率
    "ncatoequity": ["factor_vip_financialanalysis_part2", "rptDate"],  # 资本固定化比率
    "longdebttodebt": ["factor_vip_financialanalysis_part2", "rptDate"],  # 长期负债占比
    "operatecaptialturn": ["factor_vip_financialanalysis_part2", "rptDate"],  # 营运资本周转率
    "apturn": ["factor_vip_financialanalysis_part2", "rptDate"],  # 应付账款周转率
    "ebittoassets2": ["factor_vip_financialanalysis_part2", "rptDate"],  # 息税前利润(TTM)/总资产
    "qfa_yoyeps": ["factor_vip_financialanalysis_part2", "rptDate"],  # 单季度.每股收益(同比增长率)
    "yoy_assets": ["factor_vip_financialanalysis_part2", "rptDate"],  # 总资产(同比增长率)
    "yoy_cash": ["factor_vip_financialanalysis_part2", "rptDate"],  # 货币资金增长率
    "yoy_fixedassets": ["factor_vip_financialanalysis_part2", "rptDate"],  # 固定资产投资扩张率
    "yoydebt": ["factor_vip_financialanalysis_part2", "rptDate"],  # 总负债(同比增长率)
    "ocftodividend": ["factor_vip_financialanalysis_part2", "rptDate"],  # 现金股利保障倍数
    "ocftointerest": ["factor_vip_financialanalysis_part2", "rptDate"],  # 现金流量利息保障倍数
    "stmnote_salestop5_pct": ["factor_vip_financialanalysis_part2", "rptDate"],

    "tot_assets": ["factor_vip_financialanalysis_part3", "rptDate", "statement_type"],  # 资产总计  单位：元
    "tot_liab": ["factor_vip_financialanalysis_part3", "rptDate", "statement_type"],  # 负债合计  单位：元
    "tot_non_cur_liab": ["factor_vip_financialanalysis_part3", "rptDate", "statement_type"],  # 非流动负债合计  单位：元
    "tot_equity": ["factor_vip_financialanalysis_part3", "rptDate", "statement_type"],  # 所有者权益合计  单位：元
    "cashtostdebt": ["factor_vip_financialanalysis_part3", "rptDate", "statement_type"],  # 货币资金/短期债务
    "qfa_grossmargin": ["factor_vip_financialanalysis_part3", "rptDate", "statement_type"],  # 单季度.毛利  单位：元
    "acctandnotes_payable": ["factor_vip_financialanalysis_part3", "rptDate", "statement_type"],  # 应付票据及应付账款  单位：元
    "acctandnotes_rcv": ["factor_vip_financialanalysis_part3", "rptDate", "statement_type"],  # 应收票据及应收账款  单位：元

    "fa_retainedearn_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 留存盈余比率(TTM)
    "fa_roc_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 资本报酬率(TTM)
    "fa_protocost_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 成本费用利润率(TTM)
    "fa_ebittogr_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 息税前利润/营业总收入(TTM)
    "fa_taxratio_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 销售税金率(TTM)
    "fa_acca_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 现金流资产比-资产回报率(TTM)
    "fa_berryratio_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 贝里比率(TTM)
    "fa_cashrecovratio_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 资金现金回收率(TTM)
    "fa_ltdebttoasset": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 长期负债/资产总计
    "fa_equitytofixedasset": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 股东权益/固定资产
    "fa_intangassetratio": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 无形资产比率
    "fa_debttotangibleafybl": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 有形净值债务率
    "fa_ocftointerestdebt_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 经营活动产生现金流量净额/带息债务(TTM)
    "fa_ocftonetdebt_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 经营活动产生现金流量净额/净债务(TTM)
    "fa_cfotocurliabs_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 现金流动负债比(TTM)
    "fa_faturn_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 固定资产周转率(TTM)
    "fa_invturn_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 存货周转率(TTM)
    "fa_currtassetstrate_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 流动资产周转率(TTM)
    "fa_naturn_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 净资产周转率(TTM)
    "fa_ncgr_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 增长率-净现金流量(TTM)
    "fa_tpgr_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 增长率-利润总额(TTM)
    "fa_oigr_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 增长率-营业利润(TTM)
    "fa_nppcgr_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 增长率-归属母公司股东的净利润(TTM)
    "fa_cfogr_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 增长率-经营活动产生的现金流量净额(TTM)
    "fa_cffgr_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 增长率-筹资活动产生的现金流量净额(TTM)
    "fa_cfigr_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 增长率-投资活动产生的现金流量净额(TTM)
    "fa_gpmgr_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 增长率-毛利率(TTM)
    "pcf_ncf_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 市现率PCF(现金净流量TTM)
    "val_ortoev_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 营业收入(TTM)/企业价值
    "val_tatoev": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 资产总计/企业价值
    "val_mvtofcff": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 市值/企业自由现金流
    "dividendyield2": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 股息率(近12个月)
    "pe_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 市盈率PE(TTM)
    "pb_lf": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 市净率PB(LF,内地)
    "pcf_ocf_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 市现率PCF(经营现金流TTM)
    "ps_ttm": ["factor_vip_financialanalysis_part4", "tradeDate"],  # 市销率PS(TTM)
    "share_pledgeda_pct_holder": ["factor_vip_financialanalysis_part4", "tradeDate"],
    "pre_close": ["factor_vip_financialanalysis_part4", "tradeDate"],
    "adjfactor": ["factor_vip_financialanalysis_part4", "tradeDate"],

    'eps_diluted': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'eps_diluted2': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'eps_adjust': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'eps_exbasic': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'eps_exdiluted': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'eps_exdiluted2': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'bps': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'bps_adjust': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ocfps': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'grps': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'orps': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'surpluscapitalps': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'surplusreserveps': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'undistributedps': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'retainedps': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'cfps': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ebitps': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'fcffps': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'fcfeps': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ebitdaps': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'roe_avg': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'roe_diluted': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'roe_deducted': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'roe_exbasic': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'roe_exdiluted': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'roe_add': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ebittointerest': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'roe_yearly': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'roa2_yearly': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'roa_yearly': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'netprofitmargin': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'cogstosales': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'nptocostexpense': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'expensetosales': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ebittogr': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'gctogr': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'adminexpensetogr': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'finaexpensetogr': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'impairtogr': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'netdebttoev': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'taxtoebt': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ocftonetdebt': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'salescashintoor': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ocftoor': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ocftooperateincome': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'capitalizedtoda': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'icftocf': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ocftoinveststockdividend': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'deducteddebttoassets': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'deducteddebttoassets2': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ocficftocurrentdebt': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ncatoassets': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'longdebttoequity': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'tangibleassetstoassets': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ocficftodebt': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'cashratio': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'cashtocurrentdebt': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ocftoquickdebt': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'debttoequity': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'fa_debttoeqy': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'equitytodebt': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'equitytointerestdebt': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'tangibleassettodebt': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'tangassettointdebt': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'tangibleassettonetdebt': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'debttotangibleequity': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ebitdatodebt': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ocftointerestdebt': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ocftoshortdebt': ['factor_vip_financialanalysis_part5', 'rptDate'],
    'ocftolongdebt': ['factor_vip_financialanalysis_part5', 'rptDate']

}

table_map_factors_us = {
    "close": ["factor_vip_us_market", "tradeDate"],  # 美股因子
    "adjfactor": ["factor_vip_us_market", "tradeDate"],  # 美股因子
    "industry": ["factor_vip_us_market", "tradeDate"],  # 美股因子
}

table_map_factors_commodity = {
    "close": ["factor_vip_commodity", "tradeDate"],
}