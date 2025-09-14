"""
CardReaderManagerのテスト
"""
from pathlib import Path
ROOT=Path(__file__).parent.parent.parent
import sys
sys.path.append(str(ROOT))

import pandas as pd
import yaml
import argparse
import time

from src.reader.CardReaderManager import CardReaderManager
from src.module.tc4052b import TC4052B
from src.module.rc_s660s.src.rcs660s import RCS660S
from src.module.rc_s660s.src.rcs660s_manager import RCS660SManager
from src.module.color_sensor import ColorSensor
from src.module.photo_diode import PhotoDiode
from src.utils.sleep import sleep


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--ch", type=str, nargs="+", default=["ch4"])
    parser.add_argument("--frequency", type=float, default=4)
    args=parser.parse_args()

    confpath=Path(__file__).parent / "conf"

    # MUXとrcs660sのインスタンス化
    print("[Init] rcs660s")
    conf_rcs660s=yaml.safe_load(open(confpath / "rcs660s" / "conf.yaml"))
    mapping_rcs660s=pd.DataFrame(conf_rcs660s["mapping"]).T

    tc4052b=TC4052B(mapping=mapping_rcs660s)
    rcs660s=RCS660S(
        port=conf_rcs660s["port"], 
        baudrate=conf_rcs660s["baudrate"], 
        timeout_fps=conf_rcs660s["timeout_fps"]
    )
    rcs660s_manager=RCS660SManager(rcs660s=rcs660s)


    # ColorSensorのインスタンス化
    print("[Init] color_sensor")
    conf_color_sensor=yaml.safe_load(open(confpath / "color_sensor" / "conf.yaml"))
    color_sensor=ColorSensor(
        mux_address=conf_color_sensor["mux_address"],
        slave_address=conf_color_sensor["slave_address"],
        channel_mapping=conf_color_sensor["mapping"] # mappingは辞書とする
    )
    


    # PhotoDiodeのインスタンス化
    print("[Init] photo_diode")
    conf_photo_diode=yaml.safe_load(open(confpath / "photo_diode" / "conf.yaml"))
    photo_diode=PhotoDiode(
        bus=conf_photo_diode["bus"],
        device=conf_photo_diode["device"],
        vref=conf_photo_diode["vref"],
        max_speed_hz=conf_photo_diode["max_speed_hz"],
        spi_mode=conf_photo_diode["spi_mode"],
        channel_mapping=conf_photo_diode["mapping"] # mappingは辞書とする
    )

    print("[Init] cardreader_manager")
    cardreader_manager=CardReaderManager(
        tc4052b=tc4052b,
        rcs660s_manager=rcs660s_manager,
        color_sensor=color_sensor,
        photo_diode=photo_diode,
        channel_names=args.ch # 検出するチャンネル名をここで指定する
    )


    # >> 読み取り >>
    print("[Start] read")
    previous_time=time.time_ns()
    start_time=previous_time
    sleep_time=1/args.frequency*10**9
    cnt=0
    elapsed_time=0
    while True:
        try:
            previous_time=time.time_ns()
            sensor_values=cardreader_manager.read()
            print(f"[{cnt}] {elapsed_time:.3f}s",sensor_values)
            sleep(previous_time,sleep_time)
            cnt+=1
            elapsed_time=(time.time_ns()-start_time)*10**-9
        except Exception as e:
            print(e)
            break
    # >> 読み取り >>

    print("end")


if __name__ == "__main__":
    main()