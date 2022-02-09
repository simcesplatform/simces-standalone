# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains the Platform Manager code that handles the starting of the simulation components for
   a simulation using the simulation platform.
"""

import logging
import json
import pathlib
from typing import Any, cast, Dict, List, Optional

from tools.clients import default_env_variable_definitions as default_rabbitmq_definitions
from tools.components import (
    SIMULATION_COMPONENT_NAME, SIMULATION_ID, SIMULATION_STATE_MESSAGE_TOPIC,
    SIMULATION_EPOCH_MESSAGE_TOPIC, SIMULATION_STATUS_MESSAGE_TOPIC, SIMULATION_ERROR_MESSAGE_TOPIC,
    SIMULATION_START_MESSAGE_FILENAME)
from tools.db_clients import default_env_variable_definitions as default_mongodb_definitions
from tools.datetime_tools import get_utcnow_in_milliseconds
from tools.tools import (
    FullLogger, load_environmental_variables, EnvironmentVariable, EnvironmentVariableValue,
    SIMULATION_LOG_LEVEL, SIMULATION_LOG_FILE, SIMULATION_LOG_FORMAT, DEFAULT_LOGFILE_NAME, DEFAULT_LOGFILE_FORMAT)

from platform_manager.component import (
    EXTERNAL_COMPONENT_TYPE, ComponentParameters, ComponentCollectionParameters,
    get_component_type_parameters, load_component_parameters_from_yaml,
    COMPONENT_TYPE_SIMULATION_MANAGER, COMPONENT_TYPE_LOG_WRITER)
from platform_manager.docker_runner import ContainerConfiguration
from platform_manager.simulation import (
    SimulationConfiguration, SimulationComponentConfiguration,
    DUPLICATE_CONTAINER_NAME_SEPARATOR, SIMULATION_MANAGER_NAME)

LOGGER = FullLogger(__name__)

TIMEOUT = 5.0
MANIFEST_FILE_EXTENSIONS = (".yml", ".yaml")

# The files in each folder under the manifest folder is gone through in an unspecified order.
# Only the first specification for each component type is taken into account.
# The files in the root manifest folder are given top priority.
# The second highest priority is given to files under the folder defined by MANIFEST_FOLDER_WITH_PRIORITY.
# All other subfolders are gone through in an unspecified order.
MANIFEST_FOLDER_WITH_PRIORITY = "local"

# Names for environmental variables for the platform manager
RABBITMQ_EXCHANGE = "RABBITMQ_EXCHANGE"
RABBITMQ_EXCHANGE_AUTODELETE = "RABBITMQ_EXCHANGE_AUTODELETE"
RABBITMQ_EXCHANGE_DURABLE = "RABBITMQ_EXCHANGE_DURABLE"
RABBITMQ_EXCHANGE_PREFIX = "RABBITMQ_EXCHANGE_PREFIX"
MONGODB_APPNAME = "MONGODB_APPNAME"

MANIFEST_FOLDER = "MANIFEST_FOLDER"
START_MESSAGE_FOLDER = "START_MESSAGE_FOLDER"

DOCKER_NETWORK_MONGODB = "DOCKER_NETWORK_MONGODB"
DOCKER_NETWORK_RABBITMQ = "DOCKER_NETWORK_RABBITMQ"
DOCKER_NETWORK_PLATFORM = "DOCKER_NETWORK_PLATFORM"
DOCKER_VOLUME_NAME_RESOURCES = "DOCKER_VOLUME_NAME_RESOURCES"
DOCKER_VOLUME_NAME_LOGS = "DOCKER_VOLUME_NAME_LOGS"
DOCKER_VOLUME_TARGET_RESOURCES = "DOCKER_VOLUME_TARGET_RESOURCES"
DOCKER_VOLUME_TARGET_LOGS = "DOCKER_VOLUME_TARGET_LOGS"

# Attribute names for the simulation configuration file
START = "Start"
START_MESSAGE_TYPE = "Type"
START_MESSAGE_TIMESTAMP = "Timestamp"
START_MESSAGE_SIMULATION_ID = "SimulationId"
START_MESSAGE_SIMULATION_SPECIFIC_EXCHANGE = "SimulationSpecificExchange"
START_MESSAGE_NAME = "SimulationName"
START_MESSAGE_DESCRIPTION = "SimulationDescription"
START_MESSAGE_PROCESS_PARAMETERS = "ProcessParameters"

# The filename for a stored Start message
START_MESSAGE_FILENAME_TEMPLATE = "start_message_{simulation_exchange:}.json"


# This helper function is a copy from fetch/fetch.py
def create_folder(target_folder: pathlib.Path):
    """Creates the target folder if it does not exist yet."""
    try:
        if target_folder.exists():
            if not target_folder.is_dir():
                LOGGER.warning("'{}' is not a directory".format(target_folder))
            return

        resolved_target = target_folder.resolve()
        if resolved_target.parent != resolved_target and not resolved_target.parent.is_dir():
            create_folder(resolved_target.parent)
        resolved_target.mkdir()
        # change the permission to allow read-write access to the folder for all users
        resolved_target.chmod(0o777)

    except OSError as os_error:
        LOGGER.error("Received '{}' while creating folder '{}': {}".format(
            type(os_error).__name__, target_folder, os_error
        ))


class PlatformEnvironment:
    """Class for holding the values for non-simulation specific environment variables."""
    def __init__(self):
        """Loads the environmental variables that are used in the simulation components."""
        # TODO: add some checks for the parameters

        # setup the RabbitMQ parameters for the simulation specific exchange
        rabbitmq_env_variables = load_environmental_variables(*default_rabbitmq_definitions())
        # the exchange name is decided when starting a new simulation
        rabbitmq_env_variables.pop(RABBITMQ_EXCHANGE, None)
        self.__rabbitmq = {
            **rabbitmq_env_variables,
            RABBITMQ_EXCHANGE_AUTODELETE: True,
            RABBITMQ_EXCHANGE_DURABLE: False
        }
        self.__rabbitmq_exchange_prefix = cast(
            str, EnvironmentVariable(RABBITMQ_EXCHANGE_PREFIX, str, "procem.").value)

        # setup the MongoDB parameters for components needing database access
        self.__mongodb = load_environmental_variables(*default_mongodb_definitions())

        # setup the common parameters used by all simulation components
        self.__common = load_environmental_variables(
            (SIMULATION_LOG_LEVEL, int, logging.DEBUG),
            (SIMULATION_LOG_FILE, str, DEFAULT_LOGFILE_NAME),
            (SIMULATION_LOG_FORMAT, str, DEFAULT_LOGFILE_FORMAT),
            (SIMULATION_STATE_MESSAGE_TOPIC, str, "SimState"),
            (SIMULATION_EPOCH_MESSAGE_TOPIC, str, "Epoch"),
            (SIMULATION_STATUS_MESSAGE_TOPIC, str, "Status.Ready"),
            (SIMULATION_ERROR_MESSAGE_TOPIC, str, "Status.Error")
        )

        # load the component type definitions from the component manifest files
        self.__supported_component_types = ComponentCollectionParameters()
        self.__manifest_folder = pathlib.Path(cast(str, EnvironmentVariable(MANIFEST_FOLDER, str, "/manifests").value))
        self.__read_manifest_folder(self.__manifest_folder)

        self.__start_message_folder = pathlib.Path(
            cast(str, EnvironmentVariable(START_MESSAGE_FOLDER, str, "/logs/start").value)
        )
        create_folder(self.__start_message_folder)

        # load the Docker network and volume related variables
        self.__docker = load_environmental_variables(
            (DOCKER_NETWORK_MONGODB, str),
            (DOCKER_NETWORK_RABBITMQ, str),
            (DOCKER_NETWORK_PLATFORM, str, ""),
            (DOCKER_VOLUME_NAME_RESOURCES, str),
            (DOCKER_VOLUME_NAME_LOGS, str),
            (DOCKER_VOLUME_TARGET_RESOURCES, str, ""),
            (DOCKER_VOLUME_TARGET_LOGS, str, "")
        )

    def get_rabbitmq_parameters(self, simulation_id: str) -> Dict[str, EnvironmentVariableValue]:
        """The simulation specific parameters for a RabbitMQ connection."""
        return {
            **self.__rabbitmq,
            RABBITMQ_EXCHANGE: self.get_simulation_exchange_name(simulation_id)
        }

    def get_simulation_exchange_name(self, simulation_id: str) -> str:
        """Returns the name for the simulation specific exchange."""
        return (
            self.__rabbitmq_exchange_prefix +
            simulation_id.replace("-", "").replace(":", "").replace("Z", "").replace("T", "-").replace(".", "-")
        )

    def get_component_log_filename(self, component_name: str) -> str:
        """Returns the log filename for the given component."""
        filename_addition = "_" + component_name
        main_log_filename = cast(str, self.__common[SIMULATION_LOG_FILE])
        identifier_start = main_log_filename.rfind(".")

        if identifier_start == -1:
            return main_log_filename + filename_addition
        return main_log_filename[:identifier_start] + filename_addition + main_log_filename[identifier_start:]

    def get_docker_networks(self, rabbitmq: bool = True, mongodb: bool = False) -> List[str]:
        """Returns the names of the asked Docker networks."""
        docker_networks = [cast(str, self.__docker[DOCKER_NETWORK_PLATFORM])]
        if rabbitmq and self.__docker[DOCKER_NETWORK_RABBITMQ]:
            docker_networks.append(cast(str, self.__docker[DOCKER_NETWORK_RABBITMQ]))
        if mongodb and self.__docker[DOCKER_NETWORK_MONGODB]:
            docker_networks.append(cast(str, self.__docker[DOCKER_NETWORK_MONGODB]))
        return docker_networks

    def get_docker_volumes(self, resources: bool = True, logs: bool = True) -> List[str]:
        """
        Returns the binding of the Docker volumes.
        Resources volume is used for static files and logs volume is used for log output.
        The format for the binding values are: <volume_name>:<folder_name>[:<rw|ro>]
        """
        docker_volumes = []
        if resources and self.__docker[DOCKER_VOLUME_NAME_RESOURCES]:
            docker_volumes.append(":".join([
                cast(str, self.__docker[DOCKER_VOLUME_NAME_RESOURCES]),
                cast(str, self.__docker[DOCKER_VOLUME_TARGET_RESOURCES])
            ]))
        if logs and self.__docker[DOCKER_VOLUME_NAME_LOGS]:
            docker_volumes.append(":".join([
                cast(str, self.__docker[DOCKER_VOLUME_NAME_LOGS]),
                cast(str, self.__docker[DOCKER_VOLUME_TARGET_LOGS])
            ]))
        return docker_volumes

    def get_start_message_variables(self, component_type: str, component_attributes: SimulationComponentConfiguration) \
            -> Optional[Dict[str, Any]]:
        """Returns the process parameter block for the Start message for the given component type."""
        component_type_parameters = self.__supported_component_types.component_types.get(component_type, None)
        if component_type_parameters is None:
            LOGGER.warning("Component type '{}' is not supported".format(component_type))
            return None

        variables = {}
        # go through all the attributes found in the simulation run specification
        for attribute_name, attribute_value in component_attributes.attributes.items():
            if (attribute_name not in component_type_parameters.attributes or
                    component_type_parameters.attributes[attribute_name].include_in_start):
                variables[attribute_name] = attribute_value

        # go through all the attributes registered for the component type
        for attribute_name, attribute_settings in component_type_parameters.attributes.items():
            if attribute_settings.include_in_start and attribute_name not in component_attributes.attributes:
                if attribute_settings.optional and attribute_settings.default is not None:
                    variables[attribute_name] = attribute_settings.default
                elif attribute_settings.optional:
                    LOGGER.warning(
                        "Optional attribute '{}' for component '{}' ".format(attribute_name, component_type) +
                        " does not have a default value and it is not set")
                else:
                    LOGGER.warning("Required attribute '{}' not given for component type '{}'".format(
                        attribute_name, component_type
                    ))
                    return None

        return variables

    def get_base_env_variables(self, component_parameters: ComponentParameters, simulation_id: str,
                               component_name: str) -> Dict[str, EnvironmentVariableValue]:
        """Returns the environment variables for a normal simulation component with the given component name.
           Does not include the parameters set in the simulation configuration file."""
        env_variables = {}
        if component_parameters.include_rabbitmq_parameters:
            env_variables = self.get_rabbitmq_parameters(simulation_id)
        if component_parameters.include_mongodb_parameters:
            env_variables = {**env_variables, **self.__mongodb}
        if component_parameters.include_general_parameters:
            env_variables = {
                **env_variables,
                **self.__common,
                SIMULATION_ID: simulation_id,
                SIMULATION_COMPONENT_NAME: component_name,
                SIMULATION_LOG_FILE: self.get_component_log_filename(component_name),
                SIMULATION_START_MESSAGE_FILENAME: str(self.get_start_message_filename(
                    self.get_simulation_exchange_name(simulation_id)))
            }
        return env_variables  # type: ignore

    def get_environmental_variables(self, component_type: str, simulation_id: str, component_name: str,
                                    component_attributes: SimulationComponentConfiguration) \
            -> Optional[Dict[str, EnvironmentVariableValue]]:
        """Returns the environment variables for a simulation component."""
        component_type_parameters = self.__supported_component_types.component_types.get(component_type, None)
        if component_type_parameters is None:
            LOGGER.warning("Component type '{}' is not supported".format(component_type))
            return None

        # set the base environment variables (RabbitMQ, simulation id, component name, etc.)
        env_variables = self.get_base_env_variables(component_type_parameters, simulation_id, component_name)

        # go through all the attributes found in the simulation run specification
        for attribute_name, attribute_value in component_attributes.attributes.items():
            if attribute_name in component_type_parameters.attributes:
                env_variable_name = component_type_parameters.attributes[attribute_name].environment
                if env_variable_name is None:
                    env_variable_name = attribute_name
            else:
                env_variable_name = attribute_name

            # if the attribute value is a list, concatenate the items to a string using comma as a separator
            if isinstance(attribute_value, list):
                attribute_value = ",".join([str(attribute_item) for attribute_item in attribute_value])

            env_variables[env_variable_name] = attribute_value

        # go through all the attributes registered for the component type
        for attribute_name, attribute_settings in component_type_parameters.attributes.items():
            if attribute_name not in component_attributes.attributes:
                if attribute_settings.optional and attribute_settings.default is not None:
                    env_variable_name = attribute_settings.environment
                    if env_variable_name is None:
                        env_variable_name = attribute_name
                    env_variables[env_variable_name] = attribute_settings.default

                elif attribute_settings.optional:
                    LOGGER.warning(
                        "Optional attribute '{}' for component '{}' ".format(attribute_name, component_type) +
                        " does not have a default value and it is not set")
                else:
                    LOGGER.warning("Required attribute '{}' not given for component type '{}'".format(
                        attribute_name, component_type
                    ))
                    return None

        return env_variables

    def get_container_configurations(self, simulation_configuration: SimulationConfiguration) -> \
            Optional[List[ContainerConfiguration]]:
        """Returns a list containing the Docker container configurations for a new simulation run."""
        container_configurations = []

        for component_type in ([COMPONENT_TYPE_LOG_WRITER] +
                               list(simulation_configuration.components) +
                               [COMPONENT_TYPE_SIMULATION_MANAGER]):
            if component_type not in self.__supported_component_types.component_types:
                LOGGER.error("Encountered unsupported component type: {}".format(component_type))
                return None

            component_type_settings = self.__supported_component_types.component_types[component_type]
            if component_type_settings.component_type == EXTERNAL_COMPONENT_TYPE:
                # No Docker containers are created for static components
                continue

            component_instance_dictionary = self.__get_component_processes(component_type, simulation_configuration)
            if component_instance_dictionary is None:
                LOGGER.error("Encountered unknown core component type: {}".format(component_type))
                return None

            # Go through each instance for each of the dynamic component type.
            for component_name, component_configuration in component_instance_dictionary.items():
                for index in range(1, component_configuration.duplication_count + 1):
                    if component_configuration.duplication_count == 1:
                        full_component_name = component_name
                    else:
                        full_component_name = DUPLICATE_CONTAINER_NAME_SEPARATOR.join([component_name, str(index)])

                    # Create a dictionary of the environmental variables for this current component instance.
                    environment_variables = self.get_environmental_variables(
                        component_type=component_type,
                        component_attributes=component_configuration,
                        simulation_id=simulation_configuration.simulation.simulation_id,
                        component_name=full_component_name
                    )
                    if environment_variables is None:
                        LOGGER.error("Could not create full list of environment variables for '{}'".format(
                            full_component_name))
                        return None

                    container_configurations.append(
                        ContainerConfiguration(
                            container_name=full_component_name,
                            docker_image=(
                                "unknown" if component_type_settings.docker_image is None
                                else component_type_settings.docker_image.full_name
                            ),
                            environment=environment_variables,
                            networks=self.get_docker_networks(
                                rabbitmq=component_type_settings.include_rabbitmq_parameters,
                                mongodb=component_type_settings.include_mongodb_parameters
                            ),
                            volumes=self.get_docker_volumes(
                                resources=component_name not in (
                                    COMPONENT_TYPE_SIMULATION_MANAGER, COMPONENT_TYPE_LOG_WRITER)
                            )
                        )
                    )

        return container_configurations

    def get_start_message(self, simulation_configuration: SimulationConfiguration) -> Optional[Dict[str, Any]]:
        """Returns a Start message corresponding to the given configuration for a simulation run."""
        simulation_id = simulation_configuration.simulation.simulation_id

        # The general part of the Start message including the parameters for simulation manager and log writer
        start_message = {
            START_MESSAGE_TYPE: START,
            START_MESSAGE_TIMESTAMP: get_utcnow_in_milliseconds(),
            START_MESSAGE_SIMULATION_ID: simulation_id,
            START_MESSAGE_SIMULATION_SPECIFIC_EXCHANGE: self.get_simulation_exchange_name(simulation_id),
            START_MESSAGE_NAME: simulation_configuration.simulation.simulation_name,
            START_MESSAGE_DESCRIPTION: simulation_configuration.simulation.description,
            START_MESSAGE_PROCESS_PARAMETERS:
            {
                COMPONENT_TYPE_SIMULATION_MANAGER: self.get_start_message_variables(
                    component_type=COMPONENT_TYPE_SIMULATION_MANAGER,
                    component_attributes=simulation_configuration.simulation.manager_configuration
                ),
                COMPONENT_TYPE_LOG_WRITER: self.get_start_message_variables(
                    component_type=COMPONENT_TYPE_LOG_WRITER,
                    component_attributes=simulation_configuration.simulation.logwriter_configuration
                )
            }
        }

        for component_type, component_instances in simulation_configuration.components.items():
            if component_type not in self.__supported_component_types.component_types:
                LOGGER.error("Encountered unsupported component type: {}".format(component_type))
                return None

            # add new process parameter block to the Start message
            start_message[START_MESSAGE_PROCESS_PARAMETERS][component_type] = {}
            start_message_component_type = start_message[START_MESSAGE_PROCESS_PARAMETERS][component_type]

            for process_name, process_parameters in component_instances.processes.items():
                for index in range(1, process_parameters.duplication_count + 1):
                    if process_parameters.duplication_count == 1:
                        full_process_name = process_name
                    else:
                        full_process_name = DUPLICATE_CONTAINER_NAME_SEPARATOR.join([process_name, str(index)])

                    start_message_component_type[full_process_name] = self.get_start_message_variables(
                        component_type=component_type,
                        component_attributes=process_parameters
                    )

        return start_message

    def store_start_message(self, start_message: Dict[str, Any]) -> bool:
        """Stores the given Start message to a file."""
        try:
            # at this point it is assumed that the target folder exists and is writable
            # also, it is assumed that the given message is a valid Start message
            simulation_exchange = start_message.get(START_MESSAGE_SIMULATION_SPECIFIC_EXCHANGE, None)
            if not isinstance(simulation_exchange, str):
                LOGGER.error("No simulation specific exchange found in the Start message")
                return False

            start_message_str = json.dumps(start_message, indent=4)
            full_filename = self.get_start_message_filename(cast(str, simulation_exchange))
            with open(full_filename, mode="w", encoding="UTF-8") as start_message_file:
                start_message_file.write(start_message_str + "\n")

            return True

        except (OSError, TypeError, OverflowError, ValueError) as error:
            LOGGER.error("Exception '{}' when trying to save the Start message to file: {}".format(
                type(error).__name__, error))
            return False

    def register_component_type(self, component_type: str, component_type_definition: Dict[str, Any],
                                replace: bool = True) -> bool:
        """Registers a new (or updates a registered) component type to the platform environment."""
        if component_type in (COMPONENT_TYPE_SIMULATION_MANAGER, COMPONENT_TYPE_LOG_WRITER):
            LOGGER.warning("Changing component type '{}' is not allowed.".format(component_type))
            return False

        component_type_parameters = get_component_type_parameters(component_type_definition)
        if component_type_parameters is None:
            LOGGER.warning("Could not register component type: {}".format(component_type))
            return False

        check = self.__supported_component_types.add_type(component_type, component_type_parameters, replace)
        return check

    def get_start_message_filename(self, simulation_exchange: str) -> pathlib.Path:
        """Returns the full filename where the JSON formatted Start message will be stored."""
        simple_filename = pathlib.Path(START_MESSAGE_FILENAME_TEMPLATE.format(simulation_exchange=simulation_exchange))
        return self.__start_message_folder / simple_filename

    def __read_manifest_folder(self, manifest_folder: pathlib.Path):
        """
        Iterates through the given folder and parses all found files and
        adds the defined components to the list of supported component types.
        """
        try:
            subfolders = []  # List[Path]
            priority_folder = None  # Optional[Path]
            for manifest_file in manifest_folder.iterdir():
                if manifest_file.is_dir():
                    # iterate through the files in the current folder before any subfolders
                    if manifest_file.parts and manifest_file.parts[-1] == MANIFEST_FOLDER_WITH_PRIORITY:
                        priority_folder = manifest_file
                    else:
                        subfolders.append(manifest_file)

                elif manifest_file.is_file() and manifest_file.suffix in MANIFEST_FILE_EXTENSIONS:
                    component_definition = load_component_parameters_from_yaml(manifest_file)
                    if component_definition is not None:
                        add_check = self.__supported_component_types.add_type(*component_definition, False)
                        if add_check:
                            LOGGER.info("Added component type '{}' to supported components".format(
                                component_definition[0]))
                            LOGGER.debug("Component '{}' definition: {}".format(*component_definition))
                        else:
                            LOGGER.info("Component type '{}' was already registered.".format(component_definition[0]))
                    else:
                        LOGGER.warning("No component definition could be parsed from '{}'".format(manifest_file))

            # iterate through the subfolder with priority name before any other subfolders
            if priority_folder:
                self.__read_manifest_folder(priority_folder)
            for subfolder in subfolders:
                self.__read_manifest_folder(subfolder)

        except OSError as file_error:
            LOGGER.error("Exception '{}' when trying to read manifest folder '{}': {}".format(
                type(file_error).__name__, manifest_folder, file_error))

    def __get_component_processes(self, component_type: str, simulation_configuration: SimulationConfiguration) \
            -> Optional[Dict[str, SimulationComponentConfiguration]]:
        """
        Returns a dictionary containing the configuration for the processes for the given component type.

        Core components can have only instance of each type while the other dynamic components can have multiple
        instances in the same simulation run. Gathers the component names and configurations first to allow
        uniform creation for the container configuration for both core and domain components.
        """
        component_type_settings = self.__supported_component_types.component_types[component_type]
        if component_type in (COMPONENT_TYPE_SIMULATION_MANAGER, COMPONENT_TYPE_LOG_WRITER):
            if component_type == COMPONENT_TYPE_SIMULATION_MANAGER:
                # setup the simulation manager name and the configuration
                component_configuration = simulation_configuration.simulation.manager_configuration
                if SIMULATION_MANAGER_NAME in component_configuration.attributes:
                    component_name = cast(str, component_configuration.attributes[SIMULATION_MANAGER_NAME])
                else:
                    component_name = cast(str, component_type_settings.attributes[SIMULATION_MANAGER_NAME].default)

            elif component_type == COMPONENT_TYPE_LOG_WRITER:
                # setup the log writer name and the configuration
                component_configuration = simulation_configuration.simulation.logwriter_configuration
                component_name = cast(str, self.__mongodb[MONGODB_APPNAME])

            else:
                LOGGER.error("Encountered unknown core component type: {}".format(component_type))
                return None

            component_instance_dictionary = {component_name: component_configuration}

        else:
            component_instance_dictionary = simulation_configuration.components[component_type].processes

        return component_instance_dictionary
