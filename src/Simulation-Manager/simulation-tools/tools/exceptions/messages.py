# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains the exception classes for the message errors."""

from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class MessageError(Exception):
    """Base class for message related errors."""
    def __init__(self, message):
        super(MessageError, self).__init__(message)
        LOGGER.error(message)
        self.message = message


class MessageTypeError(MessageError):
    """Exception class for errors related to invalid message types."""


class MessageDateError(MessageError):
    """Exception class for errors related to invalid datetimes."""


class MessageIdError(MessageError):
    """Exception class for errors related to invalid message ids."""


class MessageSourceError(MessageError):
    """Exception class for errors related to invalid sources."""


class MessageValueError(MessageError):
    """Exception class for errors related to invalid values in messages."""


class MessageEpochValueError(MessageValueError):
    """Exception class for errors related to invalid epoch values in messages."""


class MessageStateValueError(MessageValueError):
    """Exception class for errors related to invalid simulation state values in messages."""


class MessageUnitValueError(MessageValueError):
    """Exception class for errors related to invalid unit of measurement in a message block."""


class MessageBlockError(MessageError):
    """Exception class for errors related to invalid use of block attributes."""
