"""
MUX+カラーセンサを制御するクラス
・MUX : PCA9548APW
・カラーセンサ : S11059-02DT
"""

from enum import Enum
from smbus2 import SMBus
import time

from .s11059_02dt_control_command import S11059_02DT_ControlCommand, GAIN, INTEGRATION_MODE, INTEGRATION_TIME


class ColorSensorRGBReadType(Enum):
    DEFAULT="raw" # センサ値をそのまま帰す
    RATIO="ratio" #rgb比率+IRの値を返す


class ColorSensor():
    """
    バス1つにつき, 1インスタンスを作成する
    """

    BUS_NUM=1 #バス番号. 基本は1
    I2C_BUS=SMBus(BUS_NUM) #クラスで共通のバスを使う

    def __init__(self, 
        mux_address,slave_address, channel_mapping:dict, 
        read_type:ColorSensorRGBReadType=ColorSensorRGBReadType.DEFAULT
    ):
        """
        :param mux_address: マルチプレクサのアドレス
        :param slave_address: カラーセンサのアドレス
        :param channel_mapping: チャンネルとアドレスの対応, chN : 1<<N
            {
                'ch0': 0b00000001,
                'ch1': 0b00000010,
                ...
                'ch7': 0b10000000
            }
        :param read_type: 読み取りタイプ
        """
        self.master_addr=mux_address
        self.slave_addr=slave_address
        self.channel_mapping=channel_mapping
        self.read_type=read_type
        self.control_command=S11059_02DT_ControlCommand(
            gain=GAIN.HIGH,
            integration_mode=INTEGRATION_MODE.STATIC, # 固定モード
            integration_time=INTEGRATION_TIME.MID_LONG, # 22.4ms
        )


    def read(self, channel_name:str):
        """
        channel名で指定して, 特定のチャンネルを開ける
        :param channel_name: チャンネル名, ex) 'ch0'
        :param return_ratio: 比率を返すかどうか. True → rgb比率, False → センサ値
        """
        self.__select_channel(channel_name) # MUXのチャンネル選択
        data=self.__get_sensor_data() # センサのデータ読み取り
        rgbi=self.__calculate_sensor_data(data) # ビットデータをルクスに変換

        # 比率を取得する場合は, RGBの比率計算を行う
        if self.read_type==ColorSensorRGBReadType.RATIO:
            r_ratio, g_ratio, b_ratio=self.__rgb_ratio(rgbi["R"], rgbi["G"], rgbi["B"])
            rgbi["R"]=r_ratio
            rgbi["G"]=g_ratio
            rgbi["B"]=b_ratio

        return rgbi
    

    def close_bus(self):
        ColorSensor.I2C_BUS.close()


    def __rgb_ratio(self, r,g,b):
        """
        各成分の合計で割って正規化比率を計算する
        """
        total=r+g+b
        return r/total, g/total, b/total



    def __calculate_sensor_data(self, data:list):
        """
        センサのデータを計算する
        """
        rgbi_a=[117.0,85.0,44.8,30.0] #センサのカウントとルクスの係数 (HIGHのとき)
        rgbi_key=["R","G","B","IR"]
        rgbi={}
        for i in range(4):
            rgbi[rgbi_key[i]]=((data[2*i]<<8)+data[2*i+1])/rgbi_a[i] #センサ値をルクスに変換
            # print(f"count {rgbi_key[i]}: {((data[2*i]<<8)+data[2*i+1])}")
        return rgbi


    def __get_sensor_data(self):
        """
        センサのデータを読み取る
        """

        # >> センサのリセット >>
        ColorSensor.I2C_BUS.write_byte_data(
            self.slave_addr,
            register=0x00, # 0x00レジスタにリセットコマンドを送信
            value=self.control_command.get_reset_command()
        )
        # print(f"リセットコマンド: {bin(self.control_command.get_reset_command())}")

        # >> センサのスタート >>
        ColorSensor.I2C_BUS.write_byte_data(
            self.slave_addr,
            register=0x00, # 0x00レジスタにスタートコマンドを送信
            value=self.control_command.get_start_command()
        )
        # print(f"スタートコマンド: {bin(self.control_command.get_start_command())}")
        
        sleep_rate=1.2 # 適当な係数
        time.sleep(self.control_command.get_integration_seconds*sleep_rate) # 積分時間のsleep_rate倍程度の時間待つ

        # >> センサのデータ読み取り >>
        data=ColorSensor.I2C_BUS.read_i2c_block_data(
            self.slave_addr,
            register=0x03, # 0x03レジスタから8バイト分のデータ(RGB+IR)を読み取る
            length=8
        )

        return data


    def __select_channel(self, channel_name:str):
        """
        チャンネルを選択する
        """
        channel=self.channel_mapping[channel_name]
        ColorSensor.I2C_BUS.write_byte_data(
            i2c_addr=self.master_addr,
            register=0x00,
            value=channel
        )

    
