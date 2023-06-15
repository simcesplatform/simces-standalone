# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains a client class for sending and listening to messages using a RabbitMQ message bus."""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Union, cast

import aio_pika
from aio_pika.exceptions import CONNECTION_EXCEPTIONS

from tools.callbacks import CallbackFunctionType, MessageCallback
from tools.messages import AbstractMessage
from tools.tools import (
    FullLogger, handle_async_exception, load_environmental_variables,
    EnvironmentVariableType, EnvironmentVariableValue)

LOGGER = FullLogger(__name__)
aio_pika.robust_connection.log = LOGGER.logger

RECONNECT_INTERVAL = 30
CONNECTION_CREATION_INTERVAL = 5
MAX_CONNECTION_TRIES = 18


def default_env_variable_definitions() -> List[Tuple[str, EnvironmentVariableType, EnvironmentVariableValue]]:
    """Returns the default environment variable definitions for RabbitmqClient."""
    def env_variable_name(simple_variable_name: str) -> str:
        return "{:s}{:s}".format(RabbitmqClient.DEFAULT_ENV_VARIABLE_PREFIX, simple_variable_name.upper())

    return [
        (env_variable_name("host"), str, "localhost"),
        (env_variable_name("port"), int, 5672),
        (env_variable_name("login"), str, ""),
        (env_variable_name("password"), str, ""),
        (env_variable_name("ssl"), bool, False),
        (env_variable_name("ssl_version"), str, "PROTOCOL_TLS"),
        (env_variable_name("exchange"), str, ""),
        (env_variable_name("exchange_autodelete"), bool, False),
        (env_variable_name("exchange_durable"), bool, False)
    ]


def load_config_from_env_variables() -> Dict[str, Optional[EnvironmentVariableValue]]:
    """Returns configuration dictionary from which values are fetched from environmental variables."""
    def simple_name(env_variable_name: str) -> str:
        return env_variable_name[len(RabbitmqClient.DEFAULT_ENV_VARIABLE_PREFIX):].lower()

    env_variables = load_environmental_variables(*default_env_variable_definitions())

    return {
        simple_name(variable_name): env_variables[variable_name]
        for variable_name in env_variables
    }


def validate_message(topic_name: str, message_to_publish: Union[bytes, AbstractMessage]) \
        -> Union[Tuple[None, None], Tuple[str, bytes]]:
    """Validates the message received from a queue for publishing.
       Returns a tuple (topic_name: str, message_to_publish: bytes) if the message is valid.
       Otherwise, returns (None, None)."""
    # Note: no checking for the contents of the message are done currently.
    if not isinstance(topic_name, str):
        topic_name = str(topic_name)
    if isinstance(message_to_publish, AbstractMessage):
        message_to_publish = message_to_publish.bytes()

    if topic_name == "":
        LOGGER.warning("Topic name for the message to publish was empty.")
        return None, None

    if not isinstance(message_to_publish, bytes):
        LOGGER.warning("Wrong message type ('{:s}') for publishing.".format(str(type(message_to_publish))))
        return None, None

    return topic_name, message_to_publish


class RabbitmqExchangeParameters:
    """Class for holding the parameters required for declaring an exchange for RabbitMQ message bus."""
    def __init__(self, exchange_name: str, exchange_autodelete: bool, exchange_durable: bool):
        self.__exchange_name = exchange_name
        self.__auto_delete = exchange_autodelete
        self.__durable = exchange_durable

    @property
    def exchange_name(self) -> str:
        """Returns the name for the exchange."""
        return self.__exchange_name

    @property
    def auto_delete(self) -> bool:
        """Returns the auto_delete parameter for the exchange."""
        return self.__auto_delete

    @property
    def durable(self) -> bool:
        """Returns the durable parameter for the exchange."""
        return self.__durable


