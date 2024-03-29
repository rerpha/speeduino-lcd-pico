import machine
from time import sleep_ms, ticks_ms, ticks_diff
import struct
from pico_i2c_lcd import I2cLcd

"""
Micropython code for interfacing with a 2x16 LCD over i2c to show speeduino params using its secondary serial interface.
Pin numbers match up with PICO W diagram. 
"""

# Test mode is for simulating data - this means you don't need a physical connection to a real speeduino.
TEST_MODE=False
# Fake the LCD and just print instead, in case you haven't connected a display yet
FAKE_LCD=False

# Pins
I2C_SDA_PIN = 26
I2C_SCL_PIN = 27
BUTTON_PIN = 8
UART_TX_PIN = 0
UART_RX_PIN = 1

CALIBRATION_OFFSET = 40
POLL_MS = 200
TIMEOUT_MS = 999
RETRY_AMOUNT = 3
READ_COMMAND = 'A'
RESPONSE_BYTES = 76
SPARK_STATUS_LKUP = {0: "launchHard", 1: "launchSoft", 2:"hardLimitOn", 3:"softLimitOn", 4:"boostCutSpark", 5:"error", 6:"idleControlOn", 7:"sync",}


class FakeLCD:
    def putstr(self, out):
        print(out)
    def clear(self):
        pass

# Set up UART for speeduino comms
uart = machine.UART(0, 115200, tx=machine.Pin(UART_TX_PIN), rx=machine.Pin(UART_RX_PIN))

# Set up I2C for LCD comms
if not FAKE_LCD:
    i2c = machine.I2C(1, sda=machine.Pin(I2C_SDA_PIN), scl=machine.Pin(I2C_SCL_PIN), freq=400000)
    I2C_ADDR = i2c.scan()[0]
    lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)
else:
    lcd = FakeLCD()

# Set up the button for toggling pages
button = machine.Pin(BUTTON_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
DEFAULT_PAGE = 1
page = DEFAULT_PAGE
MAX_PAGE_NUM = 3

def try_rx(uart):
    if TEST_MODE:
        # respond with some dummy data instead of trying to read real serial i/o
        params = [0] * RESPONSE_BYTES
        params[8] = 35 # coolant

        # shift bytes over here as rpm is hi+lo byte
        test_rpm = 2000
        params[16], params[15] = divmod(test_rpm, 256)
        params[10] = 12 # batter voltage
        params[1] = 1 # incr comms num
        params[24] = 0 # spark advance
        params[32] = 7 # spark status
        
        return params
    else:
        uart.write(READ_COMMAND)
        while uart.any() < RESPONSE_BYTES:
            for i in range(RETRY_AMOUNT):
                start = ticks_ms()
                sleep_ms(int(TIMEOUT_MS/RETRY_AMOUNT))
                uart.write(READ_COMMAND)
            # Timed out
            return None
        return uart.read()

while True:
    # If button pressed, increment page number. this is a bit finnicky and might require you to hold the button,
    # as it only checks every poll cycle - should probably make the polling do something like the retry behaviour 
    # and just skip polling if poll period not reached, that way this button could be pressed any time.
    if button.value() == 0:
        page += 1
    
    res = try_rx(uart)
    
    if res is None:
        lcd.clear()
        lcd.putstr("Timeout")
        break
    
    # As the speedy sends back the command first, the byte you read is +1 what it says in the manual
    coolant_temp = res[8]-CALIBRATION_OFFSET
    # shift bytes over here as rpm is hi+lo byte
    rpm = (res[16] << 8)|res[15]
    bat_voltage = res[10]
    incr_num_comms = res[1]
    spark_advance = res[24]
    spark_status_raw = res[32]
    spark_status = SPARK_STATUS_LKUP[spark_status_raw]
    lcd.clear()
    if page > MAX_PAGE_NUM:
        # We have reached the maximum amount of pages, so loop back to page 1.
        page = 1
    if page == 1:
        lcd.putstr(f"CLT:{coolant_temp}°C       \n RPM:{rpm}       ")
    elif page == 2:
        lcd.putstr(f"SPKADV:{spark_advance}     \nSPKST:{spark_status}")
    elif page == 3:
        lcd.putstr(f"VOLT:{bat_voltage}V        \nCOMM:{incr_num_comms}")

    sleep_ms(POLL_MS)
