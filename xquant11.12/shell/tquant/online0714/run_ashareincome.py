# -*- coding: utf-8 -*-

from data_clean import base_data_clean, Kafka_producer
import pandas as pd
import time
import sys
sys.path.append("/app/tools")
from gaya_factor.utils import get_sql_script

pd.set_option('display.max_columns', None)


class data_clean(base_data_clean):
    def __init__(self, date, library_name, library_id, field, env_id, cloud_env):
        super().__init__(env_id, cloud_env)
        self.date = date
        self.library_name = library_name
        self.library_id = library_id
        self.field = field

    def calculation(self, df, td):
        pass


def main(need_merge=True):
    from setEnv import env_id, cloud_env
    # 日期有页面传入-----
    try:
        date = sys.argv[1]
    except:
        date = "20181231"
    # 表名要修改----
    library_name = "factor_d_financialreportindex"
    library_id = 1
    # 因子要修改-----
    field = ["actual_ann_dt_p", "tot_oper_rev", "int_inc", "net_int_inc", "insur_prem_unearned",
             "handling_chrg_comm_inc", "net_handling_chrg_comm_inc", "net_inc_other_ops", "plus_net_inc_other_bus",
             "prem_inc", "less_ceded_out_prem", "chg_unearned_prem_res", "incl_reinsurance_prem_inc",
             "net_inc_sec_trading_brok_bus", "net_inc_sec_uw_bus", "net_inc_ec_asset_mgmt_bus", "other_bus_inc",
             "plus_net_gain_chg_fv", "plus_net_invest_inc", "incl_inc_invest_assoc_jv_entp", "plus_net_gain_fx_trans",
             "tot_oper_cost", "less_oper_cost", "less_int_exp", "less_handling_chrg_comm_exp",
             "less_taxes_surcharges_ops", "less_selling_dist_exp", "less_gerl_admin_exp", "less_fin_exp",
             "less_impair_loss_assets", "prepay_surr", "tot_claim_exp", "chg_insur_cont_rsrv", "dvd_exp_insured",
             "reinsurance_exp", "oper_exp", "less_claim_recb_reinsurer", "less_ins_rsrv_recb_reinsurer",
             "less_exp_recb_reinsurer", "other_bus_cost", "oper_profit", "plus_non_oper_rev", "less_non_oper_exp",
             "il_net_loss_disp_noncur_asset", "tot_profit", "inc_tax", "net_profit_incl_min_int_inc",
             "net_profit_excl_min_int_inc", "minority_int_inc", "other_compreh_inc", "tot_compreh_inc",
             "tot_compreh_inc_parent_comp", "tot_compreh_inc_min_shrhldr", "ebit", "ebitda",
             "net_profit_after_ded_nr_lp", "net_profit_under_intl_acc_sta", "s_fa_eps_basic", "s_fa_eps_diluted",
             "insurance_expense", "spe_bal_oper_profit", "tot_bal_oper_profit", "spe_bal_tot_profit",
             "tot_bal_tot_profit", "spe_bal_net_profit", "tot_bal_net_profit", "adjlossgain_prevyear",
             "transfer_from_surplusreserve", "transfer_from_housingimprest", "transfer_from_others",
             "distributable_profit", "withdr_legalsurplus", "withdr_legalpubwelfunds", "workers_welfare",
             "withdr_buzexpwelfare", "withdr_reservefund", "distributable_profit_shrhder", "prfshare_dvd_payable",
             "withdr_othersurpreserve", "comshare_dvd_payable", "capitalized_comstock_div", "undistributed_profit_p",
             "oper_rev", "unconfirmed_invest_loss_p", "rdexpense", "stmnote_finexp"]
    env_id = env_id
    cloud_env = cloud_env
    # 解析任务
    dc = data_clean(date, library_name, library_id, field, env_id, cloud_env)
    # 日行情需要改成每日
    # date_list = dc.get_date()
    # 数据清洗
    # 获取df
    # 获取sql语句的DataFrame
    df_sql = get_sql_script(field[0])

    # sql需要修改----
    sql_script = df_sql.loc['A股', 'factor_sql']
    sql = sql_script.format(date)
    df = dc.read_from_cloud(sql)
    dc.logger.info("取数据完毕，开始入库......")
    if need_merge:
        chiname = ["chiname", "exchangecode", "exchangename"]
        dc.field = chiname + field
        df = dc.merge_chiname(['TDATE', 'TRADINGCODE', 'STATEMENT_TYPE'], df)
    dc.run_task(df)
    dc.mysql_close()


if __name__ == '__main__':
    main()
