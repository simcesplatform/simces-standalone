# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>
#            Otto Hylli <otto.hylli@tuni.fi>

"""Module containing class for invalid messages received from the message bus."""

from typing import Any, Dict, Optional, Union

from tools.messages import BaseMessage
from tools.tools import FullLogger
from tools.exceptions.messages import MessageValueError

LOGGER = FullLogger(__name__)


class InvalidMessage(BaseMessage):
    """
    Represents a invalid message.
    Note, though this is a BaseMessage subclass it does not have a type or simulation_id instead they are always None.
    """
    CLASS_MESSAGE_TYPE = "InvalidMessage"
    MESSAGE_TYPE_CHECK = False

    MESSAGE_ATTRIBUTES = {
        "InvalidMessage": "invalid_message",
        "InvalidJsonMessage": "invalid_json_message"
    }

    # Type and SimulationId are optional or in fact not used here.
    OPTIONAL_ATTRIBUTES = ["InvalidMessage", "InvalidJsonMessage", "SimulationId", "Type"]

    QUANTITY_BLOCK_ATTRIBUTES = {}

    QUANTITY_ARRAY_BLOCK_ATTRIBUTES = {}

    TIMESERIES_BLOCK_ATTRIBUTES = []

    MESSAGE_ATTRIBUTES_FULL = {
        **BaseMessage.MESSAGE_ATTRIBUTES_FULL,
        **MESSAGE_ATTRIBUTES
    }
    OPTIONAL_ATTRIBUTES_FULL = BaseMessage.OPTIONAL_ATTRIBUTES_FULL + OPTIONAL_ATTRIBUTES
    QUANTITY_BLOCK_ATTRIBUTES_FULL = {
        **BaseMessage.QUANTITY_BLOCK_ATTRIBUTES_FULL,
        **QUANTITY_BLOCK_ATTRIBUTES
    }
    QUANTITY_ARRAY_BLOCK_ATTRIBUTES_FULL = {
        **BaseMessage.QUANTITY_ARRAY_BLOCK_ATTRIBUTES_FULL,
        **QUANTITY_ARRAY_BLOCK_ATTRIBUTES
    }
    TIMESERIES_BLOCK_ATTRIBUTES_FULL = (
        BaseMessage.TIMESERIES_BLOCK_ATTRIBUTES_FULL +
        TIMESERIES_BLOCK_ATTRIBUTES
    )

    @property
    def invalid_message(self) -> Optional[dict]:
        """The actual invalid message which could not be converted to a proper message class instance.
        If the message could not be converted to JSON this is None
        and the message can be found from the invalid_json_message property."""
        return self.__invalid_message

    @property
    def invalid_json_message(self) -> Optional[str]:
        """Actual invalid message which was invalid JSON.
        If the message is valid JSON this is None and the message can be found from the invalid_message property."""
        return self.__invalid_json_message

    @property
    def simulation_id(self) -> None:
        """Invalid messages do not contain a simulation id so this is always None."""
        return None

    @property
    def message_type(self) -> None:
        """Invalid messages do not contain a type so this is always None."""
        return None

    @invalid_message.setter
    def invalid_message(self, invalid_message: Union[dict, None]):
        """Set invalid message value."""
        if self._check_invalid_message(invalid_message):
            self.__invalid_message = invalid_message
        else:
            raise MessageValueError("Invalid message should be a dict or None.")

    @invalid_json_message.setter
    def invalid_json_message(self, invalid_json_message: str):
        """Set invalid json message value."""
        if self._check_invalid_json_message(invalid_json_message):
            self.__invalid_json_message = invalid_json_message
        else:
            raise MessageValueError("Invalid value for invalid json message, should be string or None.")

    @simulation_id.setter
    def simulation_id(self, simulation_id: Any):
        """Setter for simulation id. Only None is accepted."""
        if self._check_simulation_id(simulation_id):
            self.__simulation_id = None
        else:
            raise MessageValueError("Simulation id for invalid message must be None.")

    @message_type.setter
    def message_type(self, message_type: Any):
        """Setter for message type. Only None is accepted."""
        if self._check_message_type(message_type):
            self.__message_type = None
        else:
            raise MessageValueError("Message type for invalid message must be None.")

    def __eq__(self, other: Any) -> bool:
        """Equality check."""
        return (
            super().__eq__(other) and
            isinstance(other, InvalidMessage) and
            self.invalid_message == other.invalid_message and
            self.invalid_json_message == other.invalid_json_message
        )

    @classmethod
    def _check_invalid_message(cls, invalid_message: Optional[dict]) -> bool:
        """Check that invalid message value is dict or None."""
        return invalid_message is None or isinstance(invalid_message, dict)

    @classmethod
    def _check_invalid_json_message(cls, invalid_json_message: Optional[str]):
        """Check that invalid json message is string or None."""
        return invalid_json_message is None or isinstance(invalid_json_message, str)

    @classmethod
    def _check_simulation_id(cls, simulation_id: Any) -> bool:
        """Check that simulation id is None."""
        return simulation_id is None

    @classmethod
    def _check_message_type(cls, message_type: Any) -> bool:
        """Check that message type is None."""
        return message_type is None

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[BaseMessage, None]:
        """Create instance from a dictionary."""
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None
