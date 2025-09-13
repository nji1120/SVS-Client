"""
2025/9/13
フォトダイオードが動作するか確認するプログラム
→ テスト完了. 全チャンネルを指定して読み取れた.
  ただし、自転車のライトくらいのかなりの明るい光を当てないと値がでない. (LEDでいけるか微妙か...?)
"""

from pathlib import Path
ROOT=Path(__file__).parent.parent.parent
import sys
sys.path.append(str(ROOT.parent)) # sensor_tutorialsのパスを追加

import argparse
import time

from SVS_Client.src.sensor import PhotoDiode

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--ch",default=0,type=int)
    args=parser.parse_args()
    ch=args.ch

    channel_mappings=[
        5,4,3,2,1,0
    ]

    photo_diode=PhotoDiode(bus=0,device=0,vref=3.334,max_speed_hz=75000,spi_mode=0)
    freq=5 # Hz
    cnt=0
    while True:
        cnt+=1
        if cnt%freq==0:
            sensor_msg=f"CH{ch} : {photo_diode.read(channel=channel_mappings[ch])}"
            print(f"cnt: {cnt}, {sensor_msg}")
        time.sleep(1.0/freq)

if __name__ == "__main__":
    main()