class CardStateAnalyzer:
    def __init__(self, color_sensor_threshold:dict, photo_diode_threshold:float):
        """
        :param color_sensor_threshold
            {
                "r":{"low":1,"high":9},
                "g":{"low":1,"high":10},
                "b":{"low":1,"high":10},
                "ir":14 # IRの閾値. これによってカードの有無を判定する
            }           
        :param photo_dioede_threshold:0.17
        """
        
        #>> カラーセンサーの閾値 >>
        self.r_low,self.r_high=list(color_sensor_threshold["r"].values())
        self.g_low,self.g_high=list(color_sensor_threshold["g"].values())
        self.b_low,self.b_high=list(color_sensor_threshold["b"].values())
        self.ir_th = color_sensor_threshold["ir"]
        

        #>> フォトダイオードの閾値 >>
        self.photo_diode_threshold=photo_diode_threshold



    def analyze_card_state(self, values:dict) -> dict:
        """
        :param values
            {
                ch0:{
                    felica: XXXX,
                    color_sensor:{
                        R:XX, G:XX, B:XX, IR:XX
                    },
                    photo_diode:XX
                },...
            }
        """
        card_states={}
        for key, value in values.items():
            is_card, is_front=self.__analyze_color_sensor(value["color_sensor"])
            is_vertical=self.__analyze_photo_diode(value["photo_diode"]) if is_card else None # カードがあれば縦横判定
            felica_id="".join(value["felica"]) if not value["felica"] is None else "0000000000000000"
            card_states[key]={
                "is_card":is_card,
                "card_id":felica_id,
                "is_front":is_front,
                "is_vertical":is_vertical
            }

        return card_states


    def __analyze_color_sensor(self, color_sensor_values):
        """
        1. color sensorのIRでカードの有無を判定
        2. color sensorのRGBでカードの表裏を判定
        """

        r,g,b,ir=list(color_sensor_values.values())

        is_card=False if ir>self.ir_th else True
        is_front:bool

        if not is_card:
            is_front=None
        elif is_card:
            if (self.r_low<=r<=self.r_high) and (self.g_low<=g<=self.g_high) and (self.b_low<=b<=self.b_high):
                is_front=True
            else:
                is_front=False
        
        return is_card, is_front


    def __analyze_photo_diode(self, photo_diode_value):
        """
        1. photo diodeでカードの縦横を判定
        """
        if photo_diode_value<self.photo_diode_threshold:
            is_vertical=True
        else:
            is_vertical=False
        return is_vertical
    
        