class RabbitmqConnection:
    """Class for holding a RabbitMQ connection including the channel and exchange.
       This is mainly intended for the use of RabbitmqClient objects.
    """
    def __init__(self, connection_parameters: dict, exchange_parameters: RabbitmqExchangeParameters):
        self.__connection_parameters = connection_parameters
        self.__exchange_parameters = exchange_parameters

        self.__rabbitmq_connection = None
        self.__rabbitmq_channel = None
        self.__rabbitmq_exchange = None

    async def get_connection(self) -> Optional[aio_pika.connection.ConnectionType]:
        """Returns a RabbitMQ connection. Creates the connection on the first call.
           If the connection has been closed, tries to create a new connection."""
        if self.__rabbitmq_connection is None or self.__rabbitmq_connection.is_closed:
            connection_created = False
            connection_creation_interval = 0.0
            connection_try_number = 0

            async def update_connection_attempt_variables(try_number: int, interval: float) -> Tuple[int, float]:
                try_number += 1
                interval += CONNECTION_CREATION_INTERVAL

                if try_number < MAX_CONNECTION_TRIES:
                    LOGGER.info("Trying to create the connection again in {} seconds.".format(
                        interval))
                    await asyncio.sleep(interval)
                else:
                    LOGGER.error("Giving up on trying to connect to the RabbitMQ message bus.")
                    self.__rabbitmq_connection = None

                return try_number, interval

            while not connection_created and connection_try_number < MAX_CONNECTION_TRIES:
                try:
                    LOGGER.debug("Creating new connection to RabbitMQ message bus")
                    self.__rabbitmq_connection = await aio_pika.connect_robust(
                        reconnect_interval=RECONNECT_INTERVAL,
                        **self.__connection_parameters,
                    )

                    if not self.__rabbitmq_connection.is_closed:
                        connection_created = True
                    else:
                        connection_try_number, connection_creation_interval = \
                            await update_connection_attempt_variables(
                                connection_try_number, connection_creation_interval)

                except CONNECTION_EXCEPTIONS as connection_error:
                    LOGGER.warning("When creating RabbitMQ connection, received: {} : {}".format(
                        type(connection_error).__name__, connection_error))
                    connection_try_number, connection_creation_interval = \
                        await update_connection_attempt_variables(connection_try_number, connection_creation_interval)

            self.__rabbitmq_channel = None
            self.__rabbitmq_exchange = None

        return self.__rabbitmq_connection  # pyright: reportGeneralTypeIssues=false

    async def get_channel(self) -> Optional[aio_pika.channel.Channel]:
        """Returns a channel for a RabbitMQ connection. Creates the channel on the first call."""
        if self.__rabbitmq_channel is None or self.__rabbitmq_channel.is_closed:
            connection = await self.get_connection()
            if connection is None:
                LOGGER.warning("No RabbitMQ connection found, setting channel to None")
                self.__rabbitmq_channel = None

            else:
                try:
                    self.__rabbitmq_channel = await connection.channel()
                except CONNECTION_EXCEPTIONS as channel_error:
                    LOGGER.warning("When creating RabbitMQ channel, received: {} : {}".format(
                        type(channel_error).__name__, channel_error))
                    self.__rabbitmq_channel = None

            self.__rabbitmq_exchange = None

        return self.__rabbitmq_channel

    async def get_exchange(self) -> Optional[aio_pika.exchange.Exchange]:
        """Returns an exchange for a RabbitMQ connection. Declares the exchange on the first call.
           No checking to ensure that exchange still exists on later calls."""
        if self.__rabbitmq_exchange is None:
            channel = await self.get_channel()
            if channel is None:
                LOGGER.warning("No RabbitMQ channel found, setting exchange to None")
                self.__rabbitmq_exchange = None

            else:
                try:
                    self.__rabbitmq_exchange = await channel.declare_exchange(
                        name=self.__exchange_parameters.exchange_name,
                        type=aio_pika.exchange.ExchangeType.TOPIC,
                        auto_delete=self.__exchange_parameters.auto_delete,
                        durable=self.__exchange_parameters.durable)
                except CONNECTION_EXCEPTIONS as exchange_error:
                    LOGGER.warning("When creating RabbitMQ channel, received: {} : {}".format(
                        type(exchange_error).__name__, exchange_error))
                    self.__rabbitmq_exchange = None

        return self.__rabbitmq_exchange

    async def close(self) -> None:
        """Closes the RabbitMQ connection."""
        if self.__rabbitmq_connection is not None and not self.__rabbitmq_connection.is_closed:
            root_logger = logging.getLogger()
            root_logger_level = root_logger.level
            try:
                # suppress the log messages when closing the connection
                root_logger.setLevel(logging.CRITICAL)
                await self.__rabbitmq_connection.close()
            except CONNECTION_EXCEPTIONS as closing_error:
                LOGGER.warning("When closing RabbitMQ connection, received: {} : {}".format(
                    type(closing_error).__name__, closing_error))
            finally:
                root_logger.setLevel(root_logger_level)

        self.__rabbitmq_connection = None
        self.__rabbitmq_channel = None
        self.__rabbitmq_exchange = None


