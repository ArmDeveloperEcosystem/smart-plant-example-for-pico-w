#
# SPDX-FileCopyrightText: Copyright 2022 Arm Limited and/or its affiliates <open-source-office@arm.com>
# SPDX-License-Identifier: MIT
#

import time

import rp2

# Use a PIO state machine as a (decrementing) counter
@rp2.asm_pio()
def pio_rising_edge_counter():
    set(x, 0)
    wrap_target()
    label("loop")
    wait(0, pin, 0)
    wait(1, pin, 0)
    jmp(x_dec, "loop")


class MoistureSensor:
    def __init__(self, pin, state_machine_id=1):
        self._pin = pin
        self._sm = rp2.StateMachine(state_machine_id)

    def init(self):
        self._sm.init(pio_rising_edge_counter, freq=2_000, in_base=self._pin)

        self._start = time.ticks_ms()
        self._sm.active(1)

    # returns a value between 0 (wet) to 30 (dry)
    def read(self):
        now = time.ticks_ms()
        delta = time.ticks_diff(now, self._start)

        if delta is 0:
            return 0

        # stop the PIO state machine, read the current PIO counter
        self._sm.active(0)
        self._sm.exec("mov(isr, x)")
        self._sm.exec("push()")

        # 2's complement the PIO x value
        counter = (~(self._sm.get()) + 1) & 0xFFFFFFFF

        # divide by the time passed in seconds
        val = counter // (delta / 1000)

        # reset PIO x to 0, and re-activate state machine
        self._sm.exec("set(x, 0)")
        self._start = time.ticks_ms()
        self._sm.active(1)

        return val
