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

import serial

def check_ttyAMA0(port='/dev/ttyAMA0', baudrate=115200, timeout=1):
    """
    /dev/ttyAMA0 にシリアル通信でアクセスできるかを簡単にチェックします。
    - ポートが開ければOK
    - 'hello'を書き込み→リードしてみる（繋がった先によっては何も返らない場合もあり！）
    """
    try:
        with serial.Serial(port, baudrate, timeout=timeout) as ser:
            print(f"Opened {port} (baudrate={baudrate})")
            test_bytes = b'hello\n'
            ser.write(test_bytes)
            ser.flush()
            # 返事をちょっとだけ読む
            response = ser.read(10)
            # 通常 0バイト でも ポートopen成功=繋がってる
            print(f"Read bytes: {response}")

            return True, response
    except serial.SerialException as e:
        print(f"Could not open {port}: {e}")
        return False, None
    except Exception as e:
        print(f"Other error: {e}")
        return False, None


def switch():

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




if __name__=="__main__":
    switch()
    
    ok, res = check_ttyAMA0()
    if ok:
        print("ポート接続テスト: OK")
    else:
        print("ポート接続テスト: NG")

    sleep_time=60 * 10 #s
    time.sleep(sleep_time)