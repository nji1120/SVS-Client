"""
カードリーダ全体を管理するクラス
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import time
from enum import Enum
from copy import deepcopy

from ..module.tc4052b import TC4052B
from ..module.rc_s660s.src.rcs660s_manager import RCS660SManager
from ..module.color_sensor import ColorSensor
from ..module.photo_diode import PhotoDiode


class ColorSensorIRReadType(Enum):
    RAW="raw" # センサの値そのまま
    DIFFERENCE="difference" #カードが無いときの値(baseline)からの差分

class PhotoDiodeReadType(Enum):
    RAW="raw" # センサの値そのまま
    DIFFERENCE="difference" #カードが無いときの値(baseline)からの差分

class CardReaderManager:

    def __init__(
        self,
        tc4052b:TC4052B,
        rcs660s_manager:RCS660SManager,
        color_sensor:ColorSensor,
        photo_diode:PhotoDiode,
        channel_names:list[str],
        delta_time:float=0.00,
        photo_diode_read_type:PhotoDiodeReadType=PhotoDiodeReadType.RAW,
        color_sensor_ir_read_type:ColorSensorIRReadType=ColorSensorIRReadType.RAW,
    ):
        """
        :param tc4052b: TC4052B, RCS660Sのチャンネル選択用MUX
        :param rcs660s_manager: RCS660SManager
        :param color_sensor: ColorSensor
        :param photo_diode: PhotoDiode
        :param channel_names: チャンネル名のリスト(全センサ種類間で共通とする), ex) ['ch0', 'ch1', 'ch2',...]
        :param delta_time: 各センサの読み取り間隔 [s]
        :param photo_diode_read_type: PhotoDiodeReadType
        :param color_sensor_ir_read_type: ColorSensorIRReadType
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
        self.color_sensor_ir_read_type=color_sensor_ir_read_type
        self.color_sensor_ir_baseline={ch_name:0 for ch_name in channel_names} # カードがないときのcolor sensor IR値のベースライン

        self.photo_diode=photo_diode
        self.photo_diode_baseline={ch_name:0 for ch_name in channel_names} # カードがないときのphoto diode値のベースライン
        self.photo_diode_read_type=photo_diode_read_type

        self.channel_names=channel_names
        self.delta_time=delta_time


        # read_typeがdifferenceの場合はbaselineを取得する
        self.is_difference_read=(
            self.photo_diode_read_type==PhotoDiodeReadType.DIFFERENCE 
            or self.color_sensor_ir_read_type==ColorSensorIRReadType.DIFFERENCE
        )
        if self.is_difference_read:
            sensor_values:dict
            sensor_values=self.read()
            self.__get_value_baseline(sensor_values)


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


        # 差分計算が必要な場合はbaselineを取得し、差分を計算する
        if self.is_difference_read:
            self.__get_value_baseline(sensor_values) # baselineを取得
            sensor_values=self.__calculate_value_difference(sensor_values) # 差分を計算

        
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


    def __get_value_baseline(self, sensor_values:dict) -> None:
        """
        カードが無いときのphoto diode値をbaselineとして保持する. デフォルトは0.
        :param sensor_values: {
            ch0: {
                felica: XXXX, 
                color_sensor: {R:XX, G:XX, B:XX, IR:XX}, 
                photo_diode:XX}
            }, ...
        """
        for ch_name, sensor_dict in sensor_values.items():
            if sensor_dict["felica"] is None:
                if self.photo_diode_read_type==PhotoDiodeReadType.DIFFERENCE:
                    self.photo_diode_baseline[ch_name]=sensor_dict["photo_diode"]
                if self.color_sensor_ir_read_type==ColorSensorIRReadType.DIFFERENCE:
                    self.color_sensor_ir_baseline[ch_name]=sensor_dict["color_sensor"]["IR"]
    

    def __calculate_value_difference(self, sensor_values:dict) -> dict:
        """
        baselineからの差分を返す
        """
        out = deepcopy(sensor_values)
        for ch_name, sensor_dict in out.items():
            if self.photo_diode_read_type==PhotoDiodeReadType.DIFFERENCE:
                sensor_dict["photo_diode"] -= self.photo_diode_baseline[ch_name]
            if self.color_sensor_ir_read_type==ColorSensorIRReadType.DIFFERENCE:
                sensor_dict["color_sensor"]["IR"] -= self.color_sensor_ir_baseline[ch_name]
        return out
    

    def __del__(self):
        self.rcs660s_manager.close()
        self.color_sensor.close_bus()