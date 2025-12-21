"""
2in2outのMUXを制御するクラス
基本的にUART用のMUXとしての利用が多い
(と思われる. I2CやSPI用のようにUARTは専用のMUXがあんまり見当たらないため)
"""

from RPi import GPIO
import pandas as pd


# マッピングテーブルに入力されるであろうキーリスト
# (※基本的にH/Lを入れるつもりではあるけど...)
HIGH=1
LOW=0
KEY_LIST_HIGH=["HIGH","HI","H","ON","TRUE","T",1,True]
KEY_LIST_LOW=["Low","LO","L","OFF","FALSE","F",0,False]
KEY_LIST_NONE=["NONE","N","N/A","","NAN",None] # pd.NAは含めない.含めるとinによる検索でエラー吐く
def CHECK_HIGH_LOW(key) -> int|None:

    key=key.upper() if type(key) is str else key
    if pd.isna(key):
        return None
    elif key in KEY_LIST_NONE:
        return None

    elif key in KEY_LIST_HIGH:
        return HIGH
    elif key in KEY_LIST_LOW:
        return LOW
    else:
        raise ValueError(f"Invalid key: {key}")


class AddressPin:
    """
    GPIOのwrapperクラス
    """
    def __init__(self, pin:int):
        self.pin=int(pin)
        GPIO.setup(self.pin, GPIO.OUT)
    
    def set_high(self):
        GPIO.output(self.pin, GPIO.HIGH)
    
    def set_low(self):
        GPIO.output(self.pin, GPIO.LOW)

    def noop(self):
        """
        何もしない(noop:no operation)
        多段MUXで特にH/Lの指定が必要ないときに使う
        """
        pass
    
    def __del__(self):
        GPIO.cleanup(self.pin)


class TC4052B:
    """
    TC4052Bを制御するクラス
    mappingテーブルを受け取って, 指定のchannelを開けるだけ
    """


    def __init__(self, mapping:pd.DataFrame):
        """
        :param mapping: 
            index: channel_name (開けるチャンネル名)
            columns: gpio_pins (アドレス指定に使うgpioのピン番号)
            rows: LOW, HIGH, LOW, LOW,... (各GPIOのHIGH/LOW)

            ex)
                 5, 6, 13, 19,
            ch0: LOW, HIGH, LOW, LOW,
            ch1: LOW, LOW, HIGH, LOW,
            ...
        """
        GPIO.setmode(GPIO.BCM) # GPIOのピン番号を指定するモード(!!物理的な配置番号じゃないから注意!!)

        # gpioピン
        address_pins=[
            AddressPin(pin) for pin in mapping.columns
        ] 

        # channel切り替え用のswitchを作成
        self.channel_switch=self.__create_channel_switch(
            address_pins=address_pins,
            mapping=mapping,
        )



    def switch_channel(self, channel_name:str) -> None:
        """
        channel切り替え関数.
        mappingCSVに書いていたchannel_nameを指定するだけ
        """
        try:
            # 各GPIOのHIGH/LOWを指定
            set_address_pins=[set_high_low() for set_high_low in self.channel_switch[channel_name]]
        except KeyError:
            raise ValueError(f"Invalid channel name: {channel_name}")
        except Exception as e:
            raise ValueError(f"Error switching channel: {e}")


    # def __del__(self):
    #     GPIO.cleanup()


    def __create_channel_switch(
        self, 
        address_pins:list[AddressPin], 
        mapping:pd.DataFrame,
    ) -> dict:
        """
        csvのmappingから, 関数でchannel切り替えができるswitchを作成する.
        usage:
            # ch0を開ける. こんな感じで対応するchannelをdictのキーで指定して, 中の関数を実行すれば良い 
            [func() for func in channel_switch["ch0"]] 
            ...
        """
        channel_switch={}
        for idx, row in mapping.iterrows():

            channel_name=idx
            high_low_arrangement=[]
            for address_pin,key in zip(address_pins,row.values):
                # 関数のmapping
                func_map={
                    None: address_pin.noop,
                    HIGH: address_pin.set_high,
                    LOW: address_pin.set_low,
                }
                
                high_low=CHECK_HIGH_LOW(key)
                try:
                    high_low_arrangement.append(func_map[high_low])
                except Exception as e:
                    raise ValueError(f"Invalid high/low: {high_low} : {e}")
            
            channel_switch[channel_name]=high_low_arrangement
        
        return channel_switch

