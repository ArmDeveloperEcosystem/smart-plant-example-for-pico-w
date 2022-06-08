#
# Copyright (c) 2022 Arm Limited and Contributors. All rights reserved.
#
# SPDX-License-Identifier: MIT
#

import json
import random
import time

import config

# read a JSON file
def load_json_file(filename):
    with open(filename) as input:
        j = json.load(input)

    return j


# create a randomized time in seconds for the specified parameters
def random_mktime(year, month, mday, hour, minute=None, second=None, timezone_offset=0):
    return time.mktime(
        (
            year,
            month,
            mday,
            hour,
            minute if minute is not None else random.randrange(59),
            second if second is not None else random.randrange(59),
            0,
            0,
        )
    ) - (timezone_offset * 60 * 60)


# check if a specific time in seconds has passed
def has_time_passed(t):
    if t is None:
        return False

    return (t - time.time()) < 0


# send a randomized message from a message category as an SMS message via Twilio
def send_message(category, messages, twilio_client):
    if category not in messages:
        print(f'Invalid message category "{category}" !')

    message = random.choice(messages[category])

    print(f"*** {category}: {message.encode()}")

    twilio_client.messages.create(config.TWILIO_TO, config.TWILIO_FROM, message)


# display an name tag on the display
def display_name(display, name):
    display.fill(0xFFFF)
    display.fill_rect(0, 0, 160, 40, 0x9883)
    display.fill_rect(0, 70, 160, 10, 0x9883)
    display.text("HELLO", 60, 10, 0xFFFF)
    display.text("my name is", 40, 25, 0xFFFF)
    display.text(name, (160 - len(name) * 8) // 2, 50, 0x0000)

    display.update()
