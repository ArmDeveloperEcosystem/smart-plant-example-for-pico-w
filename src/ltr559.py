#
# SPDX-FileCopyrightText: Copyright 2022 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: MIT
#

import time

_I2C_ADDRESS = const(0x23)
_ALS_CONTR_ADDRESS = const(0x80)
_PS_CONRT_ADDRESS = const(0x81)
_PART_ID_ADDRESS = const(0x86)
_MANUFAC_ID_ADDRESS = const(0x87)
_ALS_DATA_CHAN1_0_ADDRESS = const(0x88)
_ALS_DATA_CHAN1_1_ADDRESS = const(0x89)
_ALS_DATA_CHAN0_0_ADDRESS = const(0x8A)
_ALS_DATA_CHAN0_1_ADDRESS = const(0x8B)
_PS_DATA_0_ADDRESS = const(0x8D)
_PS_DATA_1_ADDRESS = const(0x8E)


class LTR559:
    def __init__(self, i2c):
        self._i2c = i2c

    def init(self):
        part_id = self.read_part_id()
        if part_id is not 0x92:
            raise Exception("Unexpected part id!")

        manufac_id = self.read_manufac_id()
        if manufac_id is not 0x05:
            raise Exception("Unexpected manufac id!")

        self.reset()

        self.write_register(_ALS_CONTR_ADDRESS, 0x01)
        self.write_register(_PS_CONRT_ADDRESS, 0x03)

    def read_part_id(self):
        return self.read_register(_PART_ID_ADDRESS)

    def read_manufac_id(self):
        return self.read_register(_MANUFAC_ID_ADDRESS)

    def reset(self):
        self.write_register(_ALS_CONTR_ADDRESS, 0x02)

        time.sleep(0.01)

        while True:
            als_contr = self.read_register(_ALS_CONTR_ADDRESS)

            if als_contr is 0x00:
                break

            time.sleep(0.05)

    def read_proximity(self):
        ps_data_0 = self.read_register(_PS_DATA_0_ADDRESS)
        ps_data_1 = self.read_register(_PS_DATA_1_ADDRESS)

        proximity = ((ps_data_1 & 0x03) << 8) | ps_data_0

        return proximity

    def read_lux(self):
        als_data_ch1_0 = self.read_register(_ALS_DATA_CHAN1_0_ADDRESS)
        als_data_ch1_1 = self.read_register(_ALS_DATA_CHAN1_1_ADDRESS)
        als_data_ch0_0 = self.read_register(_ALS_DATA_CHAN0_0_ADDRESS)
        als_data_ch0_1 = self.read_register(_ALS_DATA_CHAN0_1_ADDRESS)

        als_data_ch1 = (als_data_ch1_1 << 8) | als_data_ch1_0
        als_data_ch0 = (als_data_ch0_1 << 8) | als_data_ch0_0

        # based on: https://android.googlesource.com/kernel/msm/+/android-msm-seed-3.10-lollipop-mr1/drivers/input/misc/ltr559.c#379
        if (als_data_ch0 + als_data_ch1) == 0:
            ratio = 1000
        else:
            ratio = als_data_ch1 * 1000 / (als_data_ch1 + als_data_ch0)

        if ratio < 450:
            lux = ((17743 * als_data_ch0) + (11059 * als_data_ch1)) / 10000
        elif ratio < 640:
            lux = ((42785 * als_data_ch0) - (19548 * als_data_ch1)) / 10000
        elif ratio < 850:
            lux = ((5926 * als_data_ch0) + (1185 * als_data_ch1)) / 10000
        else:
            lux = 0

        return lux

    def read_register(self, address):
        return self._i2c.readfrom_mem(_I2C_ADDRESS, address, 1)[0]

    def write_register(self, address, value):
        self._i2c.writeto_mem(_I2C_ADDRESS, address, bytearray([value]))
