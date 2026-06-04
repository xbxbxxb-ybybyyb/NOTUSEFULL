import os
import pandas as  pd
from artifacts import online_model, model_save_and_evaluate

label_name = "LabelFirstPeak_th10_120s"
start_date = "2024-01-18"
os.system(
    f"curl -u 'XTrader:XTrader@123' ftp://168.8.2.68/018077/signal_files/{start_date}/ --ftp-create-dirs ")

symbol_list = [
            ("688017.SH", "tick_688017.SH"),
            ("688012.SH", "unite_semi_v1.1"),
            ("688981.SH", "l2p_688981.SH"),
            ("688047.SH", "online_kc_normal"),
            ("688390.SH", "online_kc_normal"),
            ("688012.SH", "unite_semi_test"),
            ("688041.SH", "unite_kc"),
            ("688041.SH", "unite_kc"),
            ("688271.SH", "unite_kc"),
            ("688008.SH", "unite_kc"),
            ("688122.SH", "unite_kc"),
            ("688256.SH", "unite_kc"),
            ("002371.SZ", "unite_semi_v1.1"),
            ("002409.SZ", "unite_semi_v1.1"),
            ("300223.SZ", "unite_semi_v1.1"),
            ("688008.SH", "unite_semi_v1.1"),
            ]

for exp_name in ["nation_innovation_v1.1", "unite_semi_test","unite_kc","unite_semi_v1.1", "semi_v1.1", "computer_v1.1", "nation_innovation_v1.1", "l2p_000977.SZ"]:
    base_dir = f"/data/user/013150/trade_data/COO/{exp_name}/signal_files"
    thre_json = pd.read_json(f"/data/user/013150/trade_data/COO/{exp_name}/{exp_name}/threshold.json")
    # os.system(f"curl -u 'XTrader:XTrader@123' ftp://168.8.2.68/018077/signal_files/{exp_name}/ --ftp-create-dirs ")
    parquet_files = os.listdir(base_dir)
    for file in parquet_files:
        if file.endswith("parquet"):
            stock = file[:-8].split("-")[-1]
            print(file)
            try:
                pred_th_up, pred_th_dw = thre_json[stock]["longPredTh"], thre_json[stock]["shortPredTh"]
                print(thre_json[stock])
            except:
                print("no threshold ", stock)
                continue
            output_path = os.path.join(base_dir, stock)
            try:
                os.makedirs(output_path)
            except:
                pass
            # os.system(
            #     f"curl -u 'XTrader:XTrader@123' ftp://168.8.2.68/018077/signal_files/{exp_name}/{stock.split('.')[0]}/ --ftp-create-dirs ")
            signal_df = pd.read_parquet(os.path.join(base_dir, file))
            signal_df = signal_df[signal_df["DATE"]>=start_date]
            model_save_and_evaluate.model_signal_process_long_short_pred_th_classify(signal_df,
                                                                                     pred_th_up=pred_th_up,
                                                                                     pred_th_dw=pred_th_dw,
                                                                                     symbol=stock,
                                                                                     signal_process_base_dir=output_path)
            for date in sorted(set(signal_df["DATE"].tolist())):
                print(f"curl ftp://168.8.2.68/018077/signal_files/{exp_name}/{stock.split('.')[0]}/ -T {output_path}/{date}.txt -u 'XTrader:XTrader@123'")
                os.system(f"curl ftp://168.8.2.68/018077/signal_files/{exp_name}/{stock.split('.')[0]}/ -T {output_path}/{date}.txt -u 'XTrader:XTrader@123'" )
                os.system(f"curl ftp://168.8.2.68/018077/signal_files/{date}/{stock}_{exp_name}.txt -T {output_path}/{date}.txt -u 'XTrader:XTrader@123'")

