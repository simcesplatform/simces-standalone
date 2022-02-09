# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains code examples for using the Timer class for timed tasks."""

import asyncio
import logging
from typing import Optional

import tools.timer
from tools.timer import Timer
from tools.tools import FullLogger

LOGGER = FullLogger(__name__, logger_level=logging.INFO)
tools.timer.LOGGER.level = logging.INFO  # to override the default logging level of DEBUG in timer module


async def print_hello_world() -> None:
    """Sends a logging message: Hello world"""
    LOGGER.info("Hello world")


async def print_hello(target: str) -> None:
    """Sends a logging message: Hello <target>"""
    LOGGER.info(f"Hello {target}")


class Counter:
    """Simple class that can add values."""
    def __init__(self) -> None:
        self.count = 0

    async def add(self, value: int, extra_message: Optional[str] = None) -> None:
        """
        Adds value to current count and sends a logging message with the current total.
        If extra_message is not None, also logs the given extra message.
        """
        self.count += value
        LOGGER.info(f"Current total: {self.count}")

        if extra_message is not None:
            LOGGER.info(f"Message: {extra_message}")


async def start_timer_test() -> None:
    """Starts the tests for the timed tasks."""
    task_list = []

    LOGGER.info("Setting up Hello world task to be done in 1.5 seconds.")
    hello_world_task = Timer(False, 1.5, print_hello_world)
    task_list.append(hello_world_task)

    LOGGER.info("Setting up Hello John Doe task to be done in 4 seconds.")
    hello_john_task = Timer(False, 4, print_hello, "John Doe")
    task_list.append(hello_john_task)

    LOGGER.info("Setting up Hello Jane Doe task to be done in 3 seconds.")
    hello_jane_task = Timer(False, 3, print_hello, "Jane Doe")
    task_list.append(hello_jane_task)

    counter = Counter()
    LOGGER.info("Setting up a repeating counter task to add 2 to the total once per second.")
    counter_task = Timer(True, 1.0, counter.add, 2)

    LOGGER.info("Setting up a non-repeating counter task with the extra_message parameter.")
    extra_counter_task = Timer(False, 10, counter.add, 0, extra_message="Extra message")
    task_list.append(extra_counter_task)
    LOGGER.info("")

    # wait for each of the non-repeating tasks to be finished before exiting
    for task in task_list:
        while task.is_running():
            await asyncio.sleep(1.0)

    # allow the repeating counter task to continue for another 5.5 seconds
    await asyncio.sleep(5.5)

    LOGGER.info("Canceling the repeating counter task.")
    # NOTE: also the non-repeating tasks can be cancelled in the same way
    await counter_task.cancel()
    LOGGER.info("counter_task.is_running() = {}".format(counter_task.is_running()))

    LOGGER.info("Exiting in 3 seconds.")
    await asyncio.sleep(3)


if __name__ == '__main__':
    asyncio.run(start_timer_test())
