# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>
#            Otto Hylli <otto.hylli@tuni.fi>

"""Module containing classes for holding the simulation metadata for the simulation platform."""

import asyncio
import datetime
from typing import Awaitable, Callable, Dict, List, Optional, Set, Union, cast

from tools.datetime_tools import to_utc_datetime_object, to_iso_format_datetime_string
from tools.db_clients import MongodbClient
from tools.messages import AbstractMessage, AbstractResultMessage, BaseMessage, EpochMessage, SimulationStateMessage
from tools.timer import Timer
from tools.tools import FullLogger, load_environmental_variables

from log_writer.invalid_message import InvalidMessage

LOGGER = FullLogger(__name__)

MESSAGE_BUFFER_MAX_DOCUMENTS_NAME = "MESSAGE_BUFFER_MAX_DOCUMENTS"
MESSAGE_BUFFER_MAX_INTERVAL_NAME = "MESSAGE_BUFFER_MAX_INTERVAL"

ENV_VARIABLES = load_environmental_variables(
    (MESSAGE_BUFFER_MAX_DOCUMENTS_NAME, int, 20),
    (MESSAGE_BUFFER_MAX_INTERVAL_NAME, float, 10.0)
)


class SimulationMetadata:
    """Class for holding simulation metadata and to store the simulation messages to MongoDB."""
    SIMULATION_STARTED, SIMULATION_ENDED = SimulationStateMessage.SIMULATION_STATES

    def __init__(self, simulation_id: str, mongo_client: MongodbClient):
        self.__simulation_id = simulation_id
        self.__name = None
        self.__description = None
        self.__components = set()
        self.__topic_messages = {}

        self.__start_time = None
        self.__start_flag = False
        self.__end_time = None
        self.__end_flag = False

        self.__epoch_min = None
        self.__epoch_max = None

        self.__lock = asyncio.Lock()
        self.__message_buffer = []
        self.__buffer_timer = None
        self.__buffer_max_documents = cast(int, ENV_VARIABLES[MESSAGE_BUFFER_MAX_DOCUMENTS_NAME])
        self.__buffer_max_interval = cast(float, ENV_VARIABLES[MESSAGE_BUFFER_MAX_INTERVAL_NAME])

        self.__mongo_client = mongo_client

    @property
    def simulation_id(self) -> str:
        """The simulation identifier."""
        return self.__simulation_id

    @property
    def start_time(self) -> Union[datetime.datetime, None]:
        """The start time for the simulation."""
        return self.__start_time

    @property
    def end_time(self) -> Union[datetime.datetime, None]:
        """The end time for the simulation."""
        return self.__end_time

    @property
    def start_flag(self) -> bool:
        """Returns True if the starting simulation state message has been logged."""
        return self.__start_flag

    @property
    def end_flag(self) -> bool:
        """Returns True if the ending simulation state message has been logged."""
        return self.__end_flag

    @property
    def epoch_min(self) -> Union[int, None]:
        """Returns the smallest logged epoch number."""
        return self.__epoch_min

    @property
    def epoch_max(self) -> Union[int, None]:
        """Returns the largest logged epoch number."""
        return self.__epoch_max

    @property
    def name(self) -> Union[str, None]:
        """Returns the simulation name."""
        return self.__name

    @property
    def description(self) -> Union[str, None]:
        """Returns the description for the simulation."""
        return self.__description

    @property
    def components(self) -> Set[str]:
        """Returns the simulation component names as a list."""
        return self.__components

    @property
    def total_messages(self) -> int:
        """Returns the total number of messages logged for the simulation."""
        return sum(self.__topic_messages.values())

    @property
    def topic_messages(self) -> Dict[str, int]:
        """Returns a dictionary with the topic names as keys and
           the total number of messages logged for that topic as values."""
        return self.__topic_messages

    async def clear_buffer(self):
        """Sends all the messages from the buffer to the database."""
        async with self.__lock:
            if len(self.__message_buffer) >= 1:
                # valid and invalid messages are stored separately so sort buffer to two lists.
                valid_messages = []
                invalid_messages = []
                for message, topic in self.__message_buffer:
                    if isinstance(message, InvalidMessage):
                        invalid_messages.append((message.json(), topic))
                    else:
                        valid_messages.append((message.json(), topic))

                # store both kinds of messages and check if the process succeeded.
                store_valid_task = asyncio.create_task(self.__mongo_client.store_messages(valid_messages))
                store_invalid_task = asyncio.create_task(self.__mongo_client.store_messages(
                    invalid_messages, invalid=True, default_simulation_id=self.simulation_id))
                for task, messages, message_type in [
                        (store_valid_task, valid_messages, "valid"),
                        (store_invalid_task, invalid_messages, "invalid")
                ]:
                    stored_messages = await task

                    if len(stored_messages) != len(messages):
                        LOGGER.warning(
                            "Only {:d} {:s} message documents out of {:d} written to simulation {:s}.".format(
                                len(stored_messages), message_type, len(messages), self.__simulation_id))
                    else:
                        LOGGER.debug("{:d} {:s} documents written to simulation {:s}".format(
                            len(stored_messages), message_type, self.__simulation_id))

            self.__message_buffer = []
            self.__buffer_timer = None

    async def add_message(self, message_object: BaseMessage, message_topic: str):
        """Logs the message to the simulation."""
        # Check for the start or end flags.
        if isinstance(message_object, SimulationStateMessage):
            if message_object.simulation_state == SimulationMetadata.SIMULATION_STARTED:
                self.__start_flag = True
            elif message_object.simulation_state == SimulationMetadata.SIMULATION_ENDED:
                self.__end_flag = True
            self.__name = message_object.name
            self.__description = message_object.description

        # Check the timestamp for the earliest or the latest messages.
        message_timestamp = to_utc_datetime_object(message_object.timestamp)
        if self.start_time is None or message_timestamp < self.start_time:
            self.__start_time = message_timestamp
        if self.end_time is None or message_timestamp > self.end_time:
            self.__end_time = message_timestamp

        # Add to the simulation component list.
        if isinstance(message_object, AbstractMessage):
            self.__components.add(message_object.source_process_id)

        # Check for the smallest or the largest epoch.
        if isinstance(message_object, AbstractResultMessage):
            if self.epoch_min is None or message_object.epoch_number < self.epoch_min:
                self.__epoch_min = message_object.epoch_number
            if self.epoch_max is None or message_object.epoch_number > self.epoch_max:
                self.__epoch_max = message_object.epoch_number

        # Add to topic message count.
        if message_topic not in self.__topic_messages:
            self.__topic_messages[message_topic] = 0
        self.__topic_messages[message_topic] += 1

        # Store the message to the message buffer
        async with self.__lock:
            self.__message_buffer.append((message_object, message_topic))
            if self.__buffer_timer is None:
                self.__buffer_timer = Timer(False, cast(float, self.__buffer_max_interval), self.clear_buffer)

        # Clear the message buffer if the buffer is full or
        # if the last message was a simulation state or an epoch message.
        if (len(self.__message_buffer) >= self.__buffer_max_documents or
                isinstance(message_object, (SimulationStateMessage, EpochMessage))):
            await self.clear_buffer()

        # Update the metadata to the database if the message was simulation state or epoch message.
        # The first and the last message for a simulation should be simulation state message.
        if isinstance(message_object, (SimulationStateMessage, EpochMessage)):
            await self.update_database_metadata()

        # Add indexes to the simulation specific collection after the simulation has ended.
        if (isinstance(message_object, SimulationStateMessage) and
                message_object.simulation_state == SimulationStateMessage.SIMULATION_STATES[-1] and
                message_object.simulation_id is not None):
            await self.__mongo_client.add_simulation_indexes(message_object.simulation_id)

    async def update_database_metadata(self):
        """Updates the metadata into the database."""
        metadata_attributes = {
            "StartTime": self.start_time,
            "Name": self.__name,
            "Description": self.__description,
            "Epochs": self.epoch_max,
            "Processes": sorted(list(self.components))
        }
        if self.end_flag:
            metadata_attributes["EndTime"] = self.end_time

        db_result = await self.__mongo_client.update_metadata(self.__simulation_id, **metadata_attributes)
        if db_result:
            LOGGER.info("Database metadata update successful for '{:s}'".format(self.simulation_id))
        else:
            LOGGER.warning("Database metadata update failed for '{:s}'".format(self.simulation_id))

    def __str__(self) -> str:
        start_time_str = str(to_iso_format_datetime_string(str(self.start_time)))
        end_time_str = str(to_iso_format_datetime_string(str(self.end_time)))

        return "\n    ".join([
            self.simulation_id,
            "name: " + str(self.name),
            "description: " + str(self.description),
            "start time: " + (start_time_str if self.start_flag else "({:s})".format(start_time_str)),
            "end_time: " + (end_time_str if self.end_flag else "({:s})".format(end_time_str)),
            "components: {:s}".format(", ".join(self.components)),
            "epochs: {:s} - {:s}".format(str(self.epoch_min), str(self.epoch_max)),
            "total messages: {:d}".format(self.total_messages),
            "topic messages: {:s}".format(str(self.topic_messages))
        ])


