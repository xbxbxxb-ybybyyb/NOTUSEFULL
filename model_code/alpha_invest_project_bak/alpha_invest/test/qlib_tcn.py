#  Copyright (c) Microsoft Corporation.
#  Licensed under the MIT License.
# %%
import qlib
from qlib.utils import init_instance_by_config, flatten_dict
from qlib.workflow import R
from qlib.workflow.record_temp import SignalRecord, PortAnaRecord, SigAnaRecord
from qlib.tests.data import GetData
from qlib.tests.config import CSI300_BENCH, CSI300_GBDT_TASK
import yaml

def get_tcn_task():
    config = yaml.load(open("./qlib_examples/benchmarks/TCN/workflow_config_tcn_Alpha158.yaml", "rb"))
    return config

# %%
if __name__ == "__main__":
    # use default data
    provider_uri = "~/.qlib/qlib_data/cn_data"  # target_dir
    GetData().qlib_data(target_dir=provider_uri, region="cn", exists_skip=True)
    qlib.init(provider_uri=provider_uri, region="cn")

    # model = init_instance_by_config(CSI300_GBDT_TASK["model"])
    # dataset = init_instance_by_config(CSI300_GBDT_TASK["dataset"])
    # port_analysis_config = {
    #     "executor": {
    #         "class": "SimulatorExecutor",
    #         "module_path": "qlib.backtest.executor",
    #         "kwargs": {
    #             "time_per_step": "day",
    #             "generate_portfolio_metrics": True,
    #         },
    #     },
    #     "strategy": {
    #         "class": "TopkDropoutStrategy",
    #         "module_path": "qlib.contrib.strategy.signal_strategy",
    #         "kwargs": {
    #             "signal": (model, dataset),
    #             "topk": 50,
    #             "n_drop": 5,
    #         },
    #     },
    #     "backtest": {
    #         "start_time": "2017-01-01",
    #         "end_time": "2020-08-01",
    #         "account": 100000000,
    #         "benchmark": CSI300_BENCH,
    #         "exchange_kwargs": {
    #             "freq": "day",
    #             "limit_threshold": 0.095,
    #             "deal_price": "close",
    #             "open_cost": 0.0005,
    #             "close_cost": 0.0015,
    #             "min_cost": 5,
    #         },
    #     },
    # }

    tcn_config = get_tcn_task()
    model = init_instance_by_config(tcn_config['task']["model"])
    dataset = init_instance_by_config(tcn_config['task']["dataset"])
    print(dataset)

    # %%
    port_analysis_config = tcn_config["port_analysis_config"]

    # NOTE: This line is optional
    # It demonstrates that the dataset can be used standalone.
    example_df = dataset.prepare("train")

    def dataset_to_torch():
        import torch
        import numpy as np
        df_train, df_valid, df_test = dataset.prepare(
            ["train", "valid", "test"],
            col_set=["feature", "label"],
            # data_key=DataHandlerLP.DK_L,
        )

        x_train, y_train = df_train["feature"], df_train["label"]
        x_valid, y_valid = df_valid["feature"], df_valid["label"]

        x_train_values = x_train.values
        y_train_values = np.squeeze(y_train.values)

        indices = np.arange(len(x_train_values))
        batch_size = 5
        for i in range(len(indices))[:: batch_size]:
            feature = torch.from_numpy(x_train_values[indices[i: i + batch_size]]).float()
            label = torch.from_numpy(y_train_values[indices[i: i + batch_size]]).float()


    # %%
    # print(example_df.head())

    # start exp
    with R.start(experiment_name="workflow"):
        R.log_params(**flatten_dict(CSI300_GBDT_TASK))
        model.fit(dataset)
        R.save_objects(**{"params.pkl": model})

        # prediction
        recorder = R.get_recorder()
        sr = SignalRecord(model, dataset, recorder)
        sr.generate()

        # Signal Analysis

        sar = SigAnaRecord(recorder)
        sar.generate()

        # backtest. If users want to use backtest based on their own prediction,
        # please refer to https://qlib.readthedocs.io/en/latest/component/recorder.html#record-template.
        par = PortAnaRecord(recorder, port_analysis_config, "day")
        par.generate()


