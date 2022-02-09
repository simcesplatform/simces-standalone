# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains general utils for working with simulation platform message classes."""

from __future__ import annotations
from typing import Any, Dict, Union

from tools.exceptions.messages import MessageValueError
from tools.message.abstract import AbstractResultMessage, BaseMessage, get_json
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class GeneralMessage(BaseMessage):
    """Class for a generic message containing at least all the required attributes from BaseMessage.
       Useful when making general use message listeners and
       handling message types that have not yet been implemented."""
    CLASS_MESSAGE_TYPE = "General"

    MESSAGE_ATTRIBUTES = {}
    OPTIONAL_ATTRIBUTES = []

    MESSAGE_ATTRIBUTES_FULL = {
        **BaseMessage.MESSAGE_ATTRIBUTES_FULL,
        **MESSAGE_ATTRIBUTES
    }
    OPTIONAL_ATTRIBUTES_FULL = BaseMessage.OPTIONAL_ATTRIBUTES_FULL + OPTIONAL_ATTRIBUTES

    def __init__(self, **kwargs):
        """All the given arguments are considered. The required arguments for AbstractMessage are checked
           and if they contain invalid values, an instance of MessageError is thrown.
           All other arguments are used as general attributes.
        """
        super().__init__(**kwargs)

        self.general_attributes = {
            general_attribute_name: general_attribute_value
            for general_attribute_name, general_attribute_value in kwargs.items()
            if general_attribute_name not in self.__class__.MESSAGE_ATTRIBUTES_FULL
        }

    @property
    def general_attributes(self) -> Dict[str, Any]:
        """A dictionary containing all the optional attributes."""
        return self.__general_attributes

    @general_attributes.setter
    def general_attributes(self, general_attributes: dict):
        if not self._check_general_attributes(general_attributes):
            raise MessageValueError("'{:s}' is an invalid general attribute dictionary".format(
                str(general_attributes)))

        self.__general_attributes = general_attributes

    def __eq__(self, other: Any) -> bool:
        return (
            super().__eq__(other) and
            isinstance(other, GeneralMessage) and
            self.general_attributes == other.general_attributes
        )

    @classmethod
    def _check_message_type(cls, message_type: str) -> bool:
        # only check the existence of the type here, not the actual contents
        return isinstance(message_type, str) and len(message_type) > 0

    @classmethod
    def _check_general_attributes(cls, general_attributes: Dict[str, Any]) -> bool:
        return isinstance(general_attributes, dict)

    def json(self) -> Dict[str, Any]:
        """Returns the message as a JSON object."""
        general_attributes_json = {}
        for attribute_name, attribute_value in self.general_attributes.items():
            if getattr(attribute_value, "json", None) is None:
                general_attributes_json[attribute_name] = attribute_value
            else:
                general_attributes_json[attribute_name] = attribute_value.json()

        return {**get_json(self), **general_attributes_json}

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[GeneralMessage, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON does not contain valid values, returns None."""
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None


class ResultMessage(AbstractResultMessage):
    """Class for a generic result message containing at least all the required attributes for AbstractResultMessage."""
    CLASS_MESSAGE_TYPE = "Result"

    MESSAGE_ATTRIBUTES = {}
    OPTIONAL_ATTRIBUTES = []

    MESSAGE_ATTRIBUTES_FULL = {
        **AbstractResultMessage.MESSAGE_ATTRIBUTES_FULL,
        **MESSAGE_ATTRIBUTES
    }
    OPTIONAL_ATTRIBUTES_FULL = AbstractResultMessage.OPTIONAL_ATTRIBUTES_FULL + OPTIONAL_ATTRIBUTES

    def __init__(self, **kwargs):
        """All the given arguments are considered. The required arguments for AbstractResultMessage
           are checked and if they contain invalid values, an instance of MessageError is thrown.
           All other arguments are used as result values.
        """
        super().__init__(**kwargs)

        self.result_values = {
            value_attribute_name: value_attribute_value
            for value_attribute_name, value_attribute_value in kwargs.items()
            if value_attribute_name not in self.__class__.MESSAGE_ATTRIBUTES_FULL
        }

    @property
    def result_values(self) -> Dict[str, Any]:
        """A dictionary containing all the result value attributes."""
        return self.__result_values

    @result_values.setter
    def result_values(self, result_values: Dict[str, Any]):
        if not self._check_result_values(result_values):
            raise MessageValueError("'{:s}' is an invalid result value dictionary".format(str(result_values)))

        self.__result_values = result_values

    def __eq__(self, other: Any) -> bool:
        return (
            super().__eq__(other) and
            isinstance(other, ResultMessage) and
            self.result_values == other.result_values
        )

    @classmethod
    def _check_result_values(cls, result_values: Dict[str, Any]) -> bool:
        return isinstance(result_values, dict)

    def json(self) -> Dict[str, Any]:
        """Returns the message as a JSON object."""
        result_values_json = {}
        for result_name, result_value in self.result_values.items():
            if getattr(result_value, "json", None) is None:
                result_values_json[result_name] = result_value
            else:
                result_values_json[result_name] = result_value.json()

        return {**get_json(self), **result_values_json}

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[ResultMessage, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON does not contain valid values, returns None."""
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None


GeneralMessage.register_to_factory()
ResultMessage.register_to_factory()
