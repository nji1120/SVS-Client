import json

class Raspi2UnityAdapter:
    def __init__(self):
        # ポート名の変換マッピング
        self.port_map = {
            'ch0': 'port1',
            'ch1': 'port2',
            'ch2': 'port3',
            'ch3': 'port4',
            'ch4': 'port5',
            'ch5': 'port6',
        }
        
        # 内部データのキー変換
        self.key_map = {
            'card_id': 'felica_id',
            # 他に変換したいキーがあれば追記
        }

    def adapt(self, src: dict) -> dict:
        dst = {}
        for ch, state in src.items():
            # ポート名変換
            port = self.port_map.get(ch, ch)
            # 各キー名称変換
            adapted = {}
            for k, v in state.items():
                new_k = self.key_map.get(k, k)
                adapted[new_k] = v
            dst[port] = adapted
        return dst


# 使用例
if __name__ == '__main__':
    original = {'ch0': {'is_card': True, 'card_id': 85094388006619503, 'is_front': True, 'is_vertical': True}}
    adapter = Raspi2UnityAdapter()
    unity_dict = adapter.adapt(original)
    unity_json = adapter.adapt_json(original)
    print(unity_dict)
    print(unity_json)