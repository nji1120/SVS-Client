"""
テスト項目
・並列Pasori：テスト通過
・並列カラーセンサ：テスト通過
・並列フォトダイオード：テスト通過
"""

from pathlib import Path
import sys
ROOT=Path(__file__).parent.parent.parent.parent
sys.path.append(str(ROOT))
import yaml
import time
import json

from SVSv2 import Sensors, sleep


def main():

    with open(Path(__file__).parent/"execonf.yml", "r") as f:
        execonf=yaml.load(f,Loader=yaml.SafeLoader)

    #>> センサの登録 >>
    sensors=Sensors()
    for key,val in execonf["usb_port"].items():
        sensors.add_sensor(
            port_name=key,
            port_config=val,
            frequency=execonf["protocol"]["frequency"]
        )


    sleep_time=1.0/execonf["protocol"]["frequency"]*10**9
    count=0
    while True:
        try:
            prev_time=time.time_ns()
            values=sensors.read()
            print(f"trial[{count}]",json.dumps(values,indent=4))
        except Exception as e:
            print(e)
            break
        count+=1
        sleep(prev_time,sleep_time)

if __name__=="__main__":
    main()