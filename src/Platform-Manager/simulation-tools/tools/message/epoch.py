# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains the message class for the simulation platform epoch messages."""

from __future__ import annotations
import datetime
from typing import Any, Dict, Union

from tools.datetime_tools import to_iso_format_datetime_string
from tools.exceptions.messages import MessageDateError, MessageValueError
from tools.message.abstract import AbstractResultMessage
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class EpochMessage(AbstractResultMessage):
    """Class containing all the attributes for a epoch message."""
    CLASS_MESSAGE_TYPE = "Epoch"
    MESSAGE_TYPE_CHECK = True

    MESSAGE_ATTRIBUTES = {
        "StartTime": "start_time",
        "EndTime": "end_time"
    }
    OPTIONAL_ATTRIBUTES = []

    MESSAGE_ATTRIBUTES_FULL = {
        **AbstractResultMessage.MESSAGE_ATTRIBUTES_FULL,
        **MESSAGE_ATTRIBUTES
    }
    OPTIONAL_ATTRIBUTES_FULL = AbstractResultMessage.OPTIONAL_ATTRIBUTES_FULL + OPTIONAL_ATTRIBUTES

    @property
    def start_time(self) -> str:
        """The attribute for the start time of the epoch."""
        return self.__start_time

    @property
    def end_time(self) -> str:
        """The attribute for the end time of the epoch."""
        return self.__end_time

    @start_time.setter
    def start_time(self, start_time: Union[str, datetime.datetime]):
        if self._check_start_time(start_time):
            new_start_time = to_iso_format_datetime_string(start_time)

            # Check that the start time is not after the end time.
            if isinstance(new_start_time, str):
                if getattr(self, "end_time", None) is not None and new_start_time >= self.end_time:
                    raise MessageValueError("Epoch start time ({:s}) should be before the end time ({:s})".format(
                        new_start_time, self.end_time))
                self.__start_time = new_start_time
                return

        raise MessageDateError("'{:s}' is an invalid datetime".format(str(start_time)))

    @end_time.setter
    def end_time(self, end_time: Union[str, datetime.datetime]):
        if self._check_end_time(end_time):
            new_end_time = to_iso_format_datetime_string(end_time)

            # Check that the end time is not before the start time.
            if isinstance(new_end_time, str):
                if getattr(self, "start_time", None) is not None and new_end_time <= self.start_time:
                    raise MessageValueError("Epoch end time ({:s}) should be after the start time ({:s})".format(
                        new_end_time, self.start_time))
                self.__end_time = new_end_time
                return

        raise MessageDateError("'{:s}' is an invalid datetime".format(str(end_time)))

    def __eq__(self, other: Any) -> bool:
        return (
            super().__eq__(other) and
            isinstance(other, EpochMessage) and
            self.start_time == other.start_time and
            self.end_time == other.end_time
        )

    @classmethod
    def _check_start_time(cls, start_time: Union[str, datetime.datetime]) -> bool:
        return cls._check_datetime(start_time)

    @classmethod
    def _check_end_time(cls, end_time: Union[str, datetime.datetime]) -> bool:
        return cls._check_datetime(end_time)

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[EpochMessage, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON does not contain valid values, returns None."""
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None


EpochMessage.register_to_factory()
