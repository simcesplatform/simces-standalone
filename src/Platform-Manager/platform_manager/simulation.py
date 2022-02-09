# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""
This module contains data classes for storing the configuration for a single simulation run.
"""

import dataclasses
from typing import Any, Dict, Optional
import yaml

from tools.datetime_tools import get_utcnow_in_milliseconds, to_iso_format_datetime_string
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)

# The main attributes in simulation configuration file
SIMULATION = "Simulation"
COMPONENTS = "Components"

# The overall simulation attributes in the simulation configuration file
SIMULATION_NAME = "Name"
SIMULATION_DESCRIPTION = "Description"
SIMULATION_START_TIME = "InitialStartTime"
SIMULATION_EPOCH_LENGTH = "EpochLength"
SIMULATION_MAX_EPOCH_COUNT = "MaxEpochCount"

# The optional parameters for the simulation manager in the simulation configuration file
SIMULATION_MANAGER_NAME = "ManagerName"
SIMULATION_EPOCH_TIMER_INTERVAL = "EpochTimerInterval"
SIMULATION_MAX_EPOCH_RESEND_COUNT = "MaxEpochResendCount"

# The optional parameters for the log writer in the simulation configuration file
MESSAGE_BUFFER_MAX_DOCUMENTS = "MessageBufferMaxDocumentCount"
MESSAGE_BUFFER_MAX_INTERVAL = "MessageBufferMaxInterval"

# The attribute names for simulation name and description for the simulation manager
SIMULATION_NAME_FOR_MANAGER = "SimulationName"
SIMULATION_DESCRIPTION_FOR_MANAGER = "SimulationDescription"

# The special attribute that can be used to create multiple identical components for the simulation
DUPLICATION_COUNT = "duplication_count"

DUPLICATE_CONTAINER_NAME_SEPARATOR = "_"


def remove_nones(dictionary: dict) -> dict:
    """remove_nones"""
    return {
        dictionary_key: key_value
        for dictionary_key, key_value in dictionary.items()
        if key_value is not None
    }


@dataclasses.dataclass
class SimulationComponentConfiguration:
    """
    Data class for holding the parameters for one (either dynamic or static) component.
    - duplication_count: how many identical duplicates will be participating in the simulation run, default is 1
    - attributes: a dictionary containing the attribute names and values for the component
    """
    duplication_count: int = 1
    attributes: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class SimulationComponentTypeConfiguration:
    """
    Data class for holding the names and parameters for the processes of one type of component
    participating in the simulation run.
    - processes: a dictionary containing the parameters for the participating processes
    """
    processes: Dict[str, SimulationComponentConfiguration] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class SimulationGeneralConfiguration:
    """
    Data class for holding the general parameters, simulation name, epoch length, etc., for a simulation run.
    - simulation_id: the id for the simulation run
    - manager_configuration: the parameter configuration for the simulation manager
    - logwriter_configuration: the parameter configuration for the log writer
    - simulation_name: the name of the simulation
    - description: a descripton for the simulation
    """
    simulation_id: str
    manager_configuration: SimulationComponentConfiguration
    logwriter_configuration: SimulationComponentConfiguration
    simulation_name: str = "simulation"
    description: str = ""


@dataclasses.dataclass
class SimulationConfiguration:
    """
    Data class for holding the configuration for a single simulation run.
    - simulation: the general specification parameters for the simulation run
    - components: a dictionary containing the parameters for all the participating components
    """
    simulation: SimulationGeneralConfiguration
    components: Dict[str, SimulationComponentTypeConfiguration] = dataclasses.field(default_factory=dict)


def load_simulation_parameters_from_yaml(yaml_filename: str) -> Optional[SimulationConfiguration]:
    """
    Loads and returns the simulation run specification from a YAML file.
    Returns None, if there is a problem loading the simulation parameters.
    """
    try:
        with open(yaml_filename, mode="r", encoding="UTF-8") as yaml_file:
            yaml_configuration = yaml.safe_load(yaml_file)

        # load the component specific parameters for the simulation run
        component_configurations = {
            component_type: SimulationComponentTypeConfiguration(
                processes={
                    component_name: SimulationComponentConfiguration(
                        duplication_count=(
                            1 if component_attributes is None
                            else component_attributes.get(DUPLICATION_COUNT, 1)
                        ),
                        attributes={
                            attribute_name: attribute_value
                            for attribute_name, attribute_value in (
                                {}.items() if component_attributes is None
                                else component_attributes.items()
                            )
                            if attribute_name != DUPLICATION_COUNT
                        }
                    )
                    for component_name, component_attributes in (
                        {}.items() if component_type_processes is None
                        else component_type_processes.items()
                    )
                }
            )
            for component_type, component_type_processes in yaml_configuration.get(COMPONENTS, {}).items()
        }

        # load the simulation manager parameters for the simulation run
        simulation_configuration = yaml_configuration.get(SIMULATION, {})

        manager_attributes = {
            SIMULATION_START_TIME: to_iso_format_datetime_string(
                simulation_configuration.get(SIMULATION_START_TIME, None)),
            SIMULATION_EPOCH_LENGTH: simulation_configuration.get(SIMULATION_EPOCH_LENGTH, None),
            SIMULATION_MAX_EPOCH_COUNT: simulation_configuration.get(SIMULATION_MAX_EPOCH_COUNT, None),
            SIMULATION_MANAGER_NAME: simulation_configuration.get(SIMULATION_MANAGER_NAME, None),
            SIMULATION_EPOCH_TIMER_INTERVAL: simulation_configuration.get(SIMULATION_EPOCH_TIMER_INTERVAL, None),
            SIMULATION_MAX_EPOCH_RESEND_COUNT: simulation_configuration.get(SIMULATION_MAX_EPOCH_RESEND_COUNT, None),
            SIMULATION_NAME_FOR_MANAGER: simulation_configuration.get(SIMULATION_NAME, None),
            SIMULATION_DESCRIPTION_FOR_MANAGER: simulation_configuration.get(SIMULATION_DESCRIPTION, None),
            COMPONENTS: [
                component_name if component_configuration.duplication_count == 1
                else DUPLICATE_CONTAINER_NAME_SEPARATOR.join([component_name, str(index)])
                for _, processes in component_configurations.items()
                for component_name, component_configuration in processes.processes.items()
                for index in range(1, component_configuration.duplication_count + 1)
            ]
        }

        # load the log writer parameters for the simulation run
        log_writer_attributes = {
            MESSAGE_BUFFER_MAX_DOCUMENTS: simulation_configuration.get(MESSAGE_BUFFER_MAX_DOCUMENTS, None),
            MESSAGE_BUFFER_MAX_INTERVAL: simulation_configuration.get(MESSAGE_BUFFER_MAX_INTERVAL, None)
        }

        # collect all the general simulation parameters
        general_configuration = SimulationGeneralConfiguration(
            simulation_id=get_utcnow_in_milliseconds(),
            manager_configuration=SimulationComponentConfiguration(attributes=remove_nones(manager_attributes)),
            logwriter_configuration=SimulationComponentConfiguration(attributes=remove_nones(log_writer_attributes))
        )
        if SIMULATION_NAME in simulation_configuration:
            general_configuration.simulation_name = simulation_configuration[SIMULATION_NAME]
        if SIMULATION_DESCRIPTION in simulation_configuration:
            general_configuration.description = simulation_configuration[SIMULATION_DESCRIPTION]

        return SimulationConfiguration(
            simulation=general_configuration,
            components=component_configurations
        )

    except (OSError, KeyError, yaml.YAMLError) as yaml_error:
        LOGGER.error("Encountered '{}' exception when loading simulation run specification from '{}': {}".format(
            type(yaml_error).__name__, yaml_filename, yaml_error
        ))
        return None
