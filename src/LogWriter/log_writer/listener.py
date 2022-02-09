# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>
#            Otto Hylli <otto.hylli@tuni.fi>

"""This module contains a listener simulation component that prints out all messages from the message bus."""

import asyncio
import json
import logging
from typing import cast, List, Union

from tools.callbacks import LOGGER as callback_logger
from tools.clients import RabbitmqClient
from tools.datetime_tools import to_utc_datetime_object
from tools.messages import BaseMessage, AbstractMessage, GeneralMessage
from tools.tools import EnvironmentVariable, FullLogger

from log_writer.invalid_message import InvalidMessage
from log_writer.simulation import SimulationMetadata, SimulationMetadataCollection

# No info logs about each received message stored.
callback_logger.level = max(callback_logger.level, logging.WARNING)
LOGGER = FullLogger(__name__)

STATISTICS_DISPLAY_INTERVAL = cast(int, EnvironmentVariable("STATISTICS_DISPLAY_INTERVAL", int, 60).value)
STOP_WAIT_TIMER = 15


class ListenerComponent:
    """Class for the message bus listener component."""
    LISTENED_TOPICS = "#"

    def __init__(self):
        self.__rabbitmq_client = RabbitmqClient()
        self.__rabbitmq_client.add_listener(ListenerComponent.LISTENED_TOPICS, self.simulation_message_handler)

        self.__metadata_collection = SimulationMetadataCollection(stop_function=self.stop)
        self.__is_stopped = False

        # default simulation id is used when a invalid simulation message is received
        simulation_id = EnvironmentVariable('SIMULATION_ID', str, None).value
        if simulation_id is not None:
            self.__default_simulation_id = cast(str, simulation_id)
        else:
            self.__default_simulation_id = simulation_id

    async def stop(self) -> None:
        """Stops the log writer."""
        LOGGER.info("Stopping the log writer.")
        await self.__rabbitmq_client.close()
        self.__is_stopped = True

    @property
    def simulations(self) -> List[str]:
        """Returns the received simulation ids as a list."""
        return self.__metadata_collection.simulations

    @property
    def is_stopped(self) -> bool:
        """Returns True, if the log writer has been stopped and is not listening to messages anymore."""
        return self.__is_stopped

    def get_metadata(self, simulation_id: str) -> Union[SimulationMetadata, None]:
        """Returns the simulation metadata object corresponding to the given simulation identifier."""
        return self.__metadata_collection.get_simulation(simulation_id)

    async def simulation_message_handler(self, message_object: Union[BaseMessage, dict, str],
                                         message_routing_key: str):
        """Handles the received simulation messages."""
        # if message is a string see if it can be decoded as json
        if isinstance(message_object, str):
            try:
                message_json = json.loads(message_object)
                if isinstance(message_json, dict):
                    message_object = message_json

            except json.decoder.JSONDecodeError:
                # create invalid message object from the invalid json string
                LOGGER.debug("Received message could not be decoded into JSON format: {:s}".format(message_object))
                message_object = InvalidMessage(InvalidJsonMessage=message_object)

        # see if valid json is a a valid simulation platform message"
        if isinstance(message_object, dict):
            # use the GeneralMessage type when dealing with possible unknown message type
            actual_message_object = GeneralMessage.from_json(message_object)
            if actual_message_object is None:
                # invalid message
                LOGGER.debug("Could not create a valid message object from the received message: {:s}".format(
                    str(message_object)))
                # check if there is a valid timestamp
                timestamp = message_object.get("Timestamp", None)
                # if there is a valid timestamp it is used as the invalid message timestamp
                if timestamp is not None:
                    try:
                        to_utc_datetime_object(timestamp)

                    except ValueError:
                        # timestamp is not valid so it will be created from current time
                        # when the invalid message object is created
                        timestamp = None

                actual_message_object = InvalidMessage(Timestamp=timestamp, InvalidMessage=message_object)
            message_object = actual_message_object

        if isinstance(message_object, AbstractMessage):
            LOGGER.debug("{:s} : {:s} : {:s}".format(
                message_routing_key, message_object.simulation_id, message_object.message_id))
            await self.__metadata_collection.add_message(message_object, message_routing_key)

        elif isinstance(message_object, BaseMessage):
            if isinstance(message_object, InvalidMessage) and self.__default_simulation_id is None:
                LOGGER.warning("Unable to log an invalid message since default simulation id has not been given.")
                return

            # if message is invalid default simulation id is used
            simulation_id = (
                message_object.simulation_id if not isinstance(message_object, InvalidMessage)
                else self.__default_simulation_id
            )
            LOGGER.debug("{:s} : {:s}".format(message_routing_key, simulation_id))
            await self.__metadata_collection.add_message(message_object, message_routing_key, simulation_id)

        else:
            # this should not happen.
            LOGGER.warning("Received '{:s}' message when expecting for simulation platform compatible message".format(
                str(message_object)))


async def start_listener_component():
    """Start a listener component for the simulation platform."""
    message_listener = ListenerComponent()

    while not message_listener.is_stopped:
        # print out the statistics every two minutes
        await asyncio.sleep(STATISTICS_DISPLAY_INTERVAL)
        log_message = "\nSimulations listened:\n=====================\n"
        log_message += "\n".join([
            str(message_listener.get_metadata(simulation_id))
            for simulation_id in message_listener.simulations
        ])
        LOGGER.info(log_message)

    # short wait before exiting to allow all database writes to finish properly.
    await asyncio.sleep(STOP_WAIT_TIMER)


if __name__ == "__main__":
    asyncio.run(start_listener_component())
