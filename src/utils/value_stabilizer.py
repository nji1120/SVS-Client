from statistics import mode
from copy import deepcopy


class ValueStabilizer():
    """
    値をtrajectoryとして記憶し、移動平均化のようにするクラス
    こうすることで、安定した状態を取得できる
    """

    def __init__(self, trajectory_nums=10, channel_names=["ch0"]):
        """
        :param trajectory_nums: 記憶する軌跡の数
        :param channel_names: チャンネル名
        """
        self.trajectory_nums = trajectory_nums
        self.channel_names = deepcopy(channel_names)
        self.trajectory = [] #[trajectory_nums x port_nums]

        self.state_keys=[
            "is_card","card_id","is_front","is_vertical"
        ]


    def add_trajectory(self, sensor_states):
        """
        軌跡を追加する
        :param sensor_states: [port_nums]
        """
        self.trajectory.append(sensor_states)
        if len(self.trajectory) > self.trajectory_nums:
            self.trajectory.pop(0)


    def get_stable_states(self):
        """
        安定した状態を取得する
        """

        stable_states={f"{channel_name}":{} for channel_name in self.channel_names}

        for channel_name in stable_states.keys():

            is_exist_none=False

            for key in self.state_keys:
                stable_states[channel_name][key]=self.__get_stable_state(channel_name=channel_name,key=key)

                if stable_states[channel_name][key] is None:
                    is_exist_none=True

            if is_exist_none: stable_states[channel_name]["is_card"]=False #Noneの状態値があれば, カードの存在は無いことにする

        return stable_states


    def __get_stable_state(self,channel_name,key):
        """
        安定した状態(=trajectoryにおける最頻値)を取得する
        :param channel_name: チャンネル名
        :param key: 状態のキー
        :return: そのキーのmode
        """

        state_trj=[]
        for trj_t in self.trajectory:
            state_trj.append(trj_t[channel_name][key])

        state_distinct=list(set(state_trj)) # 重複を削除
        state_num_max=3 # とりあえず, 最大でNone, True, Falseの3つがあるとする

        # if len(state_distinct) >= state_num_max:
        #     # 直近1/3の軌跡を取る
        #     latest_trj=state_trj[-int(len(state_trj)/5):]
        #     latest_distinct=list(set(latest_trj))

        #     # 直近が全部同じならそれ. そうでなければ全体のmodeを取る
        #     state_mode=latest_distinct[0] if len(latest_distinct)==1 else mode(state_trj)
        
        # else:
        state_mode=mode(state_trj)
        return state_mode
    

