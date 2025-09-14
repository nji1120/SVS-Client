"""
カードリーダ全体を管理するクラス
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import time

from ..module.tc4052b import TC4052B
from ..module.rc_s660s.src.rcs660s_manager import RCS660SManager
from ..module.color_sensor import ColorSensor
from ..module.photo_diode import PhotoDiode


class CardReaderManager:

    def __init__(
        self,
        tc4052b:TC4052B,
        rcs660s_manager:RCS660SManager,
        color_sensor:ColorSensor,
        photo_diode:PhotoDiode,
        channel_names:list[str],
        delta_time:float=0.00
    ):
        """
        :param tc4052b: TC4052B, RCS660Sのチャンネル選択用MUX
        :param rcs660s_manager: RCS660SManager
        :param color_sensor: ColorSensor
        :param photo_diode: PhotoDiode
        :param channel_names: チャンネル名のリスト(全センサ種類間で共通とする), ex) ['ch0', 'ch1', 'ch2',...]
        :param delta_time: 各センサの読み取り間隔 [s]
        """

        # RCS660Sの初期化(終わってない場合)
        self.tc4052b=tc4052b
        self.rcs660s_manager=rcs660s_manager
        if not self.rcs660s_manager.is_setup:
            ch_tmp=channel_names[0] # とりあえず初期化用のチャンネル選ぶ
            self.tc4052b.switch_channel(ch_tmp)
            time.sleep(delta_time)
            self.rcs660s_manager.reset_device()
            self.rcs660s_manager.setup_device()

        self.color_sensor=color_sensor

        self.photo_diode=photo_diode

        self.channel_names=channel_names
        self.delta_time=delta_time


    def read(self) -> dict:

        # バスごとにスレッドで並列実行する
        future_results=[]
        with ThreadPoolExecutor(max_workers=3) as executor:
            future=[
                executor.submit(self.__read_rcs660s),
                executor.submit(self.__read_color_sensor),
                executor.submit(self.__read_photo_diode)
            ]
            for future in as_completed(future):
                out=future.result()
                future_results.append(out)


        # チャンネルごとに結果をまとめる
        sensor_values=defaultdict(dict)
        for result in future_results:
            for ch_name, sensor_dict in result.items():
                for sensor, value in sensor_dict.items():
                    sensor_values[ch_name][sensor] = value
        sensor_values=dict(sensor_values)

        
        return sensor_values


    def __read_rcs660s(self):
        out={}
        for channel_name in self.channel_names:
            self.tc4052b.switch_channel(channel_name) # RCS660Sのチャンネル選択
            time.sleep(self.delta_time) # ちょっとだけ待つ
            out[channel_name]={
                "felica":self.rcs660s_manager.polling()["idm"]
            }
        return out

    def __read_color_sensor(self):
        out={}
        for channel_name in self.channel_names:
            out[channel_name]={
                "color_sensor":self.color_sensor.read(channel_name)
            }
            time.sleep(self.delta_time) # ちょっとだけ待つ
        return out

    def __read_photo_diode(self):
        out={}
        for channel_name in self.channel_names:
            out[channel_name]={
                "photo_diode":self.photo_diode.read(channel_name)
            }
            time.sleep(self.delta_time) # ちょっとだけ待つ
        return out
    

    def __del__(self):
        self.rcs660s_manager.close()
        self.color_sensor.close_bus()