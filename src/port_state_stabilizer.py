from statistics import mode
import numpy as np

class PortStateStabilizer():
    """
    ポートの状態をtrajectoryとして記憶し、移動平均化のようにするクラス
    こうすることで、安定した状態を取得できる
    """

    def __init__(self, trajectory_nums=10, port_nums=1, port_start_index=0):
        """
        :param trajectory_nums: 記憶する軌跡の数
        :param port_nums: ポートの数
        :param port_start_index: ポートの開始インデックス
        """
        self.trajectory_nums = trajectory_nums
        self.port_nums = port_nums
        self.port_start_index = port_start_index
        self.trajectory = [] #[trajectory_nums x port_nums]

        self.state_keys=[
            "is_card","felica_id","is_front","is_vertical"
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

        stable_states={f"port{i+self.port_start_index}":{} for i in range(self.port_nums)}

        for port_name in stable_states.keys():

            is_exist_none=False

            for key in self.state_keys:
                stable_states[port_name][key]=self.__get_stable_state(port_name=port_name,key=key)

                if stable_states[port_name][key] is None:
                    is_exist_none=True

            if is_exist_none: stable_states[port_name]["is_card"]=False #Noneの状態値があれば, カードの存在は無いことにする

        return stable_states


    def __get_stable_state(self,port_name,key):
        """
        安定した状態(=trajectoryにおける最頻値)を取得する
        :param port_name: ポート名
        :param key: 状態のキー
        :return: そのキーのmode
        """

        state_trj=[]
        for trj_t in self.trajectory:
            state_trj.append(trj_t[port_name][key])

        state_mode=mode(state_trj)

        return state_mode
    

