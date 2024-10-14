# SVSv2
シングルプロセスで実装したSVS  
[→ マルチにしない理由](https://www.notion.so/1-ea0f800cab224cd68c13581e3b51496a)

## 使い方

1. カードリーダの数設定  
`app/conf.yml`の`card_reader_num`にカードリーダの数を設定する
2. 実行  
メインファイルを実行する(`python3 app/main.py`)  
サーバには以下の形式のデータがjson形式で送信される
~~~json
{
  "port1": {
    "is_card": true,
    "card_id": 85094388006619296,
    "is_front": false,
    "is_vertical": false
  },
  "port2": {
    "is_card": false,
    "card_id": 0,
    "is_front": null,
    "is_vertical": null
  },
}
~~~
