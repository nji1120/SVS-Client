"""
2025/9/13
TC4052BでMUXのチャンネルを指定して, RCS660Sでfelica通信を行うテストプログラム
→ テスト完了. 全チャンネルを指定して通信できた.
"""

from pathlib import Path
ROOT=Path(__file__).parent.parent.parent
import sys
sys.path.append(str(ROOT.parent)) # sensor_tutorialsのパスを追加
# print(sys.path)
import time

import pandas as pd
import argparse

from SVS_Client.src.module.tc4052b import TC4052B
from SVS_Client.src.module.rc_s660s.src.rcs660s_manager import RCS660SManager
from SVS_Client.src.module.rc_s660s.src.rcs660s import RCS660S
from Sensor_tutorials.rc_s660s.src.utils import print_hex


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--ch",default="ch0",type=str)
    args=parser.parse_args()
    ch=args.ch

    # 2in2outのMUX
    mapping=pd.read_csv(Path(__file__).parent/"mux_mapping.csv",index_col=0)
    print("MUX mapping:")
    print(mapping)

    # なんでかわからないけどTC4052Bのインスタンス化で落ちる
    # → どうやら, BCM modeなのに, 物理的な配置番号(1~40)で指定し, 範囲外の数値(35とかBCM番号にはない)をいれると落ちるっぽい
    tc4052b=TC4052B(mapping)
    tc4052b.switch_channel(ch) # MUXのチャンネル指定
    # print(tc4052b.channel_switch)


    # RCS660S
    port="/dev/ttyAMA0"
    baudrate=115200
    timeout_fps=100
    rcs660s=RCS660S(port=port, baudrate=baudrate, timeout_fps=timeout_fps)
    rcs660s_manager=RCS660SManager(rcs660s, is_debug=False)
    rcs660s_manager.reset_device()
    rcs660s_manager.setup_device()


    try:
        # >> 通信テスト >>
        fps=5 # Hz
        cnt=0
        while True:
            if cnt%fps==0:
                response=rcs660s_manager.polling()
                print(f"cnt: {cnt}, target channel: {ch}")
                for key,value in response.items():
                    if value is None:
                        print(f"{key}: None")
                    else:
                        print(f"{key}: {" ".join(value)}")
                print("-")

            cnt+=1
            time.sleep(1.0/fps)
        # << 通信テスト >>
    finally:
        print("通信終了")
        rcs660s_manager.close() # 通信終了
    

if __name__=="__main__":
    main()