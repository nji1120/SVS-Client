from pathlib import Path
ROOT=Path(__file__).parent.parent.parent
import sys
sys.path.append(str(ROOT))

import traceback
from socket import socket,AF_INET,SOCK_DGRAM
import pandas as pd
import yaml
import time
from math import ceil

from src.module.tc4052b import TC4052B
from src.module.rc_s660s.src.rcs660s import RCS660S
from src.module.rc_s660s.src.manager.rcs660s_manager_typeA_14443_3A import RCS660SManagerTypeA144433A

from src.utils.sleep import sleep



def main():
    """
    TypeA 14443-3A の読み取りテスト
    1機あたり最大17Hzまで出せる
    """
    config_yaml=yaml.safe_load(open(Path(__file__).parent / "conf.yaml"))


    # 接続設定
    conf_connection=config_yaml["connection"]
    frequency=conf_connection["frequency"]

    sock=socket(AF_INET,SOCK_DGRAM)
    sock.settimeout(1.0/frequency*10**3)

    # MUXとrcs660sのインスタンス化
    print("[Init] rcs660s")
    conf_rcs660s=config_yaml["rcs660s"]
    mapping_rcs660s=pd.DataFrame(conf_rcs660s["mapping"]).T

    tc4052b=TC4052B(mapping=mapping_rcs660s)
    print(f"switch channel: {config_yaml['reader_channels'][0]}")
    tc4052b.switch_channel(config_yaml["reader_channels"][0])
    
    rcs660s=RCS660S(
        port=conf_rcs660s["port"], 
        baudrate=conf_rcs660s["baudrate"], 
        timeout_fps=conf_rcs660s["timeout_fps"]
    )
    rcs660s_manager=RCS660SManagerTypeA144433A(rcs660s=rcs660s,is_debug=True)
    rcs660s_manager.setup_device()

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

            response=rcs660s_manager.polling()
            if cnt%frequency==0:
                print(f"cnt: {cnt}, elapsed_time: {elapsed_time:.3f}s",response)

            sleep(previous_time,sleep_time)
            cnt+=1
            elapsed_time=(time.time_ns()-start_time)*10**-9
        except Exception as e:
            rcs660s_manager.close()
            print(traceback.format_exc())
            break
    # >> 読み取り >>

    print("end")


if __name__ == "__main__":
    main()