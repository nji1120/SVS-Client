from statistics import mode
import numpy as np

class SensorValueStabilizer():
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

        self.felica_key="pasori"
        self.color_sensor_key="color_sensor"
        self.diode_key="photo_diode"

    def add_trajectory(self, sensor_values):
        """
        軌跡を追加する
        :param sensor_values: [port_nums]
        """
        self.trajectory.append(sensor_values)
        if len(self.trajectory) > self.trajectory_nums:
            self.trajectory.pop(0)


    def get_stable_values(self):
        """
        安定した状態を取得する
        """

        stable_values={f"port{i+self.port_start_index}":{} for i in range(self.port_nums)}

        for port_name in stable_values.keys():
            stable_values[port_name][self.felica_key]=self.__get_stable_felica_id(port_name,felica_key=self.felica_key)
            stable_values[port_name][self.color_sensor_key]=self.__get_stable_color_sensor_value(port_name,color_sensor_key=self.color_sensor_key)
            stable_values[port_name][self.diode_key]=self.__get_stable_diode_value(port_name,diode_key=self.diode_key)

        return stable_values


    def __get_stable_felica_id(self,port_name,felica_key="pasori"):
        """
        安定したFelica IDを取得する
        :param port_name: ポート名
        :param felica_key: Felica IDのキー
        :return: trajectoryの中で最も多く出現したFelica ID
        """

        felica_list=[]
        for trj_t in self.trajectory:
            felica_list.append(trj_t[port_name][felica_key])

        felica_id_mode=mode(felica_list)

        return felica_id_mode
    

    def __get_stable_color_sensor_value(self,port_name,color_sensor_key="color_sensor"):
        """
        安定したカラーセンサの値を取得する
        :param port_name: ポート名
        :param color_sensor_key: カラーセンサのキー
        :return: 各RGBIの平均値
        """
        rgbi_list={"R":[],"G":[],"B":[],"IR":[]}
        for trj_t in self.trajectory:
            for key,val in rgbi_list.items():
                rgbi_list[key].append(trj_t[port_name][color_sensor_key][key])

        rgbi_mean={}
        for key,val in rgbi_list.items():
            rgbi_mean[key]=np.mean(val)

        return rgbi_mean


    def __get_stable_diode_value(self,port_name,diode_key="photo_diode"):
        """
        安定したフォトダイオードの値を取得する
        :param port_name: ポート名
        :param diode_key: フォトダイオードのキー
        :return: フォトダイオードの平均値
        """
        diode_list=[]
        for trj_t in self.trajectory:
            diode_list.append(trj_t[port_name][diode_key])

        diode_mean=np.mean(diode_list)
        return diode_mean