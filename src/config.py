#
# SPDX-FileCopyrightText: Copyright 2022 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: MIT
#

# Name to display on name tag

NAME = "Mark the Plant"

# Wi-Fi SSID and password

WIFI_SSID = "SSID"
WIFI_PASSWORD = ""


# Twilio Account SID, auth. token, to and from phone numbers

TWILIO_ACCOUNT_SID = ""
TWILIO_AUTH_TOKEN = ""
TWILIO_FROM = ""
TWILIO_TO = ""


# Timezone offset in hours

TIMEZONE_OFFSET = -4


# Hour to send good morning and night messages, in 24 hour format

GOOD_MORNING_HOUR = 7
GOOD_NIGHT_HOUR = 19

# Thresholds for light and proximity sensors,
# good morning messages will only be set if bright,
# good night messages will only be set if dark and nothing in close proximity.

LUX_BRIGHT_THRESHOLD = 10
LUX_DARK_THRESHOLD = 5
PROXIMITY_THRESHOLD = 50

# Threshold for moisture sensor

SOIL_DRY_THRESHOLD = 20
SOIL_WET_THRESHOLD = 10
