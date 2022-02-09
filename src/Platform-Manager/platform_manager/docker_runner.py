# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains the functionality for starting Docker containers."""

import asyncio
import inspect
import re
from typing import cast, Dict, List, Optional, Union

from aiodocker import Docker
from aiodocker.exceptions import DockerError
from aiodocker.containers import DockerContainer
from aiohttp.client_exceptions import ClientError
from docker import from_env as docker_client_from_env, DockerClient
from docker.errors import APIError
from docker.models.containers import Container
from docker.models.networks import Network

from tools.tools import EnvironmentVariableValue, FullLogger, async_wrap

LOGGER = FullLogger(__name__)


def get_container_name(container: DockerContainer) -> str:
    """Returns the name of the given Docker container."""
    # Use a hack to get the container name because the aiodocker does not make it otherwise available.
    return container._container.get("Names", [" "])[0][1:]  # pylint: disable=protected-access


class ContainerConfiguration:
    """Class for holding the parameters needed when starting a Docker container instance.
    Only parameters needed for starting containers for the simulation platform are included.
    """
    def __init__(self, container_name: str, docker_image: str, environment: Dict[str, EnvironmentVariableValue],
                 networks: Union[str, List[str]], volumes: Union[str, List[str]]):
        """
        Sets up the parameters for the Docker container configuration to the format required by aiodocker.
        - container_name:    the container name
        - docker_image:      the Docker image name including a tag
        - environment:       the environment variables and their values
        - networks:          the names of the Docker networks for the container
        - volumes:           the volume names and the target paths, format: <volume_name>:<target_path>[rw|ro]
        """
        self.__name = container_name
        self.__image = docker_image
        self.__environment = [
            "=".join([
                variable_name, str(variable_value)
            ])
            for variable_name, variable_value in environment.items()
        ]

        if isinstance(networks, str):
            self.__networks = [networks]
        else:
            self.__networks = networks

        if isinstance(volumes, str):
            self.__volumes = [volumes]
        else:
            self.__volumes = volumes

    @property
    def container_name(self) -> str:
        """The container name."""
        return self.__name

    @property
    def image(self) -> str:
        """The Docker image for the container."""
        return self.__image

    @property
    def environment(self) -> List[str]:
        """The environment variables for the Docker container."""
        return self.__environment

    @property
    def networks(self) -> List[str]:
        """The Docker networks for the Docker container."""
        return self.__networks

    @property
    def volumes(self) -> List[str]:
        """The Docker volumes for the Docker container."""
        return self.__volumes


