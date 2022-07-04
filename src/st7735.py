#
# SPDX-FileCopyrightText: Copyright 2022 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: MIT
#

import machine
import time
import framebuf

# constants
_SWRESET = const(0x01)
_SLPOUT = const(0x11)
_NORON = const(0x13)

_INVOFF = const(0x20)
_INVON = const(0x21)
_DISPON = const(0x29)
_CASET = const(0x2A)
_RASET = const(0x2B)
_RAMWR = const(0x2C)

_MADCTL = const(0x36)
_COLMOD = const(0x3A)

_FRMCTR1 = const(0xB1)
_FRMCTR2 = const(0xB2)
_FRMCTR3 = const(0xB3)
_INVCTR = const(0xB4)

_PWCTR1 = const(0xC0)
_PWCTR2 = const(0xC1)
_PWCTR3 = const(0xC2)
_PWCTR4 = const(0xC3)
_PWCTR5 = const(0xC5)
_VMCTR1 = const(0xC6)

_GMCTRP1 = const(0xE0)
_GMCTRN1 = const(0xE1)

# byte swap a 16-bit value using Arm REV16 instruction
@micropython.asm_thumb
def asm_rev16(r0):
    data(2, 0xBA40)  # REV16 r0, r0


class ST7735R:
    def __init__(self, spi, cs, dc, width=160, height=80):
        self._spi = spi
        self._cs = cs
        self._dc = dc

        self._width = width
        self._height = height

        # create buffer and frame buffer to back display
        self._buffer = bytearray(self._width * self._height * 2)
        self._framebuffer = framebuf.FrameBuffer(
            self._buffer, self._width, self._height, framebuf.RGB565
        )

    def init(self):
        self._cs.init(machine.Pin.OUT, value=1)
        self._dc.init(machine.Pin.OUT, value=1)

        self.send_command(_SWRESET)
        time.sleep(0.150)

        self.send_command(_SLPOUT)
        time.sleep(0.5)

        self.send_command(_FRMCTR1, b"\x01\x2c\x2d")
        self.send_command(_FRMCTR2, b"\x01\x2c\x2d")
        self.send_command(_FRMCTR3, b"\x01\x2c\x2d\x01\x2c\x2d")

        self.send_command(_INVCTR, 0x07)

        self.send_command(_PWCTR1, b"\xa2\x02\x84")
        self.send_command(_PWCTR2, 0xC5)
        self.send_command(_PWCTR3, b"\x0a\x00")
        self.send_command(_PWCTR4, b"\x8a\x2a")
        self.send_command(_PWCTR5, b"\x8a\xee")

        self.send_command(_VMCTR1, 0x0E)

        self.send_command(_INVOFF)

        self.send_command(_MADCTL, 0xC8)

        self.send_command(_COLMOD, 0x05)

        self.send_command(
            _GMCTRP1,
            b"\x02\x1c\x07\x12\x37\x32\x29\x2d\x29\x25\x2b\x39\x00\x01\x03\x10",
        )

        self.send_command(
            _GMCTRN1,
            b"\x03\x1d\x07\x06\x2e\x2c\x29\x2d\x2e\x2e\x37\x3f\x00\x00\x02\x10",
        )

        self.send_command(_NORON)
        time.sleep(0.01)

        self.send_command(_DISPON)
        time.sleep(0.1)

        # invert
        self.send_command(_INVON)

        # rotate 90
        self.send_command(_MADCTL, 0x80 | 0x20 | 0x08)

    # wrapper API's for underlying the framebuffer
    def fill(self, c):
        self._framebuffer.fill(asm_rev16(c))

    def pixel(self, x, y, c):
        self._framebuffer.pixel(x, y, asm_rev16(c))

    def hline(self, x, y, w, c):
        self._framebuffer.hline(x, y, w, asm_rev16(c))

    def vline(self, x, y, h, c):
        self._framebuffer.vline(x, y, h, asm_rev16(c))

    def line(self, x1, y1, x2, y2, c):
        self._framebuffer.line(x1, y1, x2, y2, asm_rev16(c))

    def rect(self, x, y, w, h, c):
        self._framebuffer.rect(x, y, w, h, asm_rev16(c))

    def fill_rect(self, x, y, w, h, c):
        self._framebuffer.fill_rect(x, y, w, h, asm_rev16(c))

    def text(self, s, x, y, c):
        self._framebuffer.text(s, x, y, asm_rev16(c))

    def set_addr_window(self, x0, y0, x1, y1):
        self.send_command(_CASET, [0x00, x0, 0x00, x1])  # XSTART, XEND

        self.send_command(_RASET, [0x00, y0, 0x00, y1])  # YSTART, YEND

    def update(self):
        x_offset = (162 - self._width) // 2
        y_offset = (132 - self._height) // 2

        self.set_addr_window(
            x_offset,
            y_offset,
            x_offset + self._width - 1,
            y_offset + self._height - 1,
        )

        self.send_command(_RAMWR, self._buffer)

    def send_command(self, cmd, data=None):
        self._cs.off()
        self._dc.off()
        self._spi.write(bytearray([cmd]))

        if data is not None:
            if isinstance(data, int):
                data = bytearray([data & 0xFF])
            elif isinstance(data, list):
                data = bytearray(data)
            self._dc.on()
            self._spi.write(data)

        self._cs.on()
