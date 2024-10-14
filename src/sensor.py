from smbus2 import SMBus
import spidev

from .libpafe_py import *
from .utils import fix_idm


class Sensors():
    def __init__(self):

        self.sensors={}
        self.photo_diodes={}

    def add_sensor(self,port_name:str,port_config:dict,frequency):
        """
        センサーを追加する
        :param port_name
        :param port_config
            multiplexer:
                master: 112
                channel: 1
                slave: 42
            photo_diode:
                bus: 0
                channel: 0
                device: 0
                vref: 3.34
                max_speed_hz: 75000
                spi_mode: 0
        :param frequency
        """

        pasori=Pasori(port_name=port_name,frequency=frequency)
        color_sensosr=ColorSensor(
            port_config["multiplexer"]["master"],
            port_config["multiplexer"]["channel"],
            port_config["multiplexer"]["slave"]
        )

        ph_conf=port_config["photo_diode"]
        if not ph_conf["bus"] in self.photo_diodes.keys():
            self.photo_diodes[ph_conf["bus"]]=PhotoDiode(
                ph_conf["bus"],
                ph_conf["device"],
                ph_conf["vref"],
                ph_conf["max_speed_hz"],
                ph_conf["spi_mode"]
            )

        self.sensors[port_name]={
            "pasori":pasori,
            "color_sensor":color_sensosr,
            "photo_diode":self.photo_diodes[ph_conf["bus"]],
            "ph_channel":ph_conf["channel"]
        }

    def read(self):

        values={}
        for key,val in self.sensors.items():
            values[key]={
                "pasori":val["pasori"].read(),
                "color_sensor":val["color_sensor"].read(),
                "photo_diode":val["photo_diode"].read(val["ph_channel"])
            }

        return values
    
    def __del__(self):

        for key,val in self.sensors.items():
            pasori_close(val["pasori"].pasori)

        for key,photo_diode in self.photo_diodes.items():
            photo_diode.spi.close()

        keys=list(self.sensors.keys())
        self.sensors[keys[0]]["color_sensor"].close_bus()

        

class Pasori():
    """
    pasori1つにつき、1つのインスタンスを作成する
    """

    def __init__(self,port_name:str,frequency):
        self.pasori=pasori_open_port(port_name=port_name.encode("utf-8"))
        timeout=(1/frequency*10**3)#ms 周期分時間経過したら次に行く
        pasori_set_timeout(self.pasori,int(timeout))

    def read(self):
        felica=felica_polling(self.pasori)
        idm=felica_get_id(felica)
        fixed_idm=fix_idm(idm.value)
        free(felica)
        return fixed_idm
    

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


class PhotoDiode():
    """
    SPIバス1つにつき、1つインスタンスを作成する
    つまり、3つの8ch A/Dコンバータであれば、3つのインスタンスを作成する
    """

    def __init__(self,bus,device,vref,max_speed_hz,spi_mode):
        """
        :param bus: バス番号(=CS線番号) CS線がGPIO8なら0. GPIO7なら1になる
        :param device: デバイス番号. そのバスに接続されたデバイスの番号 (どこから確認するかは知らない)
        :param vref
        :param max_speed_hz: 最大周波数 [Hz]
        :param spi_mode: SPIのモード 大抵データシートに書いてある
        """

        self.spi=spidev.SpiDev()
        self.spi.open(bus, device)  # bus0,cs0
        self.spi.max_speed_hz = max_speed_hz  # kHz 必ず指定する
        self.spi.mode=spi_mode
        self.vref=vref

    def _readAdc(self,channel):
        adc = self.spi.xfer2([1, (8 + channel) << 4, 200])
        data = ((adc[1] & 3) << 8) + adc[2]
        return data
    
    def _convertVolts(self, data):
        volts = (data * self.vref) / float(1023)
        return volts
    
    def read(self,channel):
        """
        チャンネルの電圧を読み取る関数
        :param channel: 0~7のintを指定
        """
        data=self._readAdc(channel)
        volt=self._convertVolts(data)
        return volt
