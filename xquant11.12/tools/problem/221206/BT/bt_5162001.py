from BT.bt_single import bt_single


def main(bt_date):
    portfolio = "5162001"

    bt_dir = "666888/Apollo/bt_info/{}/{}/".format(bt_date, portfolio)
    signal_csv_dir = "ApolloBTSignals"
    production_signal_csv_dir = "ApolloProductionSignals"
    param_dir = "666888/Apollo/bt_params/{}/{}/".format(bt_date, portfolio)
    output_dir = "666888/Apollo/bt_results/{}/{}_research/".format(bt_date, portfolio)
    production_output_dir = "666888/Apollo/bt_results/{}/{}_production/".format(bt_date, portfolio)
    trigger_path = "666888/Apollo/bt_triggers/{}/{}/".format(bt_date, portfolio)
    executor_str = "SignalExecutorCsfNew"

    print("Backtesting {}'s research signals...".format(portfolio))
    bt_single(portfolio, bt_date, bt_dir, signal_csv_dir, param_dir, output_dir, trigger_path, executor_str, "research")
    print("Backtesting {}'s production signals...".format(portfolio))
    bt_single(portfolio, bt_date, bt_dir, production_signal_csv_dir, param_dir, production_output_dir, trigger_path,
              executor_str, "production")
    print("Done")


if __name__ == "__main__":
    bt_date = 20191209
    main(bt_date)