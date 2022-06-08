#
# Copyright (c) 2022 Arm Limited and Contributors. All rights reserved.
#
# SPDX-License-Identifier: MIT
#

import urequests
import ubinascii


def url_encode(s):
    result = ""

    for c in s:
        if c.isalpha() or c.isdigit() or c == "-" or c == "_" or c == "." or c == "~":
            result += c
        elif c == " ":
            result += "+"
        else:
            for b in c.encode():
                result += f"%{b:02x}"

    return result


def form_encode(data):
    result = ""

    for key, value in data.items():
        if len(result) > 0:
            result += "&"

        result += url_encode(key)
        result += "="
        result += url_encode(value)

    return result


class TwilioMessage:
    def __init__(self, json_):
        self.sid = json_["sid"]


class TwilioMessagesClient:
    def __init__(self, client):
        self._client = client

    def create(self, to, from_, body):
        data = {"To": to, "Body": body, "From": from_}

        status_code, response = self._client.request("POST", "/Messages.json", data)

        return TwilioMessage(response)


class Client:
    def __init__(self, account_sid, auth_token):
        self._base_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"
        self._authorization_header = (
            "Basic "
            + ubinascii.b2a_base64(f"{account_sid}:{auth_token}").decode().rstrip()
        )

        self.messages = TwilioMessagesClient(self)

    def request(self, method, uri, data=None, headers=None):
        url = self._base_url + uri

        if headers is None:
            headers = {}

        headers["Authorization"] = self._authorization_header

        if data and isinstance(data, dict):
            headers["Content-Type"] = "application/x-www-form-urlencoded"

            data = form_encode(data)

        response = urequests.request(method, url, data=data, headers=headers)

        status_code = response.status_code
        json_ = response.json()

        response.close()

        return status_code, json_


class Rest:
    def __init__(self):
        self.Client = Client


rest = Rest()
