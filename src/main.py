#
# SPDX-FileCopyrightText: Copyright 2022 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: MIT
#

# MicroPython imports
import json
import network
import ntpclient
import random
import time

from machine import I2C, Pin, SPI

# Custom imports
import config
import ltr559
import moisture_sensor
import st7735
import utils
import utwilio

#
# Global variables
#

wlan = None

soil_is_dry = False

good_morning_message_time = None
good_night_message_time = None
random_message_time = None


#
# App start
#

# set the random seed, so messages are randomized
random.seed()

# load the messages from the JSON file
messages = utils.load_json_file("messages.json")

# create instances of the display, light sensor, moisture sensor drivers, and Twilio client
display = st7735.ST7735R(
    spi=SPI(id=0, baudrate=125000000, sck=Pin(18), mosi=Pin(19)),
    cs=Pin(17),
    dc=Pin(16),
    width=160,
    height=80,
)

light_sensor = ltr559.LTR559(i2c=I2C(id=0, scl=Pin(5), sda=Pin(4)))

soil_sensor = moisture_sensor.MoistureSensor(Pin(8))

twilio_client = utwilio.rest.Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)

# initialize the display, light sensor, and moisture sensor
display.init()
light_sensor.init()
soil_sensor.init()

# initialize the Wi-Fi interface
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.disconnect()
time.sleep(0.1)

while True:
    # check if the Wi-Fi interface is connected
    if not wlan.isconnected():
        # not connected, update the display
        display.fill(0xFFFF)
        display.text("Connecting to Wi-Fi", 2, 7, 0x0000)
        display.text(config.WIFI_SSID, 10, 25, 0x0000)
        display.update()

        print(f"Connecting to Wi-Fi SSID: {config.WIFI_SSID}")
        wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

        # connect to the Wi-Fi network:
        while not wlan.isconnected():
            time.sleep(0.5)

        # sync current time via NTP
        ntpclient.settime()

        print(f"Connected to Wi-Fi SSID: {config.WIFI_SSID}")

        # Wi-Fi connected, display the name tag
        utils.display_name(display, config.NAME)

    # read the light and proximity sensor values
    lux = light_sensor.read_lux()
    proximity = light_sensor.read_proximity()

    # Check if a good morning, good night, or random message needs to be sent.
    # Good morning messages will only be sent when the Lux value exceeds the threshold,
    # good night messages will only be sent when the Lux value is below the threshold and
    # nothing in close proximity.
    if (
        utils.has_time_passed(good_morning_message_time)
        and lux > config.LUX_BRIGHT_THRESHOLD
    ):
        utils.send_message("morning", messages, twilio_client)

        good_morning_message_time = None

    if (
        utils.has_time_passed(good_night_message_time)
        and lux < config.LUX_DARK_THRESHOLD
        and proximity < config.PROXIMITY_THRESHOLD
    ):
        utils.send_message("night", messages, twilio_client)

        good_night_message_time = None

    if utils.has_time_passed(random_message_time):
        utils.send_message("random", messages, twilio_client)

        random_message_time = None

    # read the soil moisture
    soil_moisture = soil_sensor.read()

    if soil_is_dry:
        if soil_moisture < config.SOIL_WET_THRESHOLD:
            # soil was dry, but is wet now

            utils.send_message("soil_watered", messages, twilio_client)

            soil_is_dry = False
    else:
        if soil_moisture >= config.SOIL_DRY_THRESHOLD:
            # soil was NOT dry, but is dry now

            utils.send_message("soil_dry", messages, twilio_client)

            soil_is_dry = True

    # print out the sensor values
    print(f"lux = {lux}, proximity = {proximity}, soil_moisture = {soil_moisture}")

    # get the current local time components
    (
        current_year,
        current_month,
        current_month_day,
        current_hour,
        _,
        _,
        _,
        _,
    ) = time.gmtime(time.time() + config.TIMEZONE_OFFSET * 60 * 60)

    # update any scheduled greeting message times
    if good_morning_message_time is None:
        month_day_offset = int(current_hour >= config.GOOD_MORNING_HOUR)

        good_morning_message_time = utils.random_mktime(
            current_year,
            current_month,
            current_month_day + month_day_offset,
            config.GOOD_MORNING_HOUR,
            timezone_offset=config.TIMEZONE_OFFSET,
        )

        print(
            f"good_morning_message_time = {good_morning_message_time} = {time.localtime(good_morning_message_time)}"
        )

    if random_message_time is None:
        month_day_offset = int(current_hour >= config.GOOD_MORNING_HOUR)

        random_message_time = utils.random_mktime(
            current_year,
            current_month,
            current_month_day + month_day_offset,
            random.randrange(config.GOOD_MORNING_HOUR, config.GOOD_NIGHT_HOUR),
            timezone_offset=config.TIMEZONE_OFFSET,
        )

        print(
            f"random_message_time = {random_message_time} = {time.localtime(random_message_time)}"
        )

    if good_night_message_time is None:
        month_day_offset = int(current_hour >= config.GOOD_NIGHT_HOUR)

        good_night_message_time = utils.random_mktime(
            current_year,
            current_month,
            current_month_day + month_day_offset,
            config.GOOD_NIGHT_HOUR,
            timezone_offset=config.TIMEZONE_OFFSET,
        )

        print(
            f"good_night_message_time = {good_night_message_time} = {time.localtime(good_night_message_time)}"
        )

    # sleep until next loop cycle
    time.sleep(1)
