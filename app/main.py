from pathlib import Path
import sys
ROOT=Path(__file__).parent.parent.parent
sys.path.append(str(ROOT))
import yaml
import time
import json
from socket import socket,AF_INET,SOCK_DGRAM

from SVS_Client import Sensors, sleep, generate_execonf_using_sensormap, judge_state ,PortStateStabilizer


def main():
    # >> 実行configの生成 >>
    generate_execonf_using_sensormap(
        Path(__file__).parent/"conf.yml",
        Path(__file__).parent.parent/"model/sensor_map.csv",
        Path(__file__).parent/"execonf.yml"
    )

    with open(Path(__file__).parent/"execonf.yml", "r") as f:
        execonf=yaml.load(f,Loader=yaml.SafeLoader)


    #>> 接続確立 >>
    protocol=execonf["protocol"]
    freq=protocol["frequency"]
    sock=socket(AF_INET,SOCK_DGRAM)
    sock.settimeout(1.0/freq*10**3)
    #>> 接続確立 >>


    #>> センサの登録 >>
    sensors=Sensors()
    for key,val in execonf["usb_port"].items():
        sensors.add_sensor(
            port_name=key,
            port_config=val,
            frequency=freq
        )
    #>> センサの登録 >>


    #>> センサ値安定化クラス >>
    port_nums=len(execonf["usb_port"].keys())
    port_start_index=int(list(execonf["usb_port"].keys())[0].replace("port",""))
    port_state_stabilizer=PortStateStabilizer(
        trajectory_nums=execonf["state_stabilizer"]["trajectory_nums"],
        port_nums=port_nums,
        port_start_index=port_start_index
    )
    #>> センサ値安定化クラス >>


    sleep_time=1.0/freq*10**9
    count=0
    while True:
        try:
            prev_time=time.time_ns()

            values=sensors.read()

            card_states=judge_state(values,execonf["threshold"])

            #>> modeによる値の安定化 >>
            port_state_stabilizer.add_trajectory(card_states)
            stable_states=port_state_stabilizer.get_stable_states()
            #>> modeによる値の安定化 >>

            sock.sendto(
                json.dumps(stable_states).encode(),
                (protocol["server"],int(protocol["port"]))
            )

            print(f"\ntrial[{count}]"+"-"*40)
            print(json.dumps(values,indent=4))
            print(json.dumps(stable_states,indent=4))

        except Exception as e:
            print(e)
            sock.close()
            break

        count+=1
        sleep(prev_time,sleep_time)


if __name__=="__main__":
    main()