class RabbitmqClient:
    """RabbitMQ client that can be used to send messages and to create topic listeners."""
    DEFAULT_ENV_VARIABLE_PREFIX = "RABBITMQ_"
    CONNECTION_PARAMTERS = ["host", "port", "login", "password", "ssl"]
    OPTIONAL_SSL_PARAMETER_TOP = "ssl_options"
    OPTIONAL_SSL_PARAMETER = "ssl_version"

    EXCHANGE_ATTRIBUTE_NAME = "exchange"
    EXCHANGE_ATTRIBUTE_AUTODELETE = "exchange_autodelete"
    EXCHANGE_ATTRIBUTE_DURABLE = "exchange_durable"
    EXCHANGE_PARAMETERS = [EXCHANGE_ATTRIBUTE_NAME, EXCHANGE_ATTRIBUTE_AUTODELETE, EXCHANGE_ATTRIBUTE_DURABLE]

    FULL_ATTRIBUTE_NAME_LIST = CONNECTION_PARAMTERS + [OPTIONAL_SSL_PARAMETER] + EXCHANGE_PARAMETERS

    MESSAGE_ENCODING = "UTF-8"

    def __init__(self, **kwargs):
        """Available attributes, all other attributes are ignored:
           - host         : the host name for the RabbitMQ server
           - port         : the port number for the RabbitMQ server
           - login        : username for access to the RabbitMQ server
           - password     : password for access to the RabbitMQ server
           - ssl          : use SSL connection to the RabbitMQ server
           - ssl_version  : the SSL version parameter for the SSL connection
           - exchange     : the name for the exchange used by the client
           - exchange_autodelete  : whether to automatically delete the exchange after use
           - exchange_durable     : whether to setup the exchange to survive message bus restarts

           If a value for attribute is missing from kwargs, the value is read from
           the corresponding environmental variable with the given default value as a backup.
           - RABBITMQ_HOST (default value: "localhost")
           - RABBITMQ_PORT (default value: 5672)
           - RABBITMQ_LOGIN (default value: "")
           - RABBITMQ_PASSWORD (default value: "")
           - RABBITMQ_SSL (default value: False)
           - RABBITMQ_SSL_VERSION (default value: "PROTOCOL_TLS")
           - RABBITMQ_EXCHANGE (default value: "")
           - RABBITMQ_EXCHANGE_AUTODELETE (default value: False)
           - RABBITMQ_EXCHANGE_DURABLE (default value: False)
        """
        kwargs_env = load_config_from_env_variables()
        kwargs = {
            attribute_name: kwargs.get(attribute_name, kwargs_env[attribute_name])
            for attribute_name in RabbitmqClient.FULL_ATTRIBUTE_NAME_LIST
        }

        self.__connection_parameters = RabbitmqClient.__get_connection_parameters_only(kwargs)
        self.__exchange_parameters = RabbitmqExchangeParameters(
            exchange_name=cast(str, kwargs[RabbitmqClient.EXCHANGE_ATTRIBUTE_NAME]),
            exchange_autodelete=cast(bool, kwargs[RabbitmqClient.EXCHANGE_ATTRIBUTE_AUTODELETE]),
            exchange_durable=cast(bool, kwargs[RabbitmqClient.EXCHANGE_ATTRIBUTE_DURABLE]))

        self.__send_connection = RabbitmqConnection(self.__connection_parameters, self.__exchange_parameters)
        self.__listened_topics = set()
        self.__listener_tasks = []

        self.__lock = asyncio.Lock()
        self.__is_closed = False

        # Add a custom exception handler for exceptions in asynchronous tasks because connection problems
        # or closing RabbitMQ connection can throw them.
        asyncio.get_event_loop().set_exception_handler(handle_async_exception)

    async def close(self) -> None:
        """Closes the sender connection and all the listener connections."""
        async with self.__lock:
            await self.remove_listeners()
            await self.__send_connection.close()
            self.__is_closed = True

    @property
    def is_closed(self) -> bool:
        """Returns True if the connections for the client have been closed."""
        return self.__is_closed

    @property
    def exchange_name(self) -> str:
        """Returns the RabbitMQ exchange name that the client uses."""
        return self.__exchange_parameters.exchange_name

    @property
    def listened_topics(self) -> List[str]:
        """Returns a list of the topics the client is currently listening."""
        return list(self.__listened_topics)

    def add_listener(self, topic_names: Union[str, List[str]], callback_function: CallbackFunctionType) -> None:
        """Adds a new topic listener to the client for the given topic(s). One listener can listen to multiple topics.
           Each topic name should be an acceptable routing key for RabbitMQ.

           The given callback_function is called after each received message.
           Requirement for the callback_function is that it is awaitable and can be called by two parameters:
           the message object and the topic name.

           In case the message received from the message bus did not conform to the predefined message definitions,
           a dictionary containing the received message is send to the callback_function instead of
           AbstractMessage object. In case the received message was not in JSON format, a string containing the message
           is used as the first parameter for the callback_function instead.
        """
        if self.is_closed:
            LOGGER.warning("Client is closed, no topic listener added.")
            return

        if isinstance(topic_names, str):
            topic_names = [topic_names]

        new_connection = RabbitmqConnection(self.__connection_parameters, self.__exchange_parameters)
        listener_task = asyncio.create_task(self.__listen_to_topics(
            connection_class=new_connection,
            topic_names=topic_names,
            callback_class=MessageCallback(callback_function)
        ))

        self.__listener_tasks.append(listener_task)
        for topic_name in topic_names:
            self.__listened_topics.add(topic_name)

    async def remove_listeners(self) -> None:
        """Removes all topic listeners from the client."""
        for listener_task in self.__listener_tasks:
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass

        self.__listener_tasks = []
        self.__listened_topics = set()

    async def send_message(self, topic_name: str, message_bytes: bytes) -> None:
        """Sends the given message to the given topic. Assumes that the message is in bytes format."""
        async with self.__lock:
            if self.is_closed:
                LOGGER.warning("Message not sent because the client is closed.")
                return

            validated_topic_name, message_to_publish = validate_message(topic_name, message_bytes)
            if validated_topic_name is None or message_to_publish is None:
                return

            try:
                send_exchange = await self.__send_connection.get_exchange()
                if send_exchange is None:
                    LOGGER.warning("Cannot publish message because there is no connection")
                    return

                await send_exchange.publish(aio_pika.Message(message_to_publish), routing_key=topic_name)
                LOGGER.debug("Message '{:s}' send to topic: '{:s}'".format(
                    message_to_publish.decode(RabbitmqClient.MESSAGE_ENCODING), topic_name))

            except SystemExit:
                LOGGER.debug("SystemExit received when trying to publish message.")
                await self.__send_connection.close()
                raise
            except CONNECTION_EXCEPTIONS as error:
                LOGGER.warning("{}: '{}' when trying to publish message.".format(type(error).__name__, error))
            except GeneratorExit:
                LOGGER.warning("GeneratorExit received when trying to publish message.")

    async def __listen_to_topics(self, connection_class: RabbitmqConnection, topic_names: Union[str, List[str]],
                                 callback_class: MessageCallback) -> None:
        """Starts a RabbitMQ message bus listener for the given topics."""
        if isinstance(topic_names, str):
            topic_names = [topic_names]

        async def wait_before_reconnecting():
            LOGGER.info("Could not create a connection. Trying again in {} seconds.".format(RECONNECT_INTERVAL))
            await asyncio.sleep(RECONNECT_INTERVAL)

        reconnect_listeners = True
        while reconnect_listeners:
            # by default, no reconnect unless there is a reason for it
            reconnect_listeners = False
            LOGGER.info("Opening RabbitMQ listener for the topics: '{:s}'".format(", ".join(topic_names)))

            try:
                rabbitmq_connection = await connection_class.get_connection()
                if rabbitmq_connection is None:
                    reconnect_listeners = True
                    await wait_before_reconnecting()
                    continue

                async with rabbitmq_connection:
                    rabbitmq_channel = await connection_class.get_channel()
                    if rabbitmq_channel is not None:
                        rabbitmq_queue = await rabbitmq_channel.declare_queue(
                            auto_delete=True,  # Delete the queue when no one uses it anymore
                            exclusive=True     # No other application can access the queue; delete on exit
                        )
                        rabbitmq_exchange = await connection_class.get_exchange()
                    else:
                        rabbitmq_queue = None
                        rabbitmq_exchange = None
                        reconnect_listeners = True

                    if rabbitmq_queue is not None and rabbitmq_exchange is not None:
                        # Binding the queue to the given topics
                        for topic_name in topic_names:
                            await rabbitmq_queue.bind(rabbitmq_exchange, routing_key=topic_name)
                            LOGGER.info("Now listening to messages; exc={}, topic={}".format(
                                rabbitmq_exchange.name, topic_name))

                        async with rabbitmq_queue.iterator() as queue_iter:
                            async for message in queue_iter:
                                async with message.process():
                                    LOGGER.debug("Message '{}' received from topic: '{}'".format(
                                        message.body.decode(RabbitmqClient.MESSAGE_ENCODING), message.routing_key))
                                    asyncio.create_task(callback_class.callback(message))

                if reconnect_listeners:
                    await wait_before_reconnecting()

            except SystemExit:
                LOGGER.warning("SystemExit received when trying to listen to the message bus.")
                await connection_class.close()
                raise

            except CONNECTION_EXCEPTIONS as error:
                LOGGER.warning("{}: '{}' when trying to listen to the message bus.".format(
                    type(error).__name__, error))
                reconnect_listeners = True
                await wait_before_reconnecting()

        LOGGER.info("Closing listener for topics: '{:s}'".format(", ".join(topic_names)))
        await connection_class.close()

    @classmethod
    def __get_connection_parameters_only(cls, connection_config_dict: dict) -> dict:
        """Returns only the parameters needed for creating a connection."""
        stripped_connection_config = {
            config_parameter: parameter_value
            for config_parameter, parameter_value in connection_config_dict.items()
            if config_parameter in cls.CONNECTION_PARAMTERS
        }
        if stripped_connection_config["ssl"]:
            stripped_connection_config[cls.OPTIONAL_SSL_PARAMETER_TOP] = {
                cls.OPTIONAL_SSL_PARAMETER: connection_config_dict[cls.OPTIONAL_SSL_PARAMETER]
            }

        return stripped_connection_config
