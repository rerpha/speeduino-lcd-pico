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
TIMEOUT_MS = 999
RETRY_AMOUNT = 3
READ_COMMAND = 'A'
RESPONSE_BYTES = 76
SPARK_STATUS_LKUP = {0: "launchHard", 1: "launchSoft", 2:"hardLimitOn", 3:"softLimitOn", 4:"boostCutSpark", 5:"error", 6:"idleControlOn", 7:"sync",}

# Set up UART for speeduino comms
uart = machine.UART(0, 115200, tx=machine.Pin(0), rx=machine.Pin(1))

# Set up I2C for LCD comms
i2c = machine.I2C(1, sda=machine.Pin(26), scl=machine.Pin(27), freq=400000)
I2C_ADDR = i2c.scan()[0]
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

# Set up the button for toggling pages
BUTTON_PIN = 12
button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
DEFAULT_PAGE = 1
page = DEFAULT_PAGE

def try_rx(uart):
    uart.write(READ_COMMAND)
    while uart.any() < RESPONSE_BYTES:
        for i in range(RETRY_AMOUNT):
            start = ticks_ms()
            sleep_ms(TIMEOUT_MS/RETRY_AMOUNT)
            uart.write(READ_COMMAND)
        # Timed out
        return None
    return uart.read()

while True:
    if not button.value():
        page += 1
    
    res = try_rx(uart)
    lcd.clear()
    if res is None:
        lcd.putstr("Timeout")
    
    # As the speedy sends back the command first, the byte you read is +1 what it says in the manual
    coolant_temp = res[8]-CALIBRATION_OFFSET
    # shift bytes over here as rpm is hi+lo byte
    rpm = (res[16] << 8)|res[15]
    bat_voltage = res[10]
    incr_num_comms = res[1]
    spark_advance = res[24]
    spark_status_raw = res[32]
    spark_status = SPARK_STATUS_LKUP[spark_status_raw]

    if page == 1:
        lcd.putstr(f"CLT:{coolant_temp}°C       \nRPM:{rpm}       \n")
    elif page == 2:
        lcd.putstr(f"SPKADV:{spark_advance}     \nSPKST:{spark_status}")
    elif page == 3:
        lcd.putstr(f"VOLT:{bat_voltage}V        \nCOMM:{incr_num_comms}")

    sleep_ms(POLL_MS)
