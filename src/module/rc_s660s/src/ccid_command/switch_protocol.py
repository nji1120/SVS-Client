from enum import Enum

from .ccid_command_abc import CCIDCommandAbc

class SwitchProtocolDataObjectTag:
    SWITCH_TO_FELICA = [0x8F, 0x02, 0x03, 0x00] # felica通信用設定
    SWITCH_TO_FELICA_POLLING = [0x8F, 0x02, 0x03, 0x01] # felica通信用設定&ポーリング実行

    SWITCH_TO_TYPEA_LAYER2 = [0x8F, 0x02, 0x00, 0x02] # typeA, layer2まで進める
    SWITCH_TO_TYPEA_LAYER3 = [0x8F, 0x02, 0x00, 0x03] # typeA, layer3まで進める
    SWITCH_TO_TYPEA_LAYER4 = [0x8F, 0x02, 0x00, 0x04] # typeA, layer4まで進める

    SWITCH_TO_TYPEB_LAYER3 = [0x8F, 0x02, 0x01, 0x03] # typeB, layer3まで進める
    SWITCH_TO_TYPEB_LAYER4 = [0x8F, 0x02, 0x01, 0x04] # typeB, layer4まで進める


class SwitchProtocol(CCIDCommandAbc):
    """
    switch protocolはtransparent sessionを開始しないと使えない
    """

    def __init__(
            self, 
            data_object_tag=SwitchProtocolDataObjectTag.SWITCH_TO_FELICA_POLLING
        ):
        super().__init__()
        self.data_object_tag = data_object_tag

    def set_apdu_command(self) -> None:
        cla=[0xFF]
        ins=[0xC2]
        p1=[0x00]
        p2=[0x02]
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