class ContainerStarter:
    """Class for starting the Docker components for a simulation."""
    PREFIX_DIGITS = 2
    PREFIX_START = "Sim"

    def __init__(self):
        """Sets up the Docker client."""
        self.__container_prefix = "{:s}{{index:0{:d}d}}_".format(
            self.__class__.PREFIX_START, self.__class__.PREFIX_DIGITS)     # Sim{index:02d}_
        self.__prefix_pattern = re.compile("{:s}([0-9]{{{:d}}})_".format(
            self.__class__.PREFIX_START, self.__class__.PREFIX_DIGITS))    # Sim([0-9]{2})_

        # the docker client using aiodocker library
        self.__docker_client = Docker()
        # the docker client using docker library, used only if necessary
        self.__docker_client_synchronous = None  # type: Optional[DockerClient]

        self.__lock = asyncio.Lock()

    async def close(self):
        """Closes the Docker client connection."""
        await self.__docker_client.close()

    async def get_next_simulation_index(self) -> Union[int, None]:
        """
        Returns the next available index for the container name prefix for a new simulation.
        If all possible indexes are already in use, returns None.
        """
        running_containers = cast(List[DockerContainer], await self.__docker_client.containers.list())
        simulation_indexes = {
            int(get_container_name(container)[len(self.__class__.PREFIX_START):][:self.__class__.PREFIX_DIGITS])
            for container in running_containers
            if self.__prefix_pattern.match(get_container_name(container)) is not None
        }

        if simulation_indexes:
            index_limit = 10 ** self.__class__.PREFIX_DIGITS
            available_indexes = set(range(index_limit)) - simulation_indexes
            if available_indexes:
                return min(available_indexes)
            # no available simulation indexes available
            return None

        # no previous simulation containers found
        return 0

    async def create_container(self, container_name: str, container_configuration: ContainerConfiguration) \
            -> Optional[Union[DockerContainer, Container]]:
        """
        Creates and returns a Docker container according to the given configuration.
        Uses the 'aiodocker' library by default and if that throws an exception, tries using the 'docker' library.
        """
        # The API specification for Docker Engine: https://docs.docker.com/engine/api/v1.40/
        LOGGER.debug("Creating container: {:s}".format(container_name))
        if container_configuration.networks:
            first_network_name = container_configuration.networks[0]
            first_network = {first_network_name: {}}
        else:
            first_network = {}

        try:
            container = await self.__docker_client.containers.create(
                name=container_name,
                config={
                    "Image": container_configuration.image,
                    "Env": container_configuration.environment,
                    "HostConfig": {
                        "Binds": container_configuration.volumes,
                        "AutoRemove": True
                    },
                    "NetworkingConfig": {
                        "EndpointsConfig": first_network
                    }
                }
            )
            if not isinstance(container, DockerContainer):
                LOGGER.warning("Failed to create container: {:s}".format(
                    container_configuration.container_name))
                return None

            # When creating a container, it can only be connected to one network.
            # The other networks have to be connected separately.
            for other_network_name in container_configuration.networks[1:]:
                other_network = await self.__docker_client.networks.get(net_specs=other_network_name)
                await other_network.connect(
                    config={
                        "Container": container_name,
                        "EndpointConfig": {}
                    }
                )

            return container

        except ClientError as client_error:
            LOGGER.warning("Received {}: {}".format(type(client_error).__name__, client_error))
            LOGGER.info("Trying the 'docker' library instead of 'aiodocker'")
            return await self._create_container_backup(container_name, container_configuration)

        except DockerError as docker_error:
            LOGGER.warning("Received {}: {}".format(type(docker_error).__name__, docker_error))
            return None

    async def _create_container_backup(self, container_name: str, container_configuration: ContainerConfiguration) \
            -> Optional[Container]:
        """
        Creates and returns a Docker container according to the given configuration.
        Uses the 'docker' library.
        """
        if not container_configuration.networks:
            first_network = None
        else:
            first_network = container_configuration.networks[0]

        try:
            if self.__docker_client_synchronous is None:
                self.__docker_client_synchronous = await async_wrap(docker_client_from_env)()
            container = await async_wrap(self.__docker_client_synchronous.containers.create)(
                name=container_name,
                image=container_configuration.image,
                environment=container_configuration.environment,
                volumes=container_configuration.volumes,
                network=first_network,
                auto_remove=True
            )
            if not isinstance(container, Container):
                LOGGER.warning("Failed to create container: {:s}".format(
                    container_configuration.container_name))
                return None

            other_networks = await async_wrap(self.__docker_client_synchronous.networks.list)(
                names=container_configuration.networks[1:]
            )
            for other_network in other_networks:
                if isinstance(other_network, Network):
                    await async_wrap(other_network.connect)(container)

            return container

        except APIError as docker_error:
            LOGGER.warning("Received {}: {}".format(type(docker_error).__name__, docker_error))
            return None

    async def start_simulation(self, simulation_configurations: List[ContainerConfiguration]) -> Union[List[str], None]:
        """
        Starts a Docker container with the given configuration parameters.
        Returns the names of the container objects representing the started containers.
        Returns None, if there was a problem starting any of the containers.
        """
        async with self.__lock:
            simulation_index = await self.get_next_simulation_index()
            if simulation_index is None:
                LOGGER.warning("No free simulation indexes. Wait until a simulation run has finished.")
                return None

            simulation_containers = []  # type: List[Union[DockerContainer, Container]]
            container_names = []        # type: List[str]
            for container_configuration in simulation_configurations:
                full_container_name = (
                    self.__container_prefix.format(index=simulation_index) +
                    container_configuration.container_name)
                container_names.append(full_container_name)

                new_container = await self.create_container(full_container_name, container_configuration)
                if new_container is None:
                    # clean the already created containers
                    LOGGER.warning("Removing containers that have been created.")

                    for container_name, created_container in zip(container_names, simulation_containers):
                        LOGGER.warning("Removing container: {}".format(container_name))
                        if isinstance(created_container, DockerContainer):
                            # remove container created with aiodocker library
                            await created_container.delete()
                        elif isinstance(created_container, Container):
                            # remove container created with docker library
                            await async_wrap(created_container.remove)()
                        else:
                            LOGGER.error("An unknown container type, {}, for container: {}".format(
                                type(created_container).__name__, container_name))

                    # return None to indicate that there was a problem in the container creation
                    return None

                # add the newly created container to the container list
                simulation_containers.append(new_container)

            # start the created containers
            for container_name, container in zip(container_names, simulation_containers):
                LOGGER.info("Starting container: {:s}".format(container_name))
                if inspect.iscoroutinefunction(container.start):
                    start_function = container.start
                else:
                    start_function = async_wrap(container.start)
                await start_function()

            return container_names

    async def stop_containers(self, container_names: List[str]):
        """Stops all the Docker containers in the given container name list."""
        # TODO: implement stop_containers

    async def stop_all_simulation_containers(self):
        """Stops all the Docker containers that have been started."""
        # TODO: implement stop_all_simulation_containers
