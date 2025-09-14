from pathlib import Path
ROOT=Path(__file__).parent.parent
import sys
sys.path.append(str(ROOT))

from socket import socket,AF_INET,SOCK_DGRAM
import pandas as pd
import yaml
import json
import time

from src.reader.CardStateAnalyzer import CardStateAnalyzer
from src.reader.CardReaderManager import CardReaderManager
from src.module.tc4052b import TC4052B
from src.module.rc_s660s.src.rcs660s import RCS660S
from src.module.rc_s660s.src.rcs660s_manager import RCS660SManager
from src.module.color_sensor import ColorSensor
from src.module.photo_diode import PhotoDiode
from src.utils.sleep import sleep



def main():
    config_yaml=yaml.safe_load(open(Path(__file__).parent / "conf.yaml"))


    # 接続設定
    conf_connection=config_yaml["connection"]
    server=conf_connection["server"]
    port=conf_connection["port"]
    frequency=conf_connection["frequency"]

    sock=socket(AF_INET,SOCK_DGRAM)
    sock.settimeout(1.0/frequency*10**3)

    # MUXとrcs660sのインスタンス化
    print("[Init] rcs660s")
    conf_rcs660s=config_yaml["rcs660s"]
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
    conf_color_sensor=config_yaml["color-sensor"]
    color_sensor=ColorSensor(
        mux_address=conf_color_sensor["mux_address"],
        slave_address=conf_color_sensor["slave_address"],
        channel_mapping=conf_color_sensor["mapping"] # mappingは辞書とする
    )
    

    # PhotoDiodeのインスタンス化
    print("[Init] photo_diode")
    conf_photo_diode=config_yaml["photo-diode"]
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
        channel_names=config_yaml["reader_channels"] # 検出するチャンネル名をここで指定する
    )


    card_state_analyzer=CardStateAnalyzer(
        color_sensor_threshold=config_yaml["color-sensor"]["threshold"],
        photo_diode_threshold=config_yaml["photo-diode"]["threshold"]
    )


    # >> 読み取り >>
    print("[Start] read")
    previous_time=time.time_ns()
    start_time=previous_time
    sleep_time=1/frequency*10**9
    cnt=0
    elapsed_time=0
    while True:
        try:
            previous_time=time.time_ns()
            sensor_values=cardreader_manager.read()
            card_states=card_state_analyzer.analyze_card_state(sensor_values)
            sock.sendto(
                json.dumps(card_states).encode(),
                (server,port)
            )
            print(f"[{cnt}] {elapsed_time:.3f}s\n",sensor_values,"\n",card_states)
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