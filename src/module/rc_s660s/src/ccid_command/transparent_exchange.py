from enum import Enum

from .ccid_command_abc import CCIDCommandAbc


class TransparentExchangeDataObjectTag:
    RECEIVE = [0x94,0x00]
    
    @staticmethod
    def Transmission_BIT_FRAMING(command:list[int]=[0x00]) -> list[int]:
        data_in=[0x91,0x01]
        data_in += command
        return data_in

    @staticmethod
    def TIMER(command:list[int])-> list[int]:
        """
        :param command: 必ず4byte. リトルエンディアン.
        """
        data_in=[0x5F, 0x46, 0x04]
        data_in += command
        return data_in

    @staticmethod
    def GET_PARAMETERS(command:list[int])-> list[int]:
        data_in=[0xFF, 0x6d]
        data_length=list(len(command).to_bytes(1, 'big'))
        data_in += data_length + command
        return data_in

    @staticmethod
    def TRANSMIT(command:list[int])-> list[int]:
        data_in=[0x93]
        data_length=list(len(command).to_bytes(1, 'big'))
        data_in += data_length + command
        return data_in

    @staticmethod
    def TRANSCEIVE(command:list[int])-> list[int]:
        data_in=[0x95]
        data_length=list(len(command).to_bytes(1, 'big'))
        data_in += data_length + command
        return data_in

    @staticmethod
    def TRANSMISSION_RECEPTION_FLAG(
        b0:bool=True,
        b1:bool=True,
        b23:bool=True,
        b4:bool=True
    )-> list[int]:

        data_in=[0x90,0x02]
        val= b0 + (b1<<1) + (b23<<2) + (b23<<3) + (b4<<4)
        data_in += list(val.to_bytes(2, 'big'))
        return data_in



class TransparentExchange(CCIDCommandAbc):

    def __init__(
            self, 
            data_object_tag=TransparentExchangeDataObjectTag.RECEIVE
        ):
        super().__init__()
        self.data_object_tag = data_object_tag

    def set_apdu_command(self) -> None:
        cla=[0xFF]
        ins=[0xC2]
        p1=[0x00]
        p2=[0x01]
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