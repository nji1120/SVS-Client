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

    def __init__(self,bus,device,vref,max_speed_hz,spi_mode):
        """
        :param bus: バス番号(=CS線番号) CS線がGPIO8なら0. GPIO7なら1になる
        :param device: デバイス番号. そのバスに接続されたデバイスの番号 (どこから確認するかは知らない)
        :param vref
        :param max_speed_hz: 最大周波数 [Hz]
        :param spi_mode: SPIのモード 大抵データシートに書いてある
        """

        self.spi=SpiDev()
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