class SimulationMetadataCollection:
    """Class for containing metadata and storing the information to MongoDB for several simulations."""
    def __init__(self, stop_function: Callable[..., Awaitable[None]] = None):
        self.__simulations = {}

        self.__mongo_client = MongodbClient()
        self.__first_message = False

        # the function that is called when receiving a simulation state message "stopped"
        self.__stop_function = stop_function

    @property
    def simulations(self) -> List[str]:
        """The simulation ids as a list."""
        return list(self.__simulations.keys())

    def get_simulation(self, simulation_id: str) -> Union[SimulationMetadata, None]:
        """Returns the metadata object for simulation with the id simulation_id.
           Returns None, if the metadata is not found."""
        return self.__simulations.get(simulation_id, None)

    async def add_message(self, message_object: BaseMessage, message_topic: str, simulation_id: Optional[str] = None):
        """Logs the message to the simulation collection.
        Invalid messages do not have a simulation id so simulation_id is used with them."""
        if not self.__first_message:
            await self.__mongo_client.update_metadata_indexes()
            self.__first_message = True

        if not isinstance(message_object, InvalidMessage):
            simulation_id = message_object.simulation_id
        elif simulation_id is None:
            LOGGER.warning("Cannot store invalid message without simulation id")
            return

        if simulation_id is not None and simulation_id not in self.__simulations:
            self.__simulations[simulation_id] = SimulationMetadata(simulation_id, self.__mongo_client)
            LOGGER.info("New simulation started: '{:s}'".format(simulation_id))
        await self.__simulations[simulation_id].add_message(message_object, message_topic)

        if (isinstance(message_object, SimulationStateMessage) and
                self.__stop_function is not None and
                message_object.simulation_state == SimulationMetadata.SIMULATION_ENDED):
            asyncio.create_task(self.__stop_function())
