from .ccid_command_abc import CCIDCommandAbc


class GetFirmwareVersion(CCIDCommandAbc):

    def set_apdu_command(self) -> None:
        self.ab_data = [0xFF, 0x56, 0x00, 0x00]

