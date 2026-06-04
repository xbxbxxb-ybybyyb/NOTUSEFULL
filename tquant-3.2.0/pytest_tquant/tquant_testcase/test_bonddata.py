from tquant.bond_data import BondData
import pytest
import pandas as pd
import configparser


class TestBondData(object):
    conn = configparser.ConfigParser()
    # 加载现有配置文件
    conn.read(r"/opt/anaconda3/lib/python3.6/site-packages/MDCDataProvider/conf/DXPDataProvider.ini",
              encoding="utf-8-sig")
    file_type = conn.get('task', 'file.type')

    @classmethod
    def setup_class(cls):
        cls.bd = BondData()

    @pytest.mark.parametrize('bar_size', ['K_1MIN', 'K_5MIN', 'K_10MIN', 'K_60MIN', 'K_DAY', 'TICK', 'TRANSACTION', 'ORDER'])
    @pytest.mark.parametrize('t_time', [('20200202 090000000', '20200302 200000000'),
                                        ('20200102 090000000', '20200209 130000000')])
    @pytest.mark.parametrize('symbol', ['110050.SH', '128104.SZ'])
    @pytest.mark.skipif(file_type == 'DFS', reason="DXP条件下测试")
    def test_get_bond_data(self, symbol, t_time, bar_size):
        """
        测试获取债券行情数据
        :param symbol:可转债标的代码
        :param t_time: 测试时间段
        :param bar_size:数据周期枚举类
        :return:
        """
        result = self.bd.get_bond_data(symbol, *t_time, bar_size)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('bar_size', ['TICK', 'TRANSACTION', 'ORDER'])
    @pytest.mark.parametrize('t_time', [('20211101 090000000', '20211130 200000000'),
                                        ('20211201 090000000', '20211213 200000000')])
    @pytest.mark.parametrize('symbol', ['128053.SZ', '155391.SH'])
    @pytest.mark.skipif(file_type == 'DFS', reason="DXP条件下测试")
    def test_get_bond_data_new_time(self, symbol, t_time, bar_size):
        """
        测试获取债券行情数据(增加了新日期)
        :param symbol:可转债标的代码
        :param t_time: 测试时间段
        :param bar_size:数据周期枚举类
        :return:
        """
        result = self.bd.get_bond_data(symbol, *t_time, bar_size)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('t_time', [('20211101 090000000', '20211130 200000000'),
                                        ('20211201 090000000', '20211221 200000000')])
    @pytest.mark.parametrize('symbol', ['128053.SZ', '155391.SH'])
    @pytest.mark.skipif(file_type == 'DFS', reason="DXP条件下测试")
    def test_get_bond_tick(self, symbol, t_time):
        """
        测试获取债券行情数据
        :param symbol:可转债标的代码
        :param t_time: 测试时间段
        :return:
        """
        result = self.bd.get_bond_tick(symbol, *t_time)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('t_time', [('20211101 090000000', '20211130 200000000'),
                                        ('20211201 090000000', '20211221 200000000')])
    @pytest.mark.parametrize('symbol', ['128053.SZ', '155391.SH'])
    @pytest.mark.skipif(file_type == 'DFS', reason="DXP条件下测试")
    def test_get_bond_transaction(self, symbol, t_time):
        """
        测试获取债券行情数据
        :param symbol:可转债标的代码
        :param t_time: 测试时间段
        :return:
        """
        result = self.bd.get_bond_transaction(symbol, *t_time)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('t_time', [('20211101 090000000', '20211130 200000000'),
                                        ('20211201 090000000', '20211221 200000000')])
    @pytest.mark.parametrize('symbol', ['128053.SZ'])
    @pytest.mark.skipif(file_type == 'DFS', reason="DXP条件下测试")
    def test_get_bond_order(self, symbol, t_time):
        """
        测试获取债券行情数据
        :param symbol:可转债标的代码
        :param t_time: 测试时间段

        :return:
        """
        result = self.bd.get_bond_order(symbol, *t_time)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('bar_size', ['TICK', 'ORDER', 'TRANSACTION'])
    @pytest.mark.parametrize('t_time', [("20200202 090000000", "20200302 200000000"),
                                        ("20200102 090000000", "20200228 130000000")])
    @pytest.mark.parametrize('symbol', ["106589.SZ", "109916.SZ"])
    @pytest.mark.skipif(file_type == 'DFS', reason="DXP条件下测试")
    def test_get_bond_data_other_bar(self, symbol, t_time, bar_size):
        """
        测试获取债券行情数据
        :param symbol:可转债标的代码
        :param t_time: 测试时间段
        :param bar_size:数据周期枚举类
        :return:
        """
        result = self.bd.get_bond_data(symbol, *t_time, bar_size)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)



    @pytest.mark.parametrize('t_time', [("20200103 090000000", "20200919 200000000"),
                                        ('20200201 090000000', '20200901 200000000')])
    #@pytest.mark.parametrize('t_data', [('010011.IB.QB', 'QUOTE'), ('200205.IB.QB', 'QUOTE'),
    #                                    ('101551040.IB.QB', 'TRANSACTION'), ('190409.IB.QB', 'TRANSACTION')])
    @pytest.mark.parametrize('symbol', ['010011.IB.QB', '200205.IB.QB', '101551040.IB.QB', '190409.IB.QB'])
    @pytest.mark.parametrize('bar_size', ['QUOTE', 'TRANSACTION'])
    @pytest.mark.skipif(file_type == 'DFS', reason="DXP条件下测试")
    def test_get_qb_bond_data_dxp(self, symbol, t_time, bar_size):
        """
        :param t_data:QB债券标的代码及数据周期枚举类
        :param t_time: 查询时间范围
        :return:
        """
        #result = self.bd.get_qb_bond_data(t_data[0], *t_time, t_data[1])
        result = self.bd.get_qb_bond_data(symbol, *t_time, bar_size)
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)

    @pytest.mark.parametrize('fill_cash_bond_quotes', [True, False])
    @pytest.mark.parametrize('t_time', [("20200801 090000000", "20200915 200000000"),
                                        ("20200901 090000000", "20200930 200000000")])
    @pytest.mark.parametrize('t_data', [('200403.CFE', 'QUOTE'), ('209924.CFE', 'TRANSACTION'), ('150205.CFE', 'TICK')])
    @pytest.mark.skipif(file_type == 'DFS', reason="DXP条件下测试")
    def test_get_cfe_bond_data(self, t_time, t_data, fill_cash_bond_quotes):
        """
        :param t_data:QB债券标的代码及数据周期枚举类
        :param t_time: 查询时间范围
        :return:
        """
        result = self.bd.get_cfe_bond_data(t_data[0], *t_time, t_data[1], fill_cash_bond_quotes=fill_cash_bond_quotes)
        if t_data[1] == 'QUOTE' and fill_cash_bond_quotes is True:
            assert len(result.loc[:, 'cashbondquotes'][0][0]) == 23
        if t_data[1] == 'QUOTE' and fill_cash_bond_quotes is False:
            assert len(result.loc[:, 'cashbondquotes'][0][0]) < 23
        assert len(result) > 0
        assert isinstance(result, pd.DataFrame)


if __name__ == "__main__":
    pytest.main(["-v"])