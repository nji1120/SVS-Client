
from .ccid_command_abc import CCIDCommandAbc

class GetData(CCIDCommandAbc):

    def set_apdu_command(self) -> None:
        cla=[0xFF]
        ins=[0xCB]
        p1=[0x00]
        p2=[0x00]
        lc=[0x00]
        self.ab_data=(
            cla
            + ins
            + p1
            + p2
            + lc
        )