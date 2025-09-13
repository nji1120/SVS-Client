"""
ADコンバータ+photo-diodeを制御するクラス
・ADコンバータ : MCP3008
・photo-diode : 503PDD2E-3A
"""

from spidev import SpiDev

class PhotoDiode():
    """
    SPIバス1つにつき、1つインスタンスを作成する
    つまり、3つの8ch A/Dコンバータであれば、3つのインスタンスを作成する
    """

    def __init__(self,bus,device,vref,max_speed_hz,spi_mode, channel_mapping:dict):
        """
        :param bus: バス番号(=CS線番号) CS線がGPIO8なら0. GPIO7なら1になる
        :param device: デバイス番号. そのバスに接続されたデバイスの番号 (どこから確認するかは知らない)
        :param vref
        :param max_speed_hz: 最大周波数 [Hz]
        :param spi_mode: SPIのモード 大抵データシートに書いてある
        :param channel_mapping: チャンネルとアドレスの対応, chN : N (0~7の整数)
            {
                'ch0': 0,
                'ch1': 1,
                ...
                'ch7': 7
            }
        """

        self.spi=SpiDev()
        self.spi.open(bus, device)  # bus0,cs0
        self.spi.max_speed_hz = max_speed_hz  # kHz 必ず指定する
        self.spi.mode=spi_mode
        self.vref=vref
        self.channel_mapping=channel_mapping

    def _readAdc(self,channel_name:str):
        channel=int(self.channel_mapping[channel_name])
        adc = self.spi.xfer2([1, (8 + channel) << 4, 200])
        data = ((adc[1] & 3) << 8) + adc[2]
        return data
    
    def _convertVolts(self, data):
        volts = (data * self.vref) / float(1023)
        return volts
    
    def read(self,channel_name:str):
        """
        チャンネルの電圧を読み取る関数
        :param channel_name: mappingに対応するchannel名, ex) 'ch0'
        """
        data=self._readAdc(channel_name)
        volt=self._convertVolts(data)
        return volt
