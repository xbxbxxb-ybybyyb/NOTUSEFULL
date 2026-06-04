import os
os.environ['exec_env'] = ''
from tquant.index_data import IndexData
from tquant.basic_data import BasicData
import pytest
import pandas as pd


class TestIndexData(object):
    """
    测试指数数据接口IndexData
    """
    @classmethod
    def setup_class(cls):
        cls.ind = IndexData()
        cls.bd = BasicData()

    @pytest.mark.parametrize('date_time', ['20210112', '20210330'])
    @pytest.mark.parametrize('plate_id', ['HS300', 'ZZ500', 'SH50', '000300.SH', '000905.SH',
                                          '399001.SZ', '000016.SH', '000002.SH'])
    @pytest.mark.parametrize('weight_type', [None, 0, 1])
    @pytest.mark.parametrize('use_prev_name', [None, True, False])
    @pytest.mark.parametrize('weight', [None, True, False])
    def test_get_index_info(self, date_time, plate_id, weight_type, use_prev_name, weight):
        """
        测试查询指数板块的成分股及成分股的权重
        :param date_time:测试日期
        :param plate_id:指数代码
        :param weight_type:权重
        :return:
        """
        if weight_type == None and use_prev_name == None and weight== None:
            result = self.ind.get_index_info(date_time, plate_id)
        else:
            if weight_type == None and use_prev_name == None:
                result = self.ind.get_index_info(date_time, plate_id, weight=weight)
            elif weight_type == None and weight == None:
                result = self.ind.get_index_info(date_time, plate_id, use_prev_name=use_prev_name)
            elif use_prev_name == None and weight== None:
                result = self.ind.get_index_info(date_time, plate_id, weight_type)
            else:
                if weight_type == None:
                    result = self.ind.get_index_info(date_time, plate_id, use_prev_name=use_prev_name, weight=weight)
                elif use_prev_name == None:
                    result = self.ind.get_index_info(date_time, plate_id, weight_type, weight=weight)
                elif weight== None:
                    result = self.ind.get_index_info(date_time, plate_id, weight_type, use_prev_name=use_prev_name)
                else:
                    result = self.ind.get_index_info(date_time, plate_id, weight_type, use_prev_name=use_prev_name, weight=weight)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @pytest.mark.parametrize('trading_code', ['000300.SH', '000001.SH'])
    @pytest.mark.parametrize('start_datetime, end_datetime', [('20200302 093000000', '20200302 150000250'),
                                                              ('20190129 093000000', '20190227 150000250'),
                                                              ('20211101 093000000', '20211126 150000250'),
                                                              ('20210928 093000000', '20211102 150000250')])
    def test_get_index_tick(self, trading_code, start_datetime, end_datetime):
        """
        测试指数Tick查询
        :param trading_code:单支股票代码
        :return:
        """
        result = self.ind.get_index_tick(trading_code, start_datetime, end_datetime)
        assert isinstance(result, pd.DataFrame)
        if os.environ.get("DSWMAP_envTag") != 'prd':
            assert type(result) == pd.DataFrame
        else:
            assert len(result) > 0

    @pytest.mark.parametrize('trading_code', ['000300.SH', '000001.SH'])
    @pytest.mark.parametrize('start_datetime, end_datetime', [('20200302 093000000', '20200302 150000250'),
                                                              ('20190529 093000000', '20191127 150000250'),
                                                              ( '20211101 093000000', '20211120 150000250')])
    @pytest.mark.parametrize('k_type', ['Kline1M4ZT', 'Kline5M4ZT', 'Kline10M4ZT', 'Kline60M4ZT'])
    def test_get_index_kline(self, trading_code, start_datetime, end_datetime, k_type):
        """
        测试指数K线查询
        :param trading_code:单支股票代码
        :return:
        """
        result = self.ind.get_index_kline(trading_code, start_datetime, end_datetime, k_type)
        assert type(result) == pd.DataFrame
        if os.environ.get("DSWMAP_envTag") != 'prd':
            assert type(result) == pd.DataFrame
        else:
            assert len(result) > 0

    @pytest.mark.skipif(os.environ.get("DSWMAP_envTag") != 'prd', reason="生产环境条件下测试")
    @pytest.mark.parametrize('stock_list', [[]])
    @pytest.mark.parametrize('date_start, date_end', [("20201220", "20210120")])
    @pytest.mark.parametrize('factor_list, table_name', [(["NET_PROFIT", "EST_EPS", "EST_PE", "EST_PEG",
                                                           "EST_ROE", "EST_OPER_REVENUE", "EST_CFPS", "EST_DPS",
                                                           "EST_BPS", "EST_EBIT", "EST_EBITDA", "EST_TOTAL_PROFIT",
                                                           "EST_OPER_PROFIT", "EST_OPER_COST"], None),
                                                         (["NET_PROFIT", "EST_EPS", "EST_PE"], "AIndexConsensusRollingData"),
                                                         ])
    @pytest.mark.parametrize('ROLLING_TYPE', [['CAGR', 'FY2'], [], ['CAGR']])
    @pytest.mark.parametrize('CONSEN_DATA_CYCLE_TYP', [["263003000"]])
    @pytest.mark.parametrize('S_EST_YEARTYPE', [["FY2"]])
    @pytest.mark.parametrize('S_WRATING_CYCLE', [["263003000"]])
    def test_get_source_factor_value1(self, stock_list, date_start, date_end, factor_list, ROLLING_TYPE,
                                             CONSEN_DATA_CYCLE_TYP, S_EST_YEARTYPE, S_WRATING_CYCLE, table_name):
        date_list = self.bd.get_trading_day(date_start, date_end)
        if table_name == None:
            df = self.ind.get_source_factor_value(stock_list, date_list, factor_list, ROLLING_TYPE=ROLLING_TYPE,
                                                  CONSEN_DATA_CYCLE_TYP=CONSEN_DATA_CYCLE_TYP, S_EST_YEARTYPE=S_EST_YEARTYPE,
                                                  S_WRATING_CYCLE=S_WRATING_CYCLE)
        else:
            df = self.ind.get_source_factor_value(stock_list, date_list, factor_list, ROLLING_TYPE=ROLLING_TYPE,
                                                  CONSEN_DATA_CYCLE_TYP=CONSEN_DATA_CYCLE_TYP,
                                                  S_EST_YEARTYPE=S_EST_YEARTYPE,
                                                  S_WRATING_CYCLE=S_WRATING_CYCLE, table_name=table_name)
        assert len(df) > 0
        assert isinstance(df, pd.DataFrame)


if __name__ == "__main__":
    pytest.main(["-v"])
