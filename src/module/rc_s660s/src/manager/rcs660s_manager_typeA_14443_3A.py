from .rcs660s_manager_base import RCS660SManager

from ..rcs660s import RCS660S
from ..ccid_command.transparent_exchange import TransparentExchange, TransparentExchangeDataObjectTag
from ..ccid_command.switch_protocol import SwitchProtocol, SwitchProtocolDataObjectTag

import time

class RCS660SManagerTypeA144433A(RCS660SManager):
    """
    ISO 14443-3AのNFC Forum Type2のUID取得を扱うクラス
    (TypeAでも, 14443-4Aの場合はまた別のクラスが必要)
    """

    def __init__(self,rcs660s:RCS660S,is_debug:bool=False):
        super().__init__(rcs660s,is_debug)


    def setup_device(self)->None:
        """
        14443-3Aは特に設定することはない
        transmission/reception flag や transmission framingはデフォルトの値で良い
        """
        self.reset_device()
        self.start_transparent_session() 
        self.is_setup=True


    def polling(self) -> dict:
        """
        直列度1で17Hzが限度. 6port直列では2~3Hz程度が限度. まあ十分でしょ.
        """

        # パフォーマンス測定用関数
        # return self.__polling_performance_check()

        self.start_transparent_session() 
        self.__switch_protocol()

        # --- 前回のコマンド結果をクリア ---
        # self.rcs660s.flush_buffer() # 前回のコマンド結果をクリア
        # self.rcs660s.read_discard() # 読み捨て
        # --------------------------------

        response=self.__transceive()   
        # self.end_session()

        response={"id":self.__extract_uid(response["apdu"]["response"])}

        return response
        
    

    def __switch_protocol(self)->None:
        if self.is_debug: print("switch protocol")


        self.rcs660s.create_command_frame(
            ccid_command=SwitchProtocol(
                data_object_tag=(
                    SwitchProtocolDataObjectTag.SWITCH_TO_TYPEA_LAYER3
                )
            ), is_debug=False
        )
        self.rcs660s.send_command_frame()

        response = self.rcs660s.read_response(is_debug=False)

        # time.sleep(33.0/1000) #待機
        # response=self.rcs660s.flush_buffer() #コマンド結果をクリア

        if self.is_debug: self.debug_response(response)


    def __transceive(self)->dict:
        if self.is_debug: print("transceive")

        # --- 通信速度設定 ---
        speed_ccid=[]#[0x05, 0x01, 0b10011011] # 通信速度設定 848bps (最速)
        
        # --- タイムアウト時間 設定 (公式ドキュメントによると精度は1ms) ---
        timeout_ms = 1 # ms, 3ms未満はIDmを読み取れない. そのため3msが最速設定.
        timer_command=list(int(timeout_ms*1000).to_bytes(4, 'little')) # 待機時間[μs], リトルエンディアン
        timer_ccid=TransparentExchangeDataObjectTag.TIMER(timer_command)

        # --- SELECTコマンド ---
        polling_command=[0x30, 0x00] # ISO 14443-3AのSELECTコマンド(0x30), 0x00でページバイト指定, UIDは0x00ページにある
        polling_ccid=TransparentExchangeDataObjectTag.TRANSCEIVE(polling_command)
        
        # --- コマンドフレーム作成 ---
        self.rcs660s.create_command_frame(
            ccid_command=TransparentExchange(
                data_object_tag=speed_ccid + timer_ccid + polling_ccid
            ), is_debug=self.is_debug
        )

        # --- I/O ---
        self.rcs660s.send_command_frame()
        # response=self.rcs660s.uart.read(128)
        response = self.rcs660s.read_response(is_debug=False) # Trueだとloop問い合わせの中身をprintする

        if self.is_debug: self.debug_response(response)

        return response

    def __extract_uid(self, resp: bytes) -> list[int]:
        """
        resp: Transparent Exchange のレスポンスを想定。
            ... 92 01 00 96 02 00 00 97 10 <16-byte page0/1/2/3> 90 00
        戻り値: UID を int リスト（7バイト）で返す。
        見つからない場合はNoneを返す。
        """
        marker = b"\x97\x10"  # ICC Response + length=0x10 (READ 0x30 0x00 の16B)
        idx = resp.find(marker)
        if idx == -1 or idx + 2 + 16 > len(resp):
            return None

        data = resp[idx + 2 : idx + 2 + 16]

        # Type2 page0 layoutに従い UID 抜き出し (UID0-2, UID3-6)
        uid_bytes = [data[0], data[1], data[2], data[4], data[5], data[6], data[7]]
        return uid_bytes


    # pollingのパフォーマンス測定用関数
    def __polling_performance_check(self) -> dict:
        # 合計で70 msくらいかかるが, 6port直列でも2Hz程度は出せるのでOKとしましょう.
        # 正直, そんなに反応速度が求められるシステムじゃ無いですし. むしろUARTの通信安定性が落ちるほうがデメリットです
        
        # 速度のボトルネック調査
        t0 = time.perf_counter()
        self.start_transparent_session() # 16 ms
        t1 = time.perf_counter()
        self.__switch_protocol() # 35 ms
        t2 = time.perf_counter()
        self.rcs660s.flush_buffer()
        self.rcs660s.read_discard() # 読み捨て
        response = self.__transceive() # 23 ms
        t3 = time.perf_counter()

        if True:
            print(
                f"[perf] start_transparent_session: {(t1-t0)*1e3:.2f} ms, "
                f"switch_protocol: {(t2-t1)*1e3:.2f} ms, "
                f"transceive: {(t3-t2)*1e3:.2f} ms, "
                f"total: {(t3-t0)*1e3:.2f} ms"
            )

        response = {"id": self.__extract_uid(response["apdu"]["response"])}
        return response

