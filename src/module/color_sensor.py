"""
MUX+カラーセンサを制御するクラス
・MUX : PCA9548APW
・カラーセンサ : S11059-02DT
"""

from smbus2 import SMBus

class ColorSensor():
    """
    カラーセンサ1つにつき、1つのインスタンスを作成する
    """

    BUS_NUM=1 #バス番号. 基本は1
    I2C_BUS=SMBus(BUS_NUM) #クラスで共通のバスを使う

    def __init__(self, master_address,channel,slave_address):
        self.master_addr=master_address
        self.channel=channel
        self.slave_addr=slave_address

        self.__select_channel()

        # >> センサのスリープ解除と設定変更 >>
        ColorSensor.I2C_BUS.write_byte_data(
            self.slave_addr,
            register=0x00,
            value=0x80
        )

        ColorSensor.I2C_BUS.write_byte_data(
            self.slave_addr,
            register=0x00,
            value=0x0b
        )
        # << センサのスリープ解除と設定変更 <<


    def __select_channel(self):
        """
        チャンネルを選択する
        """
        ColorSensor.I2C_BUS.write_byte_data(
            i2c_addr=self.master_addr,
            register=0x00,
            value=self.channel
        )

    
    def read(self):

        self.__select_channel()
        data=ColorSensor.I2C_BUS.read_i2c_block_data(
            self.slave_addr,
            register=0x03,
            length=8
        )

        rgbi_a=[117.0,85.0,44.8,30.0] #センサのカウントとルクスの係数
        rgbi_key=["R","G","B","IR"]
        rgbi={}
        for i in range(4):
            rgbi[rgbi_key[i]]=int(((data[2*i]<<8)+data[2*i+1])/rgbi_a[i]) #センサ値をルクスに変換

        return rgbi
    
    def close_bus(self):
        ColorSensor.I2C_BUS.close()

