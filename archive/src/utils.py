from pathlib import Path
import yaml
import time
import pandas as pd

def fix_idm(idm:int)->int:
    """
    libpafe+ctypesで取得したidmの順番が8ビットごとに逆だから並び替える関数  

    論理演算で並び替えているので理解不能だと思う

    ex)
        libpafe+ctypes -> 354A0F8DC0482E01

        本来           -> 012E48C08D0F4A35

   :param idm libpafeでpasoriから読み込んだIDM. 10進数のint
   :return fixed_idm 並び替えたID. 10進数のint
    """


    fixed_idm=0x0000000000000000
    for i in range(8):
        filter=0xff00000000000000>>(4*2*i)
        filtered_idm=idm&filter

        shift=4*(14-4*i)
        if shift>=0:
            fixed_idm|=(filtered_idm>>shift)
        else:
            fixed_idm|=(filtered_idm<<abs(shift))
        # print(hex(filtered_idm)[2:],hex(fixed_idm)[2:])

    return fixed_idm


def generate_execonf(conf_path:Path, outpath:Path)->None:

    with open(conf_path,"r",encoding="utf-8") as f:
        conf=yaml.load(f, Loader=yaml.SafeLoader)

    execonf={
        "protocol":{
            "type":"UDP",
            "server":conf["server"],
            "port":conf["port"],
            "frequency":conf["frequency"],
        },
        "state_stabilizer":conf["state_stabilizer"],
        "threshold":conf["threshold"],
        "usb_port":{}
    }


    #>> configからカラーセンサのアドレスリストを生成 >>
    color_sensors=[]
    mul_conf=conf["multiplexer"]
    for master_address in mul_conf["master_addresses"]:
        for i in range(mul_conf["channel_num"]):
            color_sensors+=[
                [master_address, 0b00000001<<i]
            ]
    #>> configからカラーセンサのアドレスリストを生成 >>


    #>> configからフォトダイオードのアドレスリストを生成 >>
    photo_diodes=[]
    ph_conf=conf["photo_diode"]
    for bus in ph_conf["buses"]:
        for i in range(ph_conf["channel_num"]):
            photo_diodes+=[
                [bus,i]
            ]
    #>> configからフォトダイオードのアドレスリストを生成 >>


    #>> USBポート1つずつconfigを作成 >>
    for i in range(conf["card_reader_num"]):
        
        port_name=conf["pasori"]["port_base_name"]+f"{conf['pasori']['port_base_number']+i}"
        color_sensor=color_sensors.pop(0)
        photo_diode=photo_diodes.pop(0)
        
        card_reader_conf={
            "multiplexer":{
                "master":color_sensor[0],
                "channel":color_sensor[1],
                "slave":mul_conf["slave_address"]
            },
            "photo_diode":{
                "bus":photo_diode[0],
                "channel":photo_diode[1],
                "device":ph_conf["device"],
                "vref":ph_conf["vref"],
                "max_speed_hz":ph_conf["max_speed_hz"],
                "spi_mode":ph_conf["spi_mode"]
            }
        }

        execonf["usb_port"][port_name]=card_reader_conf
    #>> USBポート1つずつconfigを作成 >>

    with open(outpath,"w",encoding="utf-8") as f:
        yaml.dump(execonf,f,default_flow_style=False,sort_keys=False)


def generate_execonf_using_sensormap(conf_path:Path,sensormap_path:Path ,outpath:Path)->None:
    """
    センサーマップを使った実行configの作成
    """

    with open(conf_path,"r",encoding="utf-8") as f:
        conf=yaml.load(f, Loader=yaml.SafeLoader)


    execonf={
        "protocol":{
            "type":"UDP",
            "server":conf["server"],
            "port":conf["port"],
            "frequency":conf["frequency"],
        },
        "state_stabilizer":conf["state_stabilizer"],
        "threshold":conf["threshold"],
        "usb_port":{}
    }


    #>> USBポート1つずつconfigを作成 >>
    sensor_map=pd.read_csv(sensormap_path)
    sensor_map.columns = sensor_map.columns.str.strip() #余計なスペースを削除
    for i in range(conf["card_reader_num"]):
        sensor_i=sensor_map.iloc[i]
        port_name=conf["pasori"]["port_base_name"]+f"{conf['pasori']['port_base_number']+i}"
        
        card_reader_conf={
            "multiplexer":{
                "master": int(sensor_i["multiplexer_addr"]),
                "channel": int(sensor_i["multiplexer_ch"]),
                "slave": int(sensor_i["color_sensor_addr"])
            },
            "photo_diode":{
                "bus": int(sensor_i["adc_bus"]),
                "channel": int(sensor_i["diode_ch"]),
                "device":0,
                "vref":3.34,
                "max_speed_hz":75000,
                "spi_mode":0
            }
        }

        execonf["usb_port"][port_name]=card_reader_conf
    #>> USBポート1つずつconfigを作成 >>

    with open(outpath,"w",encoding="utf-8") as f:
        yaml.dump(execonf,f,default_flow_style=False,sort_keys=False)



def sleep(previous_time,sleeping_time):
    """
    :param previous_time: 前回の処理時刻[ns]   
    :prama sleeping_time: 待機時間[ns]
    """

    #ビジーループは良くない.CPU稼働率が94%とか行く
    # while time.time_ns()-previous_time<sleeping_time:
    #     pass

    rest_time=sleeping_time-(time.time_ns()-previous_time) #ns
    if rest_time>0:
        time.sleep(rest_time*10**-9)



def judge_state(values:dict, threshold:dict):
    """
    カードの状態を判定する関数
    :param values
        {"port1": {
            "pasori": 85094388006619296,
            "color_sensor": {
                "R": 3,
                "G": 5,
                "B": 5,
                "IR": 2
            },
            "photo_diode": 0.0
        },...}
    :param threshold
        {color_sensor:{
            "r":{"low":1,"high":9},
            "g":{"low":1,"high":10},
            "b":{"low":1,"high":10},
            },
        photo_dioede:0.17
        }
    :return card_states
    """

    card_states={}
    for port_name,sensor_val in values.items():
        
        is_card=False if sensor_val["pasori"]==0 else True

        #>> カードがある時 >>
        if is_card:
            #>> 表裏の判定 >>
            r,g,b,ir=list(sensor_val["color_sensor"].values())
            color_th=threshold["color_sensor"]
            r_low,r_high=list(color_th["r"].values())
            g_low,g_high=list(color_th["g"].values())
            b_low,b_high=list(color_th["b"].values())

            if (r_low<=r<=r_high) and (g_low<=g<=g_high) and (b_low<=b<=b_high):
                is_front=True
            else:
                is_front=False
            #>> 表裏の判定 >>

            #>> 縦横の判定 >>
            if sensor_val["photo_diode"]<threshold["photo_diode"]:
                is_vertical=True
            else:
                is_vertical=False
            #>> 縦横の判定 >>


        #>> カードがない時 >>
        elif not is_card:
            is_front=None
            is_vertical=None


        card_states[port_name]={
            "is_card":is_card,
            "felica_id":sensor_val["pasori"],
            "is_front":is_front,
            "is_vertical":is_vertical
        }


    return card_states
