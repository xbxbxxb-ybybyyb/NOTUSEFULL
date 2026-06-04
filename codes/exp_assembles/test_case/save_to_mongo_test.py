import sys
import os
import json
import pandas as pd
import pytest
from datetime import datetime

current_file_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(current_file_path)
sys.path.append(parent_directory)
from artifacts.save_to_mongo import MongoDB


class TestMongoDB(object):
    @classmethod
    def setup_class(cls):
        cls.mdb = MongoDB()
        now = datetime.now()
        # 转换为指定格式的字符串
        formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
        cls.time = formatted_now

    # @pytest.mark.smoke
    # def test_load_configs(self):
    #     """
    #     测试exp_params取数据接口
    #     :param
    #     :return:
    #     """
    #     df = self.mdb.load_configs()
    #     assert len(df) > 0
    #
    # # @pytest.mark.smoke
    # # def test_load_factor_evaluation_data(self):
    # #     load_factor_evaluation_data(self, factor_list, symbol_list, label_list, start_time, end_time)
    # #     df = self.mdb.load_configs()
    # #     assert len(df) > 0

    @pytest.mark.smoke
    def test_exp_params_todb(self):
        """
        测试exp_params存入mongodb的接口
        :param
        :return:
        """
        exp_id = "exp_test"
        params_json = {
            "test1": 1,
            "test2": "abc",
            "test3": ["q", "w", "e"],
        }
        params_json_extra = {
            "ttt": "extra"
        }
        version_alias = "test"
        hash256 = "1234"
        exp_type = "test_save"
        params_jsonstr = json.dumps(params_json_extra)
        params_jsonstr_extra = json.dumps(params_json)
        result = self.mdb.exp_params_todb(exp_id, version_alias, hash256, exp_type, params_jsonstr,
                                          params_jsonstr_extra)
        # self.mdb.delete_indb("exp_params", "version_alias", version_alias)
        assert result

    def test_exp_params_todb_same(self):
        """
        测试exp_params存入已存在的版本号的情况
        :param
        :return:
        """
        exp_id = "exp_test"
        params_json = {
            "test1": 1,
            "test2": "abc",
            "test3": ["q", "w", "e"],
        }
        params_json_extra = {
            "ttt": "extra"
        }
        version_alias = "test2"
        hash256 = "12345"
        exp_type = "test_save"
        params_jsonstr = json.dumps(params_json_extra)
        user_id = "testuser"
        create_time = "2023-10-30"
        params_jsonstr_extra = json.dumps(params_json)
        result = self.mdb.exp_params_todb(exp_id, version_alias, hash256, exp_type, params_jsonstr,
                                          params_jsonstr_extra)
        assert result

    def test_exp_params_todb_less(self):
        """
        测试exp_params存入缺少了必要参数时的情况
        :param
        :return:
        """
        params_json = {
            "test1": 1,
            "test2": "abc",
            "test3": ["q", "w", "e"],
        }
        params_json_extra = {
            "ttt": "extra"
        }
        version_alias = "test"
        hash256 = "1234"
        exp_type = "test_save"
        params_jsonstr = json.dumps(params_json_extra)
        user_id = "testuser"
        with pytest.raises(Exception) as e:
            self.mdb.exp_params_todb(version_alias, hash256, exp_type)
        assert 'missing 2 required positional argument' in str(e)

    def test_exp_params_todb_erro(self):
        """
        测试exp_params存入时version_alias和hash256不对应的情况
        :param
        :return:
        """
        exp_id = "exp_test"
        params_json = {
            "test1": 1,
            "test2": "abc",
            "test3": ["q", "w", "e"],
        }
        params_json_extra = {
            "ttt": "extra"
        }
        version_alias = "test2"
        hash256 = "123456"
        exp_type = "test_save"
        params_jsonstr = json.dumps(params_json_extra)
        user_id = "testuser"
        create_time = "2023-10-30"
        params_jsonstr_extra = json.dumps(params_json)
        try:
            self.mdb.exp_params_todb(exp_id, version_alias, hash256, exp_type, params_jsonstr,
                                     params_jsonstr_extra)
        except Exception as e:
            assert (e, "AssertionError")

    # @pytest.mark.smoke
    # def test_user_event_todb(self):
    #     exp_id = "test_exp"
    #     version_alias = "test"
    #     event_type = "save_strategy_data"
    #     user_id = "testuser"
    #     create_time = "2023-10-30"
    #     params = {
    #         "strategy": "test"
    #     }
    #     result = self.mdb.user_event_todb(exp_id, version_alias, event_type, user_id, create_time, params)
    #     # self.mdb.delete_indb("user_event", "version_alias", version_alias)
    #     assert result
    #
    # def test_user_event_todb_less(self):
    #     """
    #     测试user_event存入缺少了必要参数时的情况
    #     :param
    #     :return:
    #     """
    #     version_alias = "test"
    #     event_type = "save_strategy_data"
    #     user_id = "testuser"
    #     create_time = "2023-10-30"
    #     params = {
    #         "strategy": "test"
    #     }
    #     with pytest.raises(Exception) as e:
    #         self.mdb.user_event_todb(version_alias, event_type, user_id, create_time, params)
    #     assert 'missing 1 required positional argument' in str(e)
    #
    # def test_user_event_todb_erro(self):
    #     """
    #     测试user_event必要参不对应时的情况
    #     :param
    #     :return:
    #     """
    #     exp_id = "test_exp"
    #     version_alias = "test"
    #     event_type = "save_strategy_data"
    #     user_id = "testuser"
    #     create_time = "2023-10-30"
    #     params = {
    #         "strategg": "test"
    #     }
    #     try:
    #         self.mdb.user_event_todb(exp_id, version_alias, event_type, user_id, create_time, params)
    #     except Exception as e:
    #         assert (e, "固定参数与行为类型不符，请确认")

    def test_signal_evaluation_data_todb(self):
        """
        测试signal_evaluation_data_todb
        :param
        :return:
        """
        exp_id = "test_exp"
        version_alias = "test"
        symbol = "00001.SZ"
        evaluation_type = "123"
        condition = {
            "test1": 1,
            "test2": "abc",
            "test3": ["q", "w", "e"],
        }
        create_time = "2023-10-30"
        metrics = pd.DataFrame({
            'date': ['2023-07-01', '2023-07-02', '2023-07-03'],
            'data1': [1, 2, 3],
            'data2': [4, 5, 6],
            'data3': [7, 8, 9]
        })
        result = self.mdb.signal_evaluation_data_todb(
            exp_id, version_alias, symbol, evaluation_type, condition, metrics)
        assert result

    def test_backtest_evaluation_data_todb(self):
        """
        测试signal_evaluation_data_todb
        :param
        :return:
        """
        exp_id = "test_exp"
        version_alias = "test"
        symbol = "00001.SZ"
        backtest_evaluation_type = "backtest123"
        condition = {
            "test1": 1,
            "test2": "abc",
            "test3": ["q", "w", "e"],
        }
        strategy_name = "testbak"
        startegy_params = "testtest"
        create_time = "2023-10-30"
        metrics = pd.DataFrame({
            'date': ['2023-07-01', '2023-07-02', '2023-07-03'],
            'data1': [1, 2, 3],
            'data2': [4, 5, 6],
            'data3': [7, 8, 9]
        })
        signal_path = "signal_path_test"
        result = self.mdb.backtest_evaluation_data_todb(
            exp_id, version_alias, symbol, strategy_name, startegy_params,
            backtest_evaluation_type, condition, metrics)
        assert result

    # @pytest.mark.smoke
    # def test_evaluation_data_todb(self):
    #     version_alias = "test"
    #     model_name = "test_mdname"
    #     symbol = "00001.SH"
    #     label_th = "label_th0.9"
    #     probs = "probs0.64"
    #     create_time = "2023-10-30"
    #     performance = {
    #         "0.9": 0.555,
    #         "1.0": 0.595,
    #     }
    #     result = self.mdb.signal_evaluation_data_todb(version_alias, model_name, symbol, label_th, probs, performance, create_time)
    #     self.mdb.delete_indb("evaluation_data", "version_alias", version_alias)
    #     assert result
    # @pytest.mark.smoke
    # def test_factor_evaluation_data_todb(self):
    #     """
    #     测试factor_evaluation_data_todb接口
    #     :param
    #     :return:
    #     """
    #     factor_name = "test3"
    #     label = "flag1"
    #     symbol = "00001.SZ"
    #     evaluation_df = pd.DataFrame({
    #         'MDDate': ['2023-07-01', '2023-07-02', '2023-07-03'],
    #         'data1': [1, 2, 3],
    #         'data2': [4, 5, 6],
    #         'data3': [7, 8, 9]
    #     })
    #     result = self.mdb.factor_evaluation_data_todb(factor_name, symbol, label, evaluation_df)
    #     #self.mdb.delete_factor_indb("factor_evaluation_data", 'index.factor_name', "test3")
    #     assert result is True
    #
    # def test_factor_evaluation_data_todb2(self):
    #     """
    #     测试factor_evaluation_data_todb接口插入异常情况
    #     :param
    #     :return:
    #     """
    #     factor_name = "test3"
    #     label = "flag1"
    #     symbol = "00001.SZ"
    #     evaluation_df = pd.DataFrame({
    #         'MDDate': ['2023-07-01', '2023-07-02', '2023-07-03'],
    #         'data1': [1, 2, 3],
    #         'data2': [4, 5, 6],
    #         'data3': [7, 8, 9]
    #     })
    #     result = self.mdb.factor_evaluation_data_todb(factor_name, symbol, label, evaluation_df)
    #     assert result is False
    #
    # @pytest.mark.smoke
    # def test_load_factor_evaluation_data(self):
    #     """
    #     测试load_factor_evaluation_data接口
    #     :param
    #     :return:
    #     """
    #     factor_name_list = ["test3"]
    #     label_list = ["flag1"]
    #     symbol_list = ["00001.SZ"]
    #     start_time = "20230701"
    #     end_time = "20230703"
    #     result = self.mdb.load_factor_evaluation_data(
    #         factor_name_list, symbol_list, label_list, start_time, end_time)
    #     print(result)
    #     assert len(result)


    @pytest.mark.smoke
    def test_load_signal_evaluation_data(self):
        """
        测试load_signal_evaluation_data接口
        :param
        :return:
        """
        exp_id = "test_exp"
        symbol = "00001.SZ"
        result = self.mdb.load_signal_evaluation_data(exp_id, symbol)
        print(len(result))
        assert len(result)

    def test_load_backtest_evaluation_data(self):
        """
        测试load_signal_evaluation_data接口
        :param
        :return:
        """
        exp_id = "test_exp"
        symbol = "00001.SZ"
        result = self.mdb.load_backtest_evaluation_data(exp_id, symbol)
        print(len(result))
        assert len(result)

    def test_load_user_event(self):
        """
        测试load_user_event接口
        :param
        :return:
        """
        exp_id = "test_exp"
        result = self.mdb.load_user_event(exp_id)
        print(len(result))
        assert len(result)

    @pytest.mark.smoke
    def test_load_configs(self):
        """
        测试exp_params取数据接口
        :param
        :return:
        """
        df = self.mdb.load_configs()
        assert len(df) > 0

    def test_delete_data(self):
        """
        删除自动化用例插入的数据
        :param
        :return:
        """
        params_json = {
            "test1": 1,
            "test2": "abc",
            "test3": ["q", "w", "e"],
        }
        params_json_extra = {
            "ttt": "extra"
        }
        version_alias = "test"
        result = self.mdb.delete_indb("exp_params_new", "version_alias", version_alias)
        assert result is True

    # @pytest.mark.smoke
    # def test_load_factor_evaluation_data(self):
    #     load_factor_evaluation_data(self, factor_list, symbol_list, label_list, start_time, end_time)
    #     df = self.mdb.load_configs()
    #     assert len(df) > 0
    def test_delete_data_e(self):
        """
        删除自动化用例插入的数据
        :param
        :return:
        """
        params_json = {
            "test1": 1,
            "test2": "abc",
            "test3": ["q", "w", "e"],
        }
        params_json_extra = {
            "ttt": "extra"
        }
        version_alias = "test"
        result = self.mdb.delete_indb("exp_params_new", "version_alias", version_alias)
        assert result is False

    def test_delete_user_event(self):
        exp_id = "test_exp"
        version_alias = "test"
        event_type = "save_strategy_data"
        user_id = "testuser"
        create_time = "2023-10-30"
        params = {
            "strategy": "test"
        }
        result = self.mdb.delete_indb("user_event_new", "version_alias", version_alias)
        assert result is True

    def test_delete_user_event_e(self):
        exp_id = "test_exp"
        version_alias = "test"
        event_type = "save_strategy_data"
        user_id = "testuser"
        create_time = "2023-10-30"
        params = {
            "strategy": "test"
        }
        result = self.mdb.delete_indb("user_event_new", "version_alias", version_alias)
        assert result is False

    def test_signal_evaluation_data_delete(self):
        """
        测试signal_evaluation_data_todbs删除
        :param
        :return:
        """
        exp_id = "test_exp"
        version_alias = "test"
        symbol = "00001.SZ"
        evaluation_type = "123"
        condition = {
            "test1": 1,
            "test2": "abc",
            "test3": ["q", "w", "e"],
        }
        create_time = "2023-10-30"
        metrics = pd.DataFrame({
            'date': ['2023-07-01', '2023-07-02', '2023-07-03'],
            'data1': [1, 2, 3],
            'data2': [4, 5, 6],
            'data3': [7, 8, 9]
        })
        result = self.mdb.signal_evaluation_data_delete(
            exp_id, version_alias, symbol, evaluation_type, condition, metrics)
        assert result is True

    def test_backtest_evaluation_data_delete(self):
        """
        测试backtest_evaluation_data_todb删除
        :param
        :return:
        """
        exp_id = "test_exp"
        version_alias = "test"
        symbol = "00001.SZ"
        backtest_evaluation_type = "backtest123"
        condition = {
            "test1": 1,
            "test2": "abc",
            "test3": ["q", "w", "e"],
        }
        strategy_name = "testbak"
        startegy_params = "testtest"
        create_time = "2023-10-30"
        metrics = pd.DataFrame({
            'date': ['2023-07-01', '2023-07-02', '2023-07-03'],
            'data1': [1, 2, 3],
            'data2': [4, 5, 6],
            'data3': [7, 8, 9]
        })
        signal_path = "signal_path_test"
        result = self.mdb.backtest_evaluation_data_delete(
            exp_id, version_alias, symbol, strategy_name,
            startegy_params, backtest_evaluation_type, condition, metrics)
        assert result is True

    def test_signal_evaluation_data_delete_e(self):
        """
        测试signal_evaluation_data_todb删除异常
        :param
        :return:
        """
        exp_id = "test_exp"
        version_alias = "test"
        symbol = "00001.SZ"
        evaluation_type = "123"
        condition = {
            "test1": 1,
            "test2": "abc",
            "test3": ["q", "w", "e"],
        }
        create_time = "2023-10-30"
        metrics = pd.DataFrame({
            'date': ['2023-07-01', '2023-07-02', '2023-07-03'],
            'data1': [1, 2, 3],
            'data2': [4, 5, 6],
            'data3': [7, 8, 9]
        })
        result = self.mdb.signal_evaluation_data_delete(
            exp_id, version_alias, symbol, evaluation_type, condition, metrics)
        assert result is False

    def test_backtest_evaluation_data_delete_e(self):
        """
        测试backtest_evaluation_data_todb删除异常
        :param
        :return:
        """
        exp_id = "test_exp"
        version_alias = "test"
        symbol = "00001.SZ"
        backtest_evaluation_type = "backtest123"
        condition = {
            "test1": 1,
            "test2": "abc",
            "test3": ["q", "w", "e"],
        }
        strategy_name = "testbak"
        startegy_params = "testtest"
        create_time = "2023-10-30"
        metrics = pd.DataFrame({
            'date': ['2023-07-01', '2023-07-02', '2023-07-03'],
            'data1': [1, 2, 3],
            'data2': [4, 5, 6],
            'data3': [7, 8, 9]
        })
        signal_path = "signal_path_test"
        result = self.mdb.backtest_evaluation_data_delete(
            exp_id, version_alias, symbol, strategy_name,
            startegy_params, backtest_evaluation_type, condition, metrics)
        assert result is False

    # def test_factor_evaluation_data_delete(self):
    #     """
    #     测试factor_evaluation_data_todb接口
    #     :param
    #     :return:
    #     """
    #     factor_name = "test3"
    #     label = "flag1"
    #     symbol = "00001.SZ"
    #     evaluation_df = pd.DataFrame({
    #         'MDDate': ['2023-07-01', '2023-07-02', '2023-07-03'],
    #         'data1': [1, 2, 3],
    #         'data2': [4, 5, 6],
    #         'data3': [7, 8, 9]
    #     })
    #     result = self.mdb.delete_factor_indb("factor_evaluation_data", 'index.factor_name', "test3")
    #     assert result is True
    #
    # def test_factor_evaluation_data_delete_e(self):
    #     """
    #     测试factor_evaluation_data_todb接口
    #     :param
    #     :return:
    #     """
    #     factor_name = "test3"
    #     label = "flag1"
    #     symbol = "00001.SZ"
    #     evaluation_df = pd.DataFrame({
    #         'MDDate': ['2023-07-01', '2023-07-02', '2023-07-03'],
    #         'data1': [1, 2, 3],
    #         'data2': [4, 5, 6],
    #         'data3': [7, 8, 9]
    #     })
    #     result = self.mdb.delete_factor_indb("factor_evaluation_data", 'index.factor_name', "test3")
    #     assert result is False

    @pytest.mark.smoke
    def test_user_event_todb_get(self):
        exp_id = "test_exp"
        version_alias = "test"
        event_type = "save_strategy_data"
        collection = "test"
        params = {
            "strategy": "test"
        }
        result = self.mdb.user_event_todb_get(exp_id, version_alias, collection, event_type, params)
        # self.mdb.delete_indb("user_event", "version_alias", version_alias)
        assert result


if __name__ == "__main__":
    mdb = MongoDB()
    df = mdb.load_configs()
    print(df)
    assert len(df) > 0
