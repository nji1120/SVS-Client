import time


def sleep(previous_time,sleeping_time):
    """
    :param previous_time: 前回の処理時刻[ns]   
    :prama sleeping_time: 待機時間[ns]
    """

    #ビジーループは良くない.CPU稼働率が94%とか行く
    # while time.time_ns()-previous_time<sleeping_time:
    #     pass

    rest_time=sleeping_time-(time.time_ns()-previous_time) #ns
    if rest_time>0:
        time.sleep(rest_time*10**-9)