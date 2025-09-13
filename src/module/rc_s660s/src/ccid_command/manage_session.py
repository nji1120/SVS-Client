from enum import Enum

from .ccid_command_abc import CCIDCommandAbc

class ManageSessionDataObjectTag:
    START_TRANSPARENT_SESSION = [0x81]
    END_TRANSPARENT_SESSION = [0x82]
    RF_OFF = [0x83] # リーダライタの電波OFF
    RF_ON = [0x84] # リーダライタの電波ON

    @staticmethod
    def GET_PARAMETERS(command:list[int])-> list[int]:
        data_in=[0xFF,0x6D] 
        data_length=list(len(command).to_bytes(1, 'big'))
        data_in += data_length + command
        return data_in

    @staticmethod
    def SET_PARAMETERS(command:list[int]) -> list[int]:
        """
        :param command: ex)[0x05, 0x01, 0x89] 通信速度設定
        """
        data_in=[0xFF,0x6E]
        data_length=list(len(command).to_bytes(1, 'big'))
        data_in += data_length + command
        return data_in


class ManageSession(CCIDCommandAbc):

    def __init__(
            self, 
            data_object_tag=ManageSessionDataObjectTag.START_TRANSPARENT_SESSION
        ):
        """
        data_object_tag: データオブジェクトのタグ. これでmanage sessionの種類を指定する
        デフォルトはSTART_TRANSPARENT_SESSION
        """
        super().__init__()
        self.data_object_tag = data_object_tag

    def set_apdu_command(self) -> None:
        cla=[0xFF]
        ins=[0xC2]
        p1=[0x00]
        p2=[0x00]
        lc=list(len(self.data_object_tag).to_bytes(1, 'big'))
        data_in=self.data_object_tag

        self.ab_data=(
            cla
            + ins
            + p1
            + p2
            + lc
            + data_in
        )

