# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Unit tests for the Timer class."""

import asyncio

from aiounittest.case import AsyncTestCase

from tools.timer import Timer


class CallCounter:
    """Simple counter for Timer unit tests."""
    def __init__(self):
        self.counter = 0

    async def increase_counter(self, value: int = 1):
        """Increase the counter by value."""
        self.counter += value


class TestTimer(AsyncTestCase):
    """Unit tests for the Timer class."""
    async def test_non_repeating_timer(self):
        """Unit test for a non repeating timer with callback without arguments."""
        timer_delay = 3
        counter = CallCounter()

        timer = Timer(False, timer_delay, counter.increase_counter)
        await asyncio.sleep(timer_delay - 0.5)
        self.assertEqual(counter.counter, 0)
        self.assertTrue(timer.is_running())
        await asyncio.sleep(1)
        self.assertFalse(timer.is_running())
        self.assertEqual(counter.counter, 1)

    async def test_non_repeating_timer_with_argument(self):
        """Unit test for a non repeating timer with callback with argument."""
        timer_delay = 2
        value = 12
        counter = CallCounter()

        timer = Timer(False, timer_delay, counter.increase_counter, value)
        await asyncio.sleep(timer_delay - 0.5)
        self.assertEqual(counter.counter, 0)
        self.assertTrue(timer.is_running())
        await asyncio.sleep(1)
        self.assertFalse(timer.is_running())
        self.assertEqual(counter.counter, value)

    async def test_repeating_timer(self):
        """Unit test for a repeating timer."""
        timer_delay = 2.5
        counter = CallCounter()

        timer = Timer(True, timer_delay, counter.increase_counter)
        await asyncio.sleep(timer_delay - 0.5)
        self.assertTrue(timer.is_running())
        self.assertEqual(counter.counter, 0)
        await asyncio.sleep(1)
        self.assertEqual(counter.counter, 1)

        await asyncio.sleep(timer_delay - 1)
        self.assertEqual(counter.counter, 1)
        await asyncio.sleep(1)
        self.assertEqual(counter.counter, 2)

        await asyncio.sleep(timer_delay - 1)
        self.assertEqual(counter.counter, 2)
        await asyncio.sleep(1)
        self.assertEqual(counter.counter, 3)

        self.assertTrue(timer.is_running())
        await timer.cancel()
        self.assertFalse(timer.is_running())
        self.assertEqual(counter.counter, 3)

    async def test_multiple_timers(self):
        """Unit test with multiple timers running at once."""
        timer_delays = [2, 1.5, 0.2, 3.2, 2.3]
        counter = CallCounter()

        self.assertEqual(counter.counter, 0)
        timers = [
            Timer(False, timer_delay, counter.increase_counter)
            for timer_delay in timer_delays
        ]

        await asyncio.sleep(max(timer_delays) + 0.5)
        self.assertEqual(counter.counter, len(timers))

        for timer in timers:
            self.assertFalse(timer.is_running())
