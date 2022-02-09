# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Module containing utility functions related to datetime values."""

import datetime
from typing import Union

from tools.tools import FullLogger

LOGGER = FullLogger(__name__)

UTC_TIMEZONE_MARK = "Z"
DIGITS_IN_MILLISECONDS = 3


def get_utcnow_in_milliseconds() -> str:
    """Returns the current ISO 8601 format datetime string in UTC timezone."""
    isoformat_with_milliseconds = isoformat_to_milliseconds(datetime.datetime.utcnow().isoformat())
    if isoformat_with_milliseconds is None:
        LOGGER.error("Unexpected error when trying to get current time in ISO 8601 format")
        return "1970-01-01T00:00:00.000Z"

    return isoformat_with_milliseconds + UTC_TIMEZONE_MARK


def to_iso_format_datetime_string(datetime_value: Union[str, datetime.datetime]) -> Union[str, None]:
    """Returns the given datetime value as ISO 8601 formatted string in UTC timezone.
       Accepts either datetime objects or strings.
       Return None if the given values was invalid."""
    if isinstance(datetime_value, datetime.datetime):
        isoformat_with_milliseconds = isoformat_to_milliseconds(
            datetime_value.astimezone(datetime.timezone.utc).isoformat())
        if isoformat_with_milliseconds is None:
            return None
        return isoformat_with_milliseconds + UTC_TIMEZONE_MARK
    if isinstance(datetime_value, str):
        datetime_object = to_utc_datetime_object(datetime_value)
        return to_iso_format_datetime_string(datetime_object)
    return None


def to_utc_datetime_object(datetime_str: str) -> datetime.datetime:
    """Returns a datetime object corresponding to the given ISO 8601 formatted string."""
    return datetime.datetime.fromisoformat(datetime_str.replace(UTC_TIMEZONE_MARK, "+00:00"))


def isoformat_to_milliseconds(datetime_str: str) -> Union[str, None]:
    """Returns the given ISO 8601 format datetime string in millisecond precision.
       Also removes timezone information."""
    date_mark_index = datetime_str.find("T")
    if date_mark_index < 0:
        return None

    plus_mark_index = datetime_str.find("+", date_mark_index)
    if plus_mark_index >= 0:
        datetime_str = datetime_str[:plus_mark_index]

    minus_mark_index = datetime_str.find("-", date_mark_index)
    if minus_mark_index >= 0:
        datetime_str = datetime_str[:minus_mark_index]

    second_fraction_mark_index = datetime_str.find(".")
    if second_fraction_mark_index >= 0:
        number_of_decimals = len(datetime_str) - second_fraction_mark_index
        return (
            datetime_str[:second_fraction_mark_index + DIGITS_IN_MILLISECONDS + 1] +
            "0" * max(DIGITS_IN_MILLISECONDS - number_of_decimals, 0)
        )

    return datetime_str + "." + "0" * DIGITS_IN_MILLISECONDS
