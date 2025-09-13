from .ccid_command_abc import CCIDCommandAbc


class ResetDevice(CCIDCommandAbc):

    def set_apdu_command(self) -> None:
        self.ab_data = [0xFF, 0x55, 0x00, 0x00]
