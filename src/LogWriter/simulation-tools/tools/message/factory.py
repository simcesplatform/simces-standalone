# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains a message factory that can be used to create message objects
   from the JSON contents without explicitly specifying the message class."""

from __future__ import annotations
from typing import List, Type, TYPE_CHECKING

from tools.tools import FullLogger

# used https://www.stefaanlippens.net/circular-imports-type-hints-python.html
# to avoid errors with circular imports with BaseMessage being used in type hints for MessageFactory
if TYPE_CHECKING:
    from tools.message.abstract import BaseMessage

LOGGER = FullLogger(__name__)


class MessageFactory:
    """Class for creating instances of non-abstract message classes,
       i.e. subclasses of BaseMessage that have non-empty definition for class constant CLASS_MESSAGE_TYPE.
    """
    # TODO: implement unit test for the message factory (in addition to what callback unit test do)
    __message_types = {}

    @classmethod
    def register_message_type(cls, message_type: Type[BaseMessage]):
        """Registers the given message class to the message factory.
           Registration will fail if the CLASS_MESSAGE_TYPE for the given class is empty or
           a message class with the same CLASS_MESSAGE_TYPE has already been registered to the factory
        """
        if message_type.CLASS_MESSAGE_TYPE == "":
            LOGGER.warning("Cannot register {:s} to the message factory".format(
                getattr(message_type, "__name__", str(message_type))))
        elif message_type.CLASS_MESSAGE_TYPE in cls.__message_types:
            LOGGER.warning("Type {:s} has already been registered to the message factory".format(
                message_type.CLASS_MESSAGE_TYPE))
        else:
            cls.__message_types[message_type.CLASS_MESSAGE_TYPE] = message_type

    @classmethod
    def get_message_types(cls) -> List[str]:
        """Returns the supported message types as a list of strings."""
        return list(cls.__message_types)

    @classmethod
    def get_message(cls, message_type: str = None, **kwargs) -> BaseMessage:
        """Returns a message object corresponding the given keyword attributes.
           The type of the message object is determined by the "message_type" attribute if it is not None
           or otherwise by the "Type" attribute.
           For example, if "message_type" is None and "Type" == "Epoch", the return type will be EpochMessage.

           If the given message type is not supported by the factory or some of the attributes
           are not valid values for the message type, an exception MessageError, ValueError or TypeError will be thrown.
        """
        if message_type is None:
            message_type = kwargs.get("Type", None)

        if message_type is None:
            raise TypeError("No message type found")
        if message_type not in cls.__message_types:
            raise TypeError("Message type {:s} is not supported by the factory".format(str(message_type)))

        return cls.__message_types[message_type](**kwargs)
