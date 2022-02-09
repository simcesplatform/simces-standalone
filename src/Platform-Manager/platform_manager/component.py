# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""
This module contains data classes for storing information about the components that the Platform Manager supports.
"""

from __future__ import annotations
import dataclasses
import pathlib
from typing import Any, Dict, Optional, Tuple, Union

import yaml

from tools.tools import FullLogger

LOGGER = FullLogger(__name__)

PLATFORM_COMPONENT_TYPE = "platform"  # a component managed by the platform, deployed using Docker
EXTERNAL_COMPONENT_TYPE = "external"  # an externally managed component
ALLOWED_COMPONENT_TYPES = [PLATFORM_COMPONENT_TYPE, EXTERNAL_COMPONENT_TYPE]

COMPONENT_TYPE_SIMULATION_MANAGER = "SimulationManager"
COMPONENT_TYPE_LOG_WRITER = "LogWriter"

PARAMETER_COMPONENT_NAME = "Name"
PARAMETER_COMPONENT_TYPE = "Type"
PARAMETER_DESCRIPTION = "Description"
PARAMETER_DOCKER_IMAGE = "DockerImage"
PARAMETER_ATTRIBUTES = "Attributes"

ATTRIBUTE_ENVIRONMENT = "Environment"
ATTRIBUTE_OPTIONAL = "Optional"
ATTRIBUTE_DEFAULT = "Default"
ATTRIBUTE_INCLUDE_IN_START = "IncludeInStart"


@dataclasses.dataclass
class ImageName:
    """Dataclass for holding Docker image name including the tag part."""
    image_name: str
    image_tag: str = "latest"

    @property
    def full_name(self) -> str:
        """The full Docker image name including the tag."""
        return ":".join([self.image_name, self.image_tag])


@dataclasses.dataclass
class ComponentAttribute:
    """
    Data class for holding information about an attribute for a component type.
    - environment: a string corresponding to the environmental variable name for the attribute,
                   should be None for an attribute for a static component
    - optional: a boolean value telling whether the attribute is optional or not
    - default: a number, string or a boolean value representing the default value for the attribute,
               all optional attributes should have a default value
    - include_in_start: a boolean value telling whether to include this attribute in the Start message
    """
    environment: Optional[str] = None
    optional: bool = False
    default: Optional[Union[int, float, bool, str]] = None
    include_in_start: bool = True


@dataclasses.dataclass
class ComponentParameters:
    """
    Data class for holding information about the parameters for a simulation component.
    - component_type: the general deployment type of the component, either "core", "dynamic" or "static"
    - description: a description for the component type
    - docker_image: a string representing the Docker image to be used with the component type,
                    should be None for a static component type
    - attributes: a dictionary containing the information about the input parameters for the component type,
                  any attribute not listed here is assumed to be optional and the corresponding environmental
                  variable name for an omitted attribute is assumed to be the same as the attribute name given
                  in the simulation configuration
    - include_rabbitmq_parameters: whether to pass the RabbitMQ connection parameters for a dynamic component
    - include_mongodb_parameters: whether to pass the MongoDB connection parameters for a dynamic component
    - include_general_parameters: whether to pass the general environmental variables for a dynamic component,
                                  this should be True for any component inherited from AbstractSimulationComponent,
                                  these include simulation id, component name and the logging level
    """
    component_type: str
    description: str = ""
    docker_image: Optional[ImageName] = None
    attributes: Dict[str, ComponentAttribute] = dataclasses.field(default_factory=dict)
    include_rabbitmq_parameters: bool = True
    include_mongodb_parameters: bool = False
    include_general_parameters: bool = True


@dataclasses.dataclass
class ComponentCollectionParameters:
    """
    Data class for holding information about the supported component types and their parameters.
    - component_types: a dictionary containing information about each of the supported component types
    """
    component_types: Dict[str, ComponentParameters] = dataclasses.field(default_factory=dict)

    def add_type(self, component_type: str, component_parameters: ComponentParameters, replace: bool = True) -> bool:
        """Combines the given component parameters to the current collection."""
        if not replace and component_type in self.component_types:
            LOGGER.debug("Did not replace component '{}' definition: replace={}".format(component_type, replace))
            return False

        self.component_types[component_type] = component_parameters
        return True


def get_component_type_parameters(component_type_definition: Dict[str, Any]) -> Optional[ComponentParameters]:
    """get_component_type_parameters"""
    deployment_type = component_type_definition.get(PARAMETER_COMPONENT_TYPE, None)
    if deployment_type is None or deployment_type not in ALLOWED_COMPONENT_TYPES:
        LOGGER.warning("Component type has an unsupported deployment type: {}".format(deployment_type))
        return None

    docker_image = component_type_definition.get(PARAMETER_DOCKER_IMAGE, None)
    if isinstance(docker_image, str):
        docker_image = ImageName(*docker_image.split(":"))

    attribute_parameters = component_type_definition.get(PARAMETER_ATTRIBUTES, {})
    if not isinstance(attribute_parameters, dict):
        attribute_parameters = {}

    return ComponentParameters(
        component_type=deployment_type,
        description=component_type_definition.get(PARAMETER_DESCRIPTION, ""),
        docker_image=docker_image,
        attributes={
            attribute_name: ComponentAttribute(
                environment=attribute_definition.get(ATTRIBUTE_ENVIRONMENT, None),
                optional=attribute_definition.get(ATTRIBUTE_OPTIONAL, False),
                default=attribute_definition.get(ATTRIBUTE_DEFAULT, None),
                include_in_start=attribute_definition.get(ATTRIBUTE_INCLUDE_IN_START, True)
            )
            for attribute_name, attribute_definition in attribute_parameters.items()
            if isinstance(attribute_definition, dict)
        },
        include_rabbitmq_parameters=deployment_type != EXTERNAL_COMPONENT_TYPE,
        include_general_parameters=deployment_type != EXTERNAL_COMPONENT_TYPE
    )


def load_component_parameters_from_yaml(yaml_filename: pathlib.Path) -> Optional[Tuple[str, ComponentParameters]]:
    """Loads and returns the component name and type specification from a YAML file."""
    try:
        with open(yaml_filename, mode="r", encoding="UTF-8") as component_file:
            component_type_definition = yaml.safe_load(component_file)

        if not isinstance(component_type_definition, dict):
            LOGGER.warning("The file '{}' does not contain a dictionary.".format(yaml_filename))
            return None

        component_name = component_type_definition.get(PARAMETER_COMPONENT_NAME, None)
        if not isinstance(component_name, str):
            LOGGER.warning("The file '{}' does not contain component name.".format(yaml_filename))
            return None

        component_type_parameters = get_component_type_parameters(component_type_definition)
        if component_type_parameters is None:
            LOGGER.error("Could not create component type parameters for '{}' from '{}'".format(
                component_name, yaml_filename))
            return None

        if component_name == COMPONENT_TYPE_LOG_WRITER:
            component_type_parameters.include_mongodb_parameters = True

        LOGGER.info("Loaded definition for '{}' from {}".format(component_name, yaml_filename))
        return component_name, component_type_parameters

    except (OSError, TypeError, yaml.YAMLError) as yaml_error:
        LOGGER.error("Encountered '{}' exception when loading component type definitions from '{}': {}".format(
            type(yaml_error).__name__, yaml_filename, yaml_error
        ))
        return None
