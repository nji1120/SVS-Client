import time

from ..rcs660s import RCS660S

from ..ccid_command.reset_device import ResetDevice
from ..ccid_command.manage_session import ManageSession, ManageSessionDataObjectTag
from ..ccid_command.switch_protocol import SwitchProtocol, SwitchProtocolDataObjectTag
from ..ccid_command.transparent_exchange import TransparentExchange, TransparentExchangeDataObjectTag



class RCS660SManager:
    """
    低レベルなRCS660Sの通信を管理するクラス
    一連のコマンドを実行し, 使用者にバイト列の通信を意識させない.
    """

    def __init__(self,rcs660s:RCS660S,is_debug:bool=False):
        self.rcs660s = rcs660s
        self.is_debug = is_debug
        self.is_setup=False


    def reset_device(self):
        if self.is_debug: print("RESET DEVICE")
        self.rcs660s.create_command_frame(
            ccid_command=ResetDevice(), is_debug=self.is_debug
        )
        self.rcs660s.send_command_frame()
        time.sleep(50/1000) #response返るまでちょっと待つ
        self.rcs660s.uart.read(128)

    
    def setup_device(self):
        """
        読み取りループ前の準備コマンド
        trainsmission/reception flagとかの設定する
        """
        self.is_setup=True

        return NotImplementedError("setup_device is not implemented")



    def start_transparent_session(self) -> None:
        """
        マルチチャンネルの場合, START_transparent_sessionを毎polling前に実行する必要がある
        (SwitchProtocolは必要ない)
        """
        if self.is_debug: print("START TRANSPARENT SESSION")


        # start transparent sessionにspeedやtimerはいれてはいけない. 順序が不正ですエラーが発生する
        # --- 通信速度設定 --- (意味なし. むしろ遅くなる)
        # speed_ccid=[]#[0xFF, 0x6E, 0x03, 0x05, 0x01, 0b10011011] # 通信速度設定 848bps (最速)

        # # --- タイムアウト時間 設定 (公式ドキュメントによると精度は1ms) ---
        # timeout_ms = 5 # ms, 3ms未満はIDmを読み取れない. そのため3msが最速設定.
        # timer_command=list(int(timeout_ms*1000).to_bytes(4, 'little')) # 待機時間[μs], リトルエンディアン
        # timer_ccid=[]#TransparentExchangeDataObjectTag.TIMER(timer_command)


        # 1) Start Transparent Session
        self.rcs660s.create_command_frame(
            ccid_command=ManageSession(
                data_object_tag=ManageSessionDataObjectTag.START_TRANSPARENT_SESSION
            ), is_debug=self.is_debug
        )
        self.rcs660s.send_command_frame()

        response = self.rcs660s.read_response(is_debug=False) # readしとかないと, 次のコマンドで前コマンドの結果が返ってきちゃう
        if self.is_debug: self.debug_response(response)
       
        # time.sleep(1.0/1000) #待機
        # self.rcs660s.flush_buffer() #コマンド結果をクリア


    def start_transparent_session_performance_check(self) -> None:
        """
        速度のボトルネック調査
        """
        t0 = time.perf_counter()

        self.rcs660s.create_command_frame(
            ccid_command=ManageSession(
                data_object_tag=ManageSessionDataObjectTag.START_TRANSPARENT_SESSION
            )
        )
        t1 = time.perf_counter()

        self.rcs660s.send_command_frame()
        t2 = time.perf_counter()

        response = self.rcs660s.read_response(is_debug=False)
        t3 = time.perf_counter()

        print(
            f"[perf] build={(t1-t0)*1e3:.2f} ms, "
            f"send={(t2-t1)*1e3:.2f} ms, "
            f"recv={(t3-t2)*1e3:.2f} ms, "
            f"total={(t3-t0)*1e3:.2f} ms"
        )

    def polling(self) -> dict:
        """
        読み取りループ
        """
        return NotImplementedError("polling is not implemented")

    def end_session(self) -> None:
        if self.is_debug: print("RF OFF/ END TRANSPARENT SESSION")


        # 同じ manage sessionなので, いっぺんにコマンドを送信する
        rf_off=ManageSessionDataObjectTag.RF_OFF
        end_transparent_session=ManageSessionDataObjectTag.END_TRANSPARENT_SESSION

        self.rcs660s.create_command_frame(
            ccid_command=ManageSession(
                data_object_tag=rf_off+end_transparent_session
            ), is_debug=self.is_debug
        )
        self.rcs660s.send_command_frame()
        response = self.rcs660s.read_response(is_debug=False)
        if self.is_debug: self.debug_response(response)
        # self.rcs660s.flush_buffer()

    def close(self) -> None:
        # 通信終了
        self.end_session()
        self.rcs660s.uart.close()

    def __bit2str(self,bit_list:list[int]) -> str:
        if type(bit_list) == bytes: 
            bit_list=list(bit_list)
            return f"{' '.join(f'{bit:02X}' for bit in bit_list)}"
        else:
            return bit_list
    def debug_response(self,res_str:str)->None:
        print(f"\033[32mRESPONSE COMMAND\033[0m: {self.__bit2str(res_str)}\n")