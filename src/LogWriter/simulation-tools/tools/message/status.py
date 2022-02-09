# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains the message class for the simulation platform status messages."""

from __future__ import annotations
from typing import Any, Dict, Union

from tools.exceptions.messages import MessageValueError
from tools.message.abstract import AbstractResultMessage
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class StatusMessage(AbstractResultMessage):
    """Class containing all the attributes for a status message."""
    CLASS_MESSAGE_TYPE = "Status"
    MESSAGE_TYPE_CHECK = True

    MESSAGE_ATTRIBUTES = {
        "Value": "value",
        "Description": "description"
    }
    OPTIONAL_ATTRIBUTES = ["Description"]  # Description SHOULD be used if status value is "error"

    STATUS_VALUES = ["ready", "error"]

    MESSAGE_ATTRIBUTES_FULL = {
        **AbstractResultMessage.MESSAGE_ATTRIBUTES_FULL,
        **MESSAGE_ATTRIBUTES
    }
    OPTIONAL_ATTRIBUTES_FULL = AbstractResultMessage.OPTIONAL_ATTRIBUTES_FULL + OPTIONAL_ATTRIBUTES

    def __init__(self, **kwargs):
        """Only arguments "Type", "SimulationId", SourceProcessId", MessageId", "Timestamp",
           "EpochNumber", "LastUpdatedInEpoch", "TriggeringMessageIds", "Warnings", and "Value" are considered.
           If one the arguments is not valid, throws an instance of MessageError.
        """
        super().__init__(**kwargs)

        # Give a warning if an error message is created without a description.
        if self.value == self.__class__.STATUS_VALUES[-1] and not self.description:
            LOGGER.info("No description for a message with status: '{:s}'".format(self.value))

    @property
    def value(self) -> str:
        """The value attribute containing the status value."""
        return self.__value

    @property
    def description(self) -> Union[str, None]:
        """The description attribute containing a description for the status.
           This SHOULD be used only with an error state."""
        return self.__description

    @value.setter
    def value(self, value: str):
        if not self._check_value(value):
            raise MessageValueError("'{:s}' is an invalid status value".format(str(value)))

        self.__value = value

    @description.setter
    def description(self, description: Union[str, None]):
        if not self._check_description(description):
            raise MessageValueError("'{:s}' is an invalid error description".format(str(description)))

        self.__description = description

    def __eq__(self, other: Any) -> bool:
        return (
            super().__eq__(other) and
            isinstance(other, StatusMessage) and
            self.value == other.value and
            self.description == other.description
        )

    @classmethod
    def _check_value(cls, value: str) -> bool:
        return isinstance(value, str) and value in cls.STATUS_VALUES

    @classmethod
    def _check_description(cls, description: Union[str, None]) -> bool:
        # Allow an empty status description.
        return description is None or isinstance(description, str)

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[StatusMessage, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON does not contain valid values, returns None."""
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None


StatusMessage.register_to_factory()
