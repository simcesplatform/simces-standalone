# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains a Timer class that can be used to set up events at some point in the future."""

# Based on https://phoolish-philomath.com/asynchronous-task-scheduling-in-python.html

import asyncio
from typing import Awaitable, Callable, Union

from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class Timer:
    """Timer class that sets up either a single timed task or a periodic task that can be cancelled."""
    def __init__(self, is_repeating: bool, timeout: Union[int, float],
                 callback: Callable[..., Awaitable[None]], *args, **kwargs):
        """Starts a timer. The given callback function is called with the given parameters after timeout seconds.
           If is_repeating is True, The given timed task is repeated until cancel() is called for the Timer."""
        self.__is_repeating = is_repeating
        self.__timeout = timeout
        self.__callback = callback
        self.__args = args
        self.__kwargs = kwargs
        self.__task = asyncio.create_task(self.__timed_task())

    def is_running(self) -> bool:
        """Returns True, if the timer is running."""
        return self.__task is not None and not self.__task.done()

    async def cancel(self) -> None:
        """Cancels the timed task."""
        if self.is_running():
            self.__task.cancel()

            try:
                await self.__task
            except asyncio.CancelledError:
                LOGGER.debug("Timer cancelled: {:s}".format(str(self)))

    def __str__(self) -> str:
        return "{:s}".format(str({
            "is_repeating": self.__is_repeating,
            "timeout": self.__timeout,
            "is_running": self.is_running(),
            "callback": self.__callback.__name__
        }))

    async def __timed_task(self) -> None:
        """Sleeps for timeout seconds and calls the callback function after the sleep."""
        while True:
            LOGGER.debug("Timer started: {:s}".format(str(self)))
            await asyncio.sleep(self.__timeout)
            await self.__callback(*self.__args, **self.__kwargs)

            if not self.__is_repeating:
                break

        LOGGER.debug("Timer finished: {:s}".format(str(self)))
