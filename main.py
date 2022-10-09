import machine
from time import sleep_ms, ticks_ms, ticks_diff
import struct
from pico_i2c_lcd import I2cLcd

"""
Micropython code for interfacing with a 2x16 LCD over i2c to show speeduino params using its secondary serial interface.
Pin numbers match up with PICO W diagram. 
"""

CALIBRATION_OFFSET = 40
POLL_MS = 50
uart = machine.UART(0, 115200, tx=machine.Pin(0), rx=machine.Pin(1))
i2c = machine.I2C(1, sda=machine.Pin(26), scl=machine.Pin(27), freq=400000)
I2C_ADDR = i2c.scan()[0]

lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)
timed_out = False

while True:
    uart.write('A')
    start = ticks_ms()
    while uart.any() < 76:
        if ticks_diff(ticks_ms(), start) > 1000:
            lcd.clear()
            lcd.putstr("Timeout")
            timed_out = True
            # slightly overkill to ask for everything here as we only use 3 bytes!
            uart.write('A')
            start = ticks_ms()
        sleep_ms(POLL_MS)
    # escaped above loop, so we have recovered
    if timed_out:
        lcd.clear()
        timed_out = False
    res = uart.read()
    coolant_temp = res[8]-CALIBRATION_OFFSET
    # shift bytes over here as rpm is hi+lo byte
    rpm = (res[16] << 8)|res[15]
    lcd.putstr(f"CLT:{coolant_temp}°C       \nRPM:{rpm}       \n")
    sleep_ms(POLL_MS)
