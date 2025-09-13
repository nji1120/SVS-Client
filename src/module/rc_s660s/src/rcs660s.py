from math import ceil
import serial
import time

from .ccid_command.ccid_command_abc import CCIDCommandAbc
from .utils import print_hex, extract_bytes

class RCS660S:
    """
    RCS660Sのコマンドフレームを作成するクラス
    これをuartで送信する
    """

    def __init__(self, port: str, baudrate: int, timeout_fps: int):
        self.uart = self.__set_uart(port, baudrate, timeout_fps)

        self.ccid_command: CCIDCommandAbc
        self.preamble = [0x00]
        self.start_code = [0x00, 0xFF]
        self.packet_length: list[int]
        self.packet_length_checksum: list[int]
        self.packet_data_checksum: list[int]
        self.postamble = [0x00]
        self.command_frame: list[int]

        self.response: bytes


    # -------------------------------------- public methods --------------------------------------
    def create_command_frame(self, ccid_command: CCIDCommandAbc, is_debug: bool=False) -> None:
        self.ccid_command = ccid_command
        self.__set_packet_length()
        self.__set_packet_length_checksum()
        self.__set_packet_data_checksum()
        self.command_frame = (
            self.preamble 
            + self.start_code 
            + self.packet_length 
            + self.packet_length_checksum 
            + self.ccid_command.get_ccid_command() 
            + self.packet_data_checksum 
            + self.postamble
        )        

        # デバッグ用
        if is_debug: self.__debug_command_frame()



    def send_command_frame(self) -> None:
        self.uart.write(bytes(self.command_frame))

    def read_response(self) -> dict:
        size = 256
        self.response = bytes(self.uart.read(size)) # bytes型で読み取る

        # # debug
        # print_hex("response", self.response)
        # for i in range(10):
        #     time.sleep(0.1)
        #     response_tmp = bytes(self.uart.read(size))
        #     print_hex("response_tmp", response_tmp)
        #     self.response += response_tmp

        ack = extract_bytes(self.response, 0, 7)
        ccid_response = extract_bytes(self.response, 7, len(self.response)-2)
        apdu_response = extract_bytes(self.response, 23, len(self.response)-2) # パケットデータチェックサムとポストアンブルを除く
        
        response = self.ccid_command.read_ccid_response(ccid_response, apdu_response)
        return response


    # -------------------------------------- private methods --------------------------------------
    def __set_uart(self, port: str, baudrate: int, timeout_fps: int) -> serial.Serial:
        uart = serial.Serial(
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            port=port,
            baudrate=baudrate,
            timeout=1.0/timeout_fps
        )
        return uart
    
    def __set_packet_length(self) -> None:
        self.packet_length = list(len(
            self.ccid_command.get_ccid_command()
        ).to_bytes(2, 'big'))


    def __calculate_checksum(self, bytes_data: list[int]) -> list[int]:
        # CCIDコマンドの汎用チェックサム計算
        checksum = (16**2) * ceil(sum(bytes_data) / (16**2)) - sum(bytes_data)
        return list(checksum.to_bytes(1, 'big'))
    

    def __set_packet_length_checksum(self) -> None:
        self.packet_length_checksum = self.__calculate_checksum(
            self.packet_length
        )

    def __set_packet_data_checksum(self) -> None:
        self.packet_data_checksum = self.__calculate_checksum(
            self.ccid_command.get_ccid_command()
        )


    def __debug_command_frame(self) -> None:
        print("\033[33mdebug command frame =============================================================\033[0m")
        print_hex("packet_length", self.packet_length)
        print_hex("packet_length_checksum", self.packet_length_checksum)
        print_hex("packet_data_checksum", self.packet_data_checksum)
        print_hex("ccid_command", self.ccid_command.get_ccid_command())
        print_hex("command_frame", self.command_frame)
        print("\033[33m==================================================================================\033[0m\n")
