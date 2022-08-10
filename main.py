import machine
from time import sleep_ms, ticks_ms, ticks_diff
import struct
CALIBRATION_OFFSET = 40
POLL_MS = 500
uart = machine.UART(0, 115200, tx=machine.Pin(0), rx=machine.Pin(1))

while True:
    uart.write('A')
    start = ticks_ms()
    while uart.any() < 76:
        if ticks_diff(ticks_ms(), start) > 5000:
            print("Timeout reading speeduino")
    res = uart.read()
    coolant_temp = res[8]-CALIBRATION_OFFSET
    rpm = (res[16] << 8)|res[15]
    print(f"CLT: {coolant_temp}, RPM: {rpm}")
    sleep_ms(POLL_MS)
