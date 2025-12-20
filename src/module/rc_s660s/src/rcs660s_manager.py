import time

from .rcs660s import RCS660S

from .ccid_command.reset_device import ResetDevice
from .ccid_command.manage_session import ManageSession, ManageSessionDataObjectTag
from .ccid_command.switch_protocol import SwitchProtocol, SwitchProtocolDataObjectTag
from .ccid_command.transparent_exchange import TransparentExchange, TransparentExchangeDataObjectTag



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
        self.rcs660s.create_command_frame(
            ccid_command=ResetDevice(), is_debug=self.is_debug
        )
        self.rcs660s.send_command_frame()
        self.rcs660s.uart.read(128)

    
    def setup_device(self):

        # 1) Start Transparent Session
        self.rcs660s.create_command_frame(
            ccid_command=ManageSession(
                data_object_tag=ManageSessionDataObjectTag.START_TRANSPARENT_SESSION
            ), is_debug=self.is_debug
        )
        self.rcs660s.send_command_frame()
        response = self.rcs660s.read_response(is_debug=False)
        if self.is_debug: 
            print("1) Start Transparent Session")
            print(response)
        # print("\n")

        # 2) SwitchProtocol (TypeA/B/F)
        self.rcs660s.create_command_frame(
            ccid_command=SwitchProtocol(
                # ここはpollingまで開けても問題ない. ただし, 無駄なのでfelica通信設定のみだけで良い.
                data_object_tag=SwitchProtocolDataObjectTag.SWITCH_TO_FELICA
            ), is_debug=self.is_debug
        )
        self.rcs660s.send_command_frame()
        response = self.rcs660s.read_response()
        if self.is_debug: 
            print("2) SwitchProtocol (TypeA/B/F)")
            print(response)
        # print("\n")


        # 3)送受信処理フラグ
        self.rcs660s.create_command_frame(
            ccid_command=TransparentExchange(
                # 0bit目, 1bit目はFalse必須
                data_object_tag=TransparentExchangeDataObjectTag.TRANSMISSION_RECEPTION_FLAG(
                    False,False,True,True
                )
            ), is_debug=self.is_debug
        )
        self.rcs660s.send_command_frame()
        response = self.rcs660s.read_response()
        if self.is_debug: 
            print("3)送受信処理フラグ:")
            print(response)
        # print("\n")

        # 4) transmission bit framing
        command=[0x00]
        self.rcs660s.create_command_frame(
            ccid_command=TransparentExchange(
                data_object_tag=TransparentExchangeDataObjectTag.Transmission_BIT_FRAMING(command)
            ), is_debug=self.is_debug
        )
        self.rcs660s.send_command_frame()
        response = self.rcs660s.read_response()
        if self.is_debug: 
            print("4) transmission bit framing")
            print(response)
        # print("\n")

        # 5) 通信速度設定
        speed_def = 0b10001001 # 212kbps. 0b10001001 -> 848kbpsだとtlv違反になる
        command=[0x05, 0x01, speed_def]
        self.rcs660s.create_command_frame(
            ccid_command=ManageSession(
                data_object_tag=ManageSessionDataObjectTag.SET_PARAMETERS(command)
            ), is_debug=self.is_debug
        )
        self.rcs660s.send_command_frame()
        response = self.rcs660s.read_response()
        if self.is_debug: 
            print("5) 通信速度設定")
            print(response)
        # print("\n")

        # 6) RF ON
        self.rcs660s.create_command_frame(
            ccid_command=ManageSession(
                data_object_tag=ManageSessionDataObjectTag.RF_ON
            ), is_debug=False
        )
        self.rcs660s.send_command_frame()
        response = self.rcs660s.read_response()
        if self.is_debug: 
            print("6) RF ON:")
            print(response)
        # print("\n")


        self.is_setup=True



    def __strart_transparent_session(self) -> None:
        """
        マルチチャンネルの場合, START_transparent_sessionを毎polling前に実行する必要がある
        (SwitchProtocolは必要ない)
        """
        # 1) Start Transparent Session
        self.rcs660s.create_command_frame(
            ccid_command=ManageSession(
                data_object_tag=ManageSessionDataObjectTag.START_TRANSPARENT_SESSION
            ), is_debug=self.is_debug
        )
        self.rcs660s.send_command_frame()
        response = self.rcs660s.read_response(is_debug=False) # readしとかないと, 次のコマンドで前コマンドの結果が返ってきちゃう




    def polling(self) -> dict:
        """
        開発メモ)
        【チャンネル数と最大周波数】
        - 1チャンネル: 26Hz程度
        - 2チャンネル: 13Hz程度 (かなり線形に落ちてるなぁ)
        """


        # マルチチャンネルの場合は, これを毎pooling前に実行する必要あり
        # しかし, これを毎poolingで実行すると26Hz程度が限界となる (ないときは35Hz程度まで出せる)
        self.__strart_transparent_session() 

        # タイムアウト時間 設定 (公式ドキュメントによると精度は1ms)
        timeout_ms = 5 # ms, 3ms未満はIDmを読み取れない. そのため3msが最速設定.
        timer_command=list((timeout_ms*1000).to_bytes(4, 'little')) # 待機時間[μs], リトルエンディアン
        timer_ccid=TransparentExchangeDataObjectTag.TIMER(timer_command)

        polling_command=[0x06,0x00,0xff,0xff,0x00,0x00] # idm取得コマンド, 謎の0x06が必須(バイト長さではない...)
        polling_ccid=TransparentExchangeDataObjectTag.TRANSCEIVE(polling_command)
        self.rcs660s.create_command_frame(
            ccid_command=TransparentExchange(
                data_object_tag=timer_ccid + polling_ccid
            ), is_debug=self.is_debug
        )
        self.rcs660s.send_command_frame()


        response = self.rcs660s.read_response(is_debug=False) # Trueだとloop問い合わせの中身をprintする
        if self.is_debug: 
            print("polling")
            print(response)
        
        # バイト列からidmと工場番号に変換
        response_dict=self.__bite2idm(response)




        return response_dict


    def close(self):
        # 通信終了

        # 8) RF OFF
        if self.is_debug: print("8) RF OFF")
        self.rcs660s.create_command_frame(
            ccid_command=ManageSession(
                data_object_tag=ManageSessionDataObjectTag.RF_OFF
            ), is_debug=self.is_debug
        )
        self.rcs660s.send_command_frame()
        response = self.rcs660s.read_response()
        # print_response(response)
        # print("\n")

        # 9) End Transparent Session
        if self.is_debug: print("9) End Transparent Session")
        self.rcs660s.create_command_frame(
            ccid_command=ManageSession(
                data_object_tag=ManageSessionDataObjectTag.END_TRANSPARENT_SESSION
            ), is_debug=self.is_debug
        )
        self.rcs660s.send_command_frame()
        response = self.rcs660s.read_response()
        # print_response(response)
        # print("\n")

        self.rcs660s.uart.close()


    def __bite2idm(self,response)->dict:
        """
        rcs660sからのresponseからidmとpmmを取得する
        :return:out:{"idm":idm, "pmm":pmm}, カードが無いときはNoneになる
            idm:16進数8つのfelica固有のID
            pmm:16進数8つの製造工場ID
        """
        out={}
        
        ccid_response = response["ccid"] # ccidのresponse：idm/pmmはccidで判断
        apdu_response = response["apdu"] # apduのresponse：カードが有無はapduで判断

        apdu_success_key="success" 
        if apdu_response["status"] != apdu_success_key: # カードが無い or 何らかのエラー
            out["idm"] = None
            out["pmm"] = None
        elif apdu_response["status"] == apdu_success_key: # カードがある
            ccid_hex=[f"{b:02X}" for b in ccid_response["response"]]
            byte_size=8
            pmm_tail=2
            idm_tail=byte_size+pmm_tail
            out["idm"] = ccid_hex[-(idm_tail+byte_size):-(idm_tail)]
            out["pmm"] = ccid_hex[-(pmm_tail+byte_size):-(pmm_tail)]

        return out
