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

from SVS_Client.src.module.rc_s660s.src.ccid_command.reset_device import ResetDevice
from SVS_Client.src.module.rc_s660s.src.ccid_command.manage_session import ManageSession, ManageSessionDataObjectTag
from SVS_Client.src.module.rc_s660s.src.ccid_command.switch_protocol import SwitchProtocol, SwitchProtocolDataObjectTag
from SVS_Client.src.module.rc_s660s.src.ccid_command.transparent_exchange import TransparentExchange, TransparentExchangeDataObjectTag
from SVS_Client.src.module.rc_s660s.src.ccid_command.get_firmware_version import GetFirmwareVersion


def hex_str2int_list(s: str) -> list[int]:
    """
    "00 00 FF 00 11 EF ..." のような16進表記文字列を int のリストにする。
    空白・改行は無視し、大文字/小文字も区別しない。
    """
    tokens = s.split()
    ints: list[int] = []
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        # "0x" / "0X" 接頭辞があっても処理
        if t.lower().startswith("0x"):
            t = t[2:]
        ints.append(int(t, 16))
    return ints

def bit2str(bit_list:list[int]) -> str:
    return f"{' '.join(f'{bit:02X}' for bit in bit_list)}"

def show_hex(response:dict):
    print("Response:")
    print(f"ccid: {bit2str(response['ccid']['response'])}")
    print(f"apdu: {bit2str(response['apdu']['response'])}")
    print("-"*10)


def survey():
    """
    2025/12/21 解析完了:
    [ISO 14443-3AのNFC Forum Type2のUID取得の流れ]
        1) Start Transparent Session
        2) SwitchProtocol (TypeA Layer3)
        3) Tranceive (UID SELECTコマンド 0x30 0x00)
        4) RF OFF/ End Transparent Session
        以上

    [ポイント]
    Transceiveコマンドは, SwitchProtocolの直後に実行すること.
    間にRF ONを挟んだりすると, 物理コマンド(0x30のREADとか, WRITEとか )が通らなくなる.
    公式ドキュメントの代表的なシーケンスには, 
        SwitchProtocol → Transmission/Reception Flag → RF On → Transceive
    と記載があるが, 従ってはいけない
    TypeAで物理コマンドを実行する場合は, 
        SwitchProtocol → Transceive
    とすること.
    """

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

    is_debug=False

    rcs660s.create_command_frame(
        ccid_command=ResetDevice(),
        is_debug=is_debug
    )
    rcs660s.send_command_frame()
    response = rcs660s.uart.read(128)
    print("0) ResetDevice")
    print(response)
    # print("\n")


    # 1) Start Transparent Session
    rcs660s.create_command_frame(
        ccid_command=ManageSession(
            data_object_tag=ManageSessionDataObjectTag.START_TRANSPARENT_SESSION
        ), is_debug=is_debug
    )
    rcs660s.send_command_frame()
    response = rcs660s.read_response(is_debug=False)
    print("1) Start Transparent Session")
    print(response)
    print("\n")


    # 2) SwitchProtocol (TypeA/B/F)
    print("2) SwitchProtocol (TypeA/B/F)")
    rcs660s.create_command_frame(
        ccid_command=SwitchProtocol(
            data_object_tag=SwitchProtocolDataObjectTag.SWITCH_TO_TYPEA_LAYER3
        ), is_debug=True
    )
    rcs660s.send_command_frame()
    response = rcs660s.read_response(is_debug=False)
    print(response)
    show_hex(response)
    print("\n")


    print("3) polling")
    # タイムアウト時間 設定 (公式ドキュメントによると精度は1ms)
    timeout_ms = 10 # ms, 3ms未満はIDmを読み取れない. そのため3msが最速設定.
    timer_command=list((timeout_ms*1000).to_bytes(4, 'little')) # 待機時間[μs], リトルエンディアン
    timer_ccid=TransparentExchangeDataObjectTag.TIMER(timer_command)

    polling_command=[0x30,0x00] # TypeA NFC Forum Type 2のUID取得コマンド (0x30でSELECT, 0x00でページバイト指定)
    polling_ccid=TransparentExchangeDataObjectTag.TRANSCEIVE(polling_command)
    rcs660s.create_command_frame(
        ccid_command=TransparentExchange(
            data_object_tag=(
                timer_ccid
                + polling_ccid
            )
        ), is_debug=True
    )
    rcs660s.send_command_frame()

    response = rcs660s.read_response(is_debug=True) # Trueだとloop問い合わせの中身をprintする
    print(response)
    # show_hex(response)
    print("\n")



    print("通信終了")
    print("4) RF OFF/End Transparent Session")
    rcs660s.create_command_frame(
        ccid_command=ManageSession(
            data_object_tag=(
                ManageSessionDataObjectTag.RF_OFF
                + ManageSessionDataObjectTag.END_TRANSPARENT_SESSION
            )
        ), is_debug=is_debug
    )
    rcs660s.send_command_frame()
    # response = rcs660s.read_response(is_debug=False)
    print("raw: ", bit2str(rcs660s.uart.read(128)))

    # print_response(response)
    # print("\n")

    rcs660s.uart.close()



