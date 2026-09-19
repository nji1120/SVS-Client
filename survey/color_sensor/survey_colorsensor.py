"""
2025/9/13
TC4052BでMUXのチャンネルを指定して, カラーセンサを読み取るテストプログラム
→ テスト完了. 全チャンネルを指定して読み取れた.
"""

from pathlib import Path
ROOT=Path(__file__).parent.parent.parent
import sys
sys.path.append(str(ROOT.parent)) # sensor_tutorialsのパスを追加

import argparse
import time

from SVS_Client.src.module.color_sensor.color_sensor import ColorSensor


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--ch",default=0,type=int)
    args=parser.parse_args()
    ch=f"ch{args.ch}"

    mux_master_address=113
    color_sensor_address=42

    color_sensor=ColorSensor(
        master_address=mux_master_address,
        slave_address=color_sensor_address,
        channel_mapping={
            f"ch{i}":1<<i for i in range(8)
        }
    )
    freq=5 # Hz
    cnt=0
    while True:
        if cnt%freq==0:
            sensor_msg=f"CH{ch} : {color_sensor.read(ch)}"
            print(f"cnt: {cnt}, {sensor_msg}")
        cnt+=1
        time.sleep(1.0/freq)


if __name__ == "__main__":
    main()