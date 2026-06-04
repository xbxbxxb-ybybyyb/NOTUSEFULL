from xbrain_pro.fish_entry.system.fish_backtest import FishXbrain
import os

if __name__ == "__main__":
    fx = FishXbrain(root_path=os.path.join(os.path.dirname(os.path.abspath(__file__))),
                    json_name="user_backtest_common_params.json")
    fx.fish_backtest_entry()