def survey2():
    """
    なんのコマンドが必要なのかを調べる実験用関数
    """

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

    is_debug=False


    def start_transparent_session():
        print("1) Start Transparent Session")
        start_transparent_session="00 00 FF 00 11 EF 6B 07 00 00 00 00 03 00 00 00 FF C2 00 00 02 81 00 47 00"
        rcs660s.command_frame=hex_str2int_list(start_transparent_session)
        rcs660s.send_command_frame()
        response = rcs660s.read_response(is_debug=False)
        print(response)
        print("\n")

    def transmission_reception_flag():
        print("2) transmission reception flag")
        transmission_reception_flag="00 00 FF 00 13 ED 6B 09 00 00 00 00 05 00 00 00 FF C2 00 01 04 90 02 00 1C 13 00"
        rcs660s.command_frame=hex_str2int_list(transmission_reception_flag)
        rcs660s.send_command_frame()
        response = rcs660s.read_response(is_debug=False)
        print(response)
        print("\n")

    def transmission_bit_framing():
        print("3) transmission bit framing")
        transmission_bitframing="00 00 FF 00 12 EE 6B 08 00 00 00 00 06 00 00 00 FF C2 00 01 03 91 01 00 30 00"
        rcs660s.command_frame=hex_str2int_list(transmission_bitframing)
        rcs660s.send_command_frame()
        response = rcs660s.read_response(is_debug=False)
        print(response)
        print("\n")

    def set_parameters():
        print("4) set parameters")
        set_parameters="00 00 FF 00 15 EB 6B 0B 00 00 00 00 07 00 00 00 FF C2 00 00 06 FF 6E 03 05 01 89 BD 00"
        rcs660s.command_frame=hex_str2int_list(set_parameters)
        rcs660s.send_command_frame()
        response = rcs660s.read_response(is_debug=False)
        print(response)
        print("\n")
    def rf_on():
        print("5) rf on")
        rf_on="00 00 FF 00 12 EE 6B 08 00 00 00 00 08 00 00 00 FF C2 00 00 02 84 00 00 3E 00"
        rcs660s.command_frame=hex_str2int_list(rf_on)
        rcs660s.send_command_frame()
        response = rcs660s.read_response(is_debug=False)
        print(response)
        print("\n")

    def switch_protocol():
        print("6) switch protocol")
        switch_protocol="00 00 FF 00 13 ED 6B 09 00 00 00 00 0A 00 00 00 FF C2 00 02 04 8F 02 00 03 27 00"
        rcs660s.command_frame=hex_str2int_list(switch_protocol)
        rcs660s.send_command_frame()
        response = rcs660s.read_response(is_debug=False)
        print(response)
        print("\n")
    
    def polling():
        print("7) polling")
        polling="00 00 FF 00 1A E6 6B 10 00 00 00 00 0B 00 00 00 FF C2 00 01 0A 5F 46 04 10 27 00 00 95 02 30 00 07 00"
        rcs660s.command_frame=hex_str2int_list(polling)
        rcs660s.send_command_frame()
        response = rcs660s.read_response(is_debug=False)
        # print(response)
        show_hex(response)
        print("\n")

    def rf_off():
        print("8) rf off")
        rf_off="00 00 FF 00 12 EE 6B 08 00 00 00 00 0E 00 00 00 FF C2 00 00 02 83 00 00 39 00"
        rcs660s.command_frame=hex_str2int_list(rf_off)
        rcs660s.send_command_frame()
        response = rcs660s.read_response(is_debug=False)
        print(response)
        print("\n")

    def end_transparent_session():
        print("9) end transparent session")
        end_transparent_session="00 00 FF 00 11 EF 6B 07 00 00 00 00 0D 00 00 00 FF C2 00 00 02 82 00 3C 00"
        rcs660s.command_frame=hex_str2int_list(end_transparent_session)
        rcs660s.send_command_frame()
        response = rcs660s.read_response(is_debug=False)
        print(response)
        print("\n")



    rcs660s.create_command_frame(
        ccid_command=ResetDevice(),
        is_debug=is_debug
    )
    rcs660s.send_command_frame()
    response = rcs660s.uart.read(128)
    print("0) ResetDevice")
    print(response)
    # print("\n")


    print("0) abort")
    abort="00 00 FF 00 0A F6 72 00 00 00 00 00 01 00 00 00 8D 00"
    rcs660s.command_frame=hex_str2int_list(abort)
    rcs660s.send_command_frame()
    response = rcs660s.uart.read(128)
    print(response)
    print("\n")


    start_transparent_session()
    # transmission_reception_flag()
    # transmission_bit_framing()
    # set_parameters()
    rf_on()
    switch_protocol()
    polling()
    rf_off()
    end_transparent_session()


    rcs660s.uart.close()





if __name__=="__main__":
    survey()
    # survey2()
    # main()