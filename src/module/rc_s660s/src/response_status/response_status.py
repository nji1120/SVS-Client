from pathlib import Path
PARENT_DIR = Path(__file__).parent

import pandas as pd

class ResponseStatus:

    # -------------------------------------- CCID Response Status --------------------------------------
    CCID_STATUS_DF=None

    @classmethod
    def get_ccid_status(cls, sw1: int, sw2: int) -> str:

        if cls.CCID_STATUS_DF is None:
            cls.__init_ccid_status_df()
        
        status:str
        message:str
        if cls.__is_invalid_le(sw1):
            where=cls.CCID_STATUS_DF["sw1"]==sw1
            status=cls.CCID_STATUS_DF.loc[where]["status"].values[0]
            message=cls.CCID_STATUS_DF.loc[where]["message"].values[0]
        else:
            where=(cls.CCID_STATUS_DF["sw1"]==sw1) & (cls.CCID_STATUS_DF["sw2"]==sw2)
            status=cls.CCID_STATUS_DF.loc[where]["status"].values[0]
            message=cls.CCID_STATUS_DF.loc[where]["message"].values[0]

        return status, message

    @classmethod
    def __init_ccid_status_df(cls):
        if cls.CCID_STATUS_DF is None:
            cls.CCID_STATUS_DF = pd.read_csv(PARENT_DIR / "ccid_response_status.csv")

            # 16進数を整数に
            cls.CCID_STATUS_DF["sw1"]=cls.CCID_STATUS_DF["sw1"].apply(lambda x: int(x, 16))
            cls.CCID_STATUS_DF["sw2"]=cls.CCID_STATUS_DF["sw2"].apply(lambda x: int(x, 16))

    @classmethod
    def __is_invalid_le(cls,sw1: int) -> bool:
        """
        invalid_leの場合はsw1だけ見ればいい
        """
        result=False
        if sw1 == 0x6C:
            result=True
        return result
    

    # -------------------------------------- APDU Response Status --------------------------------------
    APDU_STATUS_DF=None
    @classmethod
    def get_apdu_status(cls, b1: int, b2: int) -> str:

        if cls.APDU_STATUS_DF is None:
            cls.__init_apdu_status_df()
        
        status:str
        message:str
        if cls.__is_invalid_le(b1):
            where=cls.APDU_STATUS_DF["B1"]==b1
            status=cls.APDU_STATUS_DF.loc[where]["status"].values[0]
            message=cls.APDU_STATUS_DF.loc[where]["message"].values[0]
        else:
            where=(cls.APDU_STATUS_DF["B1"]==b1) & (cls.APDU_STATUS_DF["B2"]==b2)
            status=cls.APDU_STATUS_DF.loc[where]["status"].values[0]
            message=cls.APDU_STATUS_DF.loc[where]["message"].values[0]

        return status, message

    @classmethod
    def __init_apdu_status_df(cls):
        if cls.APDU_STATUS_DF is None:
            cls.APDU_STATUS_DF = pd.read_csv(PARENT_DIR / "apdu_response_status.csv")

            # 16進数を整数に
            cls.APDU_STATUS_DF["B1"]=cls.APDU_STATUS_DF["B1"].apply(lambda x: int(x, 16))
            cls.APDU_STATUS_DF["B2"]=cls.APDU_STATUS_DF["B2"].apply(lambda x: int(x, 16))

