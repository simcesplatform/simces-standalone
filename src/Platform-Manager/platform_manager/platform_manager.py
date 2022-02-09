# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""
This module contains the Platform Manager code that handles the starting of the simulation components for
a simulation using the simulation platform.
"""

import asyncio
import json
from typing import Any, cast, Dict

from tools.clients import RabbitmqClient
from tools.tools import FullLogger, EnvironmentVariable

from platform_manager.docker_runner import ContainerStarter
from platform_manager.platform_environment import PlatformEnvironment
from platform_manager.simulation import load_simulation_parameters_from_yaml

LOGGER = FullLogger(__name__)

SIMULATION_CONFIGURATION_FILE = "SIMULATION_CONFIGURATION_FILE"
SIMULATION_START_MESSAGE_TOPIC = "SIMULATION_START_MESSAGE_TOPIC"


class PlatformManager:
    """PlatformManager handlers the starting of new simulations for the simulation platform."""
    def __init__(self):
        # Message bus client for sending messages to the management exchange.
        self.__rabbitmq_client = RabbitmqClient()

        # Load the environment variables.
        self.__platform_environment = PlatformEnvironment()

        # Open the Docker Engine connection.
        self.__container_starter = ContainerStarter()

        self.__start_topic = cast(str, EnvironmentVariable(SIMULATION_START_MESSAGE_TOPIC, str, "Start").value)
        self.__is_stopped = False

    @property
    def is_stopped(self) -> bool:
        """Returns True, if the platform manager is stopped."""
        return self.__is_stopped

    async def stop(self):
        """Closes the connections to the RabbitMQ client and to the Docker Engine."""
        LOGGER.info("Stopping the platform manager.")
        await self.__rabbitmq_client.close()
        await self.__container_starter.close()
        self.__is_stopped = True

    def register_component_type(self, component_type: str,
                                component_type_definition: Dict[str, Any]) -> bool:
        """Registers a new (or updates a registered) component type to the platform manager."""
        register_check = self.__platform_environment.register_component_type(
            component_type, component_type_definition)

        if register_check:
            LOGGER.info("Registered component type: '{}'".format(component_type))
        else:
            LOGGER.warning("Could not register component type: '{}'".format(component_type))
        return register_check

    async def start_simulation(self, simulation_configuration_file: str) -> bool:
        """Starts a new simulation using the given simulation configuration file."""
        if self.is_stopped:
            return False

        simulation_configuration = load_simulation_parameters_from_yaml(simulation_configuration_file)
        if simulation_configuration is None:
            LOGGER.error("Could not load the simulation configuration.")
            return False

        simulation_name = simulation_configuration.simulation.simulation_name
        simulation_id = simulation_configuration.simulation.simulation_id

        container_configuration = self.__platform_environment.get_container_configurations(simulation_configuration)
        if container_configuration is None:
            LOGGER.error("Could not create the Docker container configurations.")
            return False

        start_message = self.__platform_environment.get_start_message(simulation_configuration)
        if start_message is None:
            LOGGER.error("Could not create the Start message.")
            return False
        start_message_is_stored = self.__platform_environment.store_start_message(start_message)
        if not start_message_is_stored:
            LOGGER.warning("Could not save the Start message to a file.")

        LOGGER.info("Starting the Docker containers for simulation: '{:s}' with id: {:s}".format(
            simulation_name, simulation_id))
        container_names = await self.__container_starter.start_simulation(container_configuration)

        if container_names is None:
            LOGGER.error("A problem starting the simulation. Could not create the Docker containers.")
            return False

        start_message_bytes = bytes(json.dumps(start_message), encoding="UTF-8")
        await self.__rabbitmq_client.send_message(topic_name=self.__start_topic, message_bytes=start_message_bytes)
        LOGGER.info("Start message for simulation '{:s}' sent to management exchange.".format(simulation_name))

        # The container for the simulation manager should be the last one in the list.
        manager_container_name = container_names[-1]
        identifier_start_index = len(ContainerStarter.PREFIX_START)
        identifier_end_index = identifier_start_index + ContainerStarter.PREFIX_DIGITS
        simulation_identifier = manager_container_name[identifier_start_index:identifier_end_index]
        LOGGER.info("Simulation '{:s}' started successfully using id: {:s}".format(simulation_name, simulation_id))
        LOGGER.info("Follow the simulation by using the command:\n" +
                    "    source follow_simulation.sh {:s}".format(simulation_identifier))
        LOGGER.info("Alternatively, the simulation manager logs can by viewed by:\n" +
                    "    docker logs --follow {:s}".format(manager_container_name))
        LOGGER.info("Platform manager has finished starting the simulation and will now stop.")
        LOGGER.info("The simulation will continue to run on the background.")

        return True


async def start_platform_manager():
    """Starts the Platform manager process."""
    platform_manager = PlatformManager()

    configuration_filename = cast(str, EnvironmentVariable(SIMULATION_CONFIGURATION_FILE, str, "").value)
    start_check = await platform_manager.start_simulation(configuration_filename)
    if start_check:
        LOGGER.debug("A new simulation run started.")

    await platform_manager.stop()


if __name__ == "__main__":
    asyncio.run(start_platform_manager())
