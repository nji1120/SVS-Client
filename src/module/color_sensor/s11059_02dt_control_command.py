from enum import Enum



# --- S11059_02DTのレジスタ0x00に設定するコントロールコマンド. これを8bitに組み立てて設定する ---
class ADC_RESET(Enum):
    """
    BIT07: ADCリセット信号
    """
    RESET=1
    START=0

class SLEEP(Enum):
    """
    BIT06: スリープモード信号
    """
    SLEEP=1 # スリープモード
    WAKEUP=0 #動作モード

class GAIN(Enum):
    """
    BIT03: ゲイン設定信号
    """
    HIGH=1
    LOW=0

class INTEGRATION_MODE(Enum):
    """
    BIT02: 積分モード設定信号
    """
    MANUAL=1 # マニュアル設定モード
    STATIC=0 # 固定時間モード


class INTEGRATION_TIME(Enum):
    """

    BIT01, BIT00: 積分時間設定信号
    """
    SHORT={"byte":0b00, "value":87.5, "unit":"us"}
    MID_SHORT={"byte":0b01, "value":1.4, "unit":"ms"}
    MID_LONG={"byte":0b10, "value":22.4, "unit":"ms"}
    LONG={"byte":0b11, "value":179.2, "unit":"ms"}
# ----------------------------------------------------------------------------------------------



class S11059_02DT_ControlCommand:
    """
    S11059_02DTの0x00レジスタに送信するコントロールコマンドを生成するクラス. 
    センサ値読み取り前に, reset/startを0x00レジスタに送信する
    その後, 積分時間分sleepし,0x03レジスタから8バイト分のデータ(RGB+IR)を読み取る
    """
    def __init__(self,
        gain:GAIN = GAIN.HIGH,
        integration_mode: INTEGRATION_MODE = INTEGRATION_MODE.MANUAL,
        integration_time: INTEGRATION_TIME = INTEGRATION_TIME.SHORT,
    ):
        self.gain = gain
        self.integration_mode = integration_mode
        self.integration_time = integration_time
        self.integration_seconds = self.__calculate_integration_seconds()


    @property
    def get_integration_seconds(self):
        return self.integration_seconds


    def get_reset_command(self):
        """
        送信先レジスタアドレス:
            0x00: コントロールレジスタ
        送信データ:
            b7: リセット信号
        """
        b7 = ADC_RESET.RESET.value << 7
        b6=SLEEP.WAKEUP.value << 6
        b3=self.gain.value << 3
        b2=self.integration_mode.value << 2
        b1b0=self.integration_time.value["byte"]
        command=b7 | b6 | b3 | b2 | b1b0
        return command


    def get_start_command(self):
        """
        送信先レジスタアドレス:
            0x00: コントロールレジスタ
        送信データ:
            b7: スタート信号
            b6: スリープモード信号
            b5: 0で良し
            b4: なし(特に何でも良い)
            b3: ゲイン設定信号
            b2: 積分モード設定信号
            b1b0: 積分時間設定信号
        """
        b7=ADC_RESET.START.value << 7
        b6=SLEEP.WAKEUP.value << 6
        b3=self.gain.value << 3
        b2=self.integration_mode.value << 2
        b1b0=self.integration_time.value["byte"]
        command=b7 | b6 | b3 | b2 | b1b0
        return command


    def __calculate_integration_seconds(self):
        """
        積分時間分sleepする必要がある.
        積分時間を秒単位にして返す
        """
        unit=self.integration_time.value["unit"]
        value=self.integration_time.value["value"]

        integration_seconds:float
        if unit=="us":
            integration_seconds=value/1000000.0
        elif unit=="ms":
            integration_seconds=value/1000.0
        elif unit=="s":
            integration_seconds=value
        else:
            raise ValueError(f"Invalid unit: {unit}")

        if self.integration_mode==INTEGRATION_MODE.MANUAL:
            integration_seconds *= 2 # マニュアルモードのときは2倍になるらしい

        return integration_seconds




if __name__ == "__main__":
    control_command=S11059_02DT_ControlCommand(
        gain=GAIN.HIGH,
        integration_mode=INTEGRATION_MODE.STATIC,
        integration_time=INTEGRATION_TIME.MID_LONG,
    )
    print(f"リセットコマンド: {bin(control_command.get_reset_command())}")
    print(f"スタートコマンド: {bin(control_command.get_start_command())}")
    print(f"積分時間: {control_command.get_integration_seconds}秒")