# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains classes for the callbacks for the RabbitMQ message bus listeners."""

import asyncio
import inspect
import json
from typing import Awaitable, Callable, Union

import aio_pika.message

from tools.exceptions.messages import MessageError
from tools.messages import (
    AbstractMessage, AbstractResultMessage, BaseMessage, EpochMessage, GeneralMessage,
    SimulationStateMessage, StatusMessage, MessageFactory)
from tools.tools import FullLogger

CallbackFunctionType = Callable[[Union[BaseMessage, dict, str], str], Awaitable[None]]

LOGGER = FullLogger(__name__)


class MessageCallback():
    """The callback class for handling received messages that are instances of AbstractMessage.
       Stores the latest received message and the corresponding topic name.
    """
    MESSAGE_CODING = "UTF-8"
    MESSAGE_TYPE_ATTRIBUTE = next(iter(BaseMessage.MESSAGE_ATTRIBUTES))  # should be "Type"
    DEFAULT_MESSAGE_TYPE = GeneralMessage.CLASS_MESSAGE_TYPE

    def __init__(self, callback_function: CallbackFunctionType, message_type: Union[str, None] = None):
        """Sets up a callback that receives incoming messages from the message bus, transforms the received object
           to an instance of BaseMessage and sends the transformed object to the given callback_function.

           Requirement for the callback_function is that it is awaitable and can be called by two parameters:
           the message object and the topic name.

           In case the message received from the message bus did not conform to the predefined message definitions,
           a dictionary containing the received message is send to the callback_function instead of
           AbstractMessage object. In case the received message was not in JSON format, a string containing the message
           is used as the first parameter for the callback_function instead.

           If message_type is None, the actual type for the transformed message is determined by the "Type" attribute.
           Otherwise, the given message type is used for as transformed message type.
           The legal string for the parameter message_type are defined in tools.messages.MESSAGE_TYPES
        """
        self.__lock = asyncio.Lock()
        self.__callback_function = callback_function

        if message_type is not None and message_type not in MessageFactory.get_message_types():
            self.__message_type = self.__class__.DEFAULT_MESSAGE_TYPE
        else:
            self.__message_type = message_type

        self.__last_message = None
        self.__last_topic = None

    @property
    def last_message(self) -> Union[BaseMessage, dict, str, None]:
        """Returns the last message that was received."""
        return self.__last_message

    @property
    def last_topic(self) -> Union[str, None]:
        """Returns the topic from which the last message was received."""
        return self.__last_topic

    def log_last_message(self) -> None:
        """Writes a log message based on the last received message."""
        if isinstance(self.last_message, SimulationStateMessage):
            LOGGER.info("Received simulation state message '{:s}' from '{:s}'".format(
                self.last_message.simulation_state, self.last_message.source_process_id))
        elif isinstance(self.last_message, EpochMessage):
            LOGGER.info("Epoch message received from '{:s}' for epoch number {:d} ({:s} - {:s})".format(
                self.last_message.source_process_id,
                self.last_message.epoch_number,
                self.last_message.start_time,
                self.last_message.end_time))
        elif isinstance(self.last_message, StatusMessage):
            LOGGER.info("Status message received from '{:s}' for epoch number {:d} with value: {:s}".format(
                self.last_message.source_process_id,
                self.last_message.epoch_number,
                self.last_message.value))
        elif isinstance(self.last_message, AbstractResultMessage):
            LOGGER.info("Received '{:s}' message from '{:s}' for epoch {:d}".format(
                self.last_message.message_type,
                self.last_message.source_process_id,
                self.last_message.epoch_number))
        elif isinstance(self.last_message, AbstractMessage):
            LOGGER.info("Received '{:s}' message from '{:s}' on topic '{:s}'".format(
                self.last_message.message_type,
                self.last_message.source_process_id,
                self.last_topic))
        elif isinstance(self.last_message, BaseMessage):
            LOGGER.info("Received message from topic '{:s}'".format(self.last_topic))
        elif isinstance(self.last_message, dict):
            LOGGER.info("Received a JSON message with errors: '{:s}'".format(json.dumps(self.last_message)))
        elif self.last_message is None:
            LOGGER.warning("No last message found.")
        else:
            LOGGER.warning("The last message in unknown format: '{:s}'".format(str(self.last_message)))

    async def callback(self, message: aio_pika.message.IncomingMessage) -> None:
        """Callback function for the received messages from the message bus.
           Transforms the message to an instance of AbstractMessage and sends it to the callback_function.
        """
        # Use a lock to be able to handle each incoming message one at a time.
        async with self.__lock:
            message_str = ""
            message_json = {}
            try:
                message_str = message.body.decode(MessageCallback.MESSAGE_CODING)
                message_json = json.loads(message_str)

                if self.__message_type is None:
                    # Convert the message to the specified special cases if possible.
                    expected_message_type = message_json.get(
                        self.__class__.MESSAGE_TYPE_ATTRIBUTE,
                        self.__class__.DEFAULT_MESSAGE_TYPE)
                    if expected_message_type not in MessageFactory.get_message_types():
                        expected_message_type = self.__class__.DEFAULT_MESSAGE_TYPE
                else:
                    expected_message_type = self.__message_type

                message_object = MessageFactory.get_message(
                    message_type=expected_message_type,
                    **message_json,
                )

            except json.decoder.JSONDecodeError:
                LOGGER.warning("Received message could not be decoded into JSON format.")
                message_object = message_str
            except (TypeError, ValueError, MessageError) as message_error:
                # The message did not conform to the simulation platform message schema or
                # the message type was not supported by the message factory.
                LOGGER.warning("Received {:s} error when creating message object: {:s}".format(
                    type(message_error).__name__, str(message_error)
                ))
                message_object = message_json

            self.__last_message = message_object
            self.__last_topic = message.routing_key
            self.log_last_message()

            if inspect.iscoroutinefunction(self.__callback_function):
                asyncio.create_task(self.__callback_function(message_object, message.routing_key))
            else:
                LOGGER.error("Callback function '{:s}' is not awaitable.".format(
                    str(getattr(self.__callback_function, "__name__", None))))
