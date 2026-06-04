from BT.combine_bt_info import main as main1
from BT.copy_triggers import main as main2
from BT.generate_bt_params import main as main3
from InferSignal.generate_signals import generate_signals as main4
from BT.bt_5161101 import main as main5
from BT.bt_5162001 import main as main6

today = "20191220"

main1(today)
main2(today)
main3(today)
main4()
main5(int(today))
main6(int(today))
