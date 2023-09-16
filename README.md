# SPEEDUINO-LCD-PICO

This is an example of a speeduino monitor/hud using an RP2040-Zero along with a 16x2 I2C LCD display.

it'll probably work with any micropython-based controller, but pins will likely need changing. 

Pins for RP2040-Zero:

39(5V): From source 5V, to LCD VCC pin

38(GND): From source GND, to LCD GND pin, to button GND

32(GPIO27/SCL1): To LCD SCL pin

31(GPIO26/SDA1): To LCD SDA pin

1(GPIO00/TXD0): From source Rx

2(GPIO01/RXD0): From source Tx

11(GPIO8): To button
