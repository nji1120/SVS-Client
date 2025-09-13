import abc

from ..response_status.response_status import ResponseStatus

class CCIDCommandAbc(abc.ABC):

    def __init__(self):
        self.b_message_type = [0x6B] # PC_to_RDB_ESCAPEを表す
        self.dw_length: list[int]
        self.b_slot = [0x00]
        self.b_seq = [0x00]
        self.ab_rfu = [0x00, 0x00, 0x00]
        self.ab_data: list[int]

        self.apdu_response: dict


    @abc.abstractmethod
    def set_apdu_command(self) -> None:
        return NotImplementedError
    
    def set_apdu_response(self, apdu_response: bytes) -> None:
        """
        adpuコマンドごとにoverrideする
        """
        self.apdu_response = {
            "apdu_response":apdu_response,
        }
    

    def __set_dw_length(self) -> None:
        self.dw_length = list(len(self.ab_data).to_bytes(4, 'little'))


    def get_ccid_command(self) -> list[int]:
        self.set_apdu_command() # apdu_commandを設定
        self.__set_dw_length() # dw_lengthを設定
        ccid_command = (
            self.b_message_type 
            + self.dw_length 
            + self.b_slot 
            + self.b_seq 
            + self.ab_rfu 
            + self.ab_data
        )
        return ccid_command
    

    def read_ccid_response(self, ccid_response: bytes, apdu_response: bytes) -> dict:
        status, message = self.__read_ccid_status(ccid_response)
        apdu_status, apdu_message = self.__read_apdu_status(apdu_response)
        self.set_apdu_response(apdu_response)
        result={
            "ccid":{
                "response": ccid_response,
                "status": status,
                "message": message
            },
            "apdu":{
                "response": apdu_response,
                "status": apdu_status,
                "message": apdu_message
            }
        }
        return result
    

    def __read_ccid_status(self, ccid_response: bytes) -> tuple[str, str]:
        sw1, sw2 = ccid_response[-2], ccid_response[-1]
        status, message = ResponseStatus.get_ccid_status(sw1, sw2)
        return status, message
    
    def __read_apdu_status(self, apdu_response: bytes) -> tuple[str, str]:
        b1, b2 = apdu_response[3], apdu_response[4]
        status, message = ResponseStatus.get_apdu_status(b1, b2)
        return status, message