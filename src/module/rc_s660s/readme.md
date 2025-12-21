# rc-s660/s

## ファイルについて
Sensor_tutorialsからコピペ  

## 規格
- UART
  - 115200bps  
    ボーレートはコマンドで設定可能
  - start bit: 1bit
  - data bit: 8bit
  - data order: LSB first
  - stop bit: 1bit
  - parity: none
  - flow control: none

- 定格：3.3V
- 消費電流：max140 mA  
  <b>※ラズパイのGPIO1本の定格は16mAのため, 外部電源が必要</b>