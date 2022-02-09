# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains the message class for the simulation platform simulation state messages."""

from __future__ import annotations
from typing import Any, Dict, Union

from tools.exceptions.messages import MessageStateValueError, MessageValueError
from tools.message.abstract import AbstractMessage
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class SimulationStateMessage(AbstractMessage):
    """Class containing all the attributes for a simulation state message."""
    CLASS_MESSAGE_TYPE = "SimState"
    MESSAGE_TYPE_CHECK = True

    MESSAGE_ATTRIBUTES = {
        "SimulationState": "simulation_state",
        "Name": "name",
        "Description": "description"
    }
    OPTIONAL_ATTRIBUTES = ["Name", "Description"]

    MESSAGE_ATTRIBUTES_FULL = {
        **AbstractMessage.MESSAGE_ATTRIBUTES_FULL,
        **MESSAGE_ATTRIBUTES
    }
    OPTIONAL_ATTRIBUTES_FULL = AbstractMessage.OPTIONAL_ATTRIBUTES_FULL + OPTIONAL_ATTRIBUTES

    SIMULATION_STATES = [
        "running",
        "stopped"
    ]

    @property
    def simulation_state(self) -> str:
        """The simulation state attribute."""
        return self.__simulation_state

    @property
    def name(self) -> Union[str, None]:
        """The name of the simulation or None."""
        return self.__name

    @property
    def description(self) -> Union[str, None]:
        """The description for the simulation or None."""
        return self.__description

    @simulation_state.setter
    def simulation_state(self, simulation_state: str):
        if not self._check_simulation_state(simulation_state):
            raise MessageStateValueError("'{:s}' is not a valid value for simulation state".format(
                str(simulation_state)))
        self.__simulation_state = simulation_state

    @name.setter
    def name(self, name: Union[str, None]):
        if not self._check_name(name):
            raise MessageValueError("The simulation name must be either None or a string.")
        self.__name = name

    @description.setter
    def description(self, description: Union[str, None]):
        if not self._check_description(description):
            raise MessageValueError("The simulation description must be either None or a string.")
        self.__description = description

    def __eq__(self, other: Any) -> bool:
        return (
            super().__eq__(other) and
            isinstance(other, SimulationStateMessage) and
            self.simulation_state == other.simulation_state and
            self.name == other.name and
            self.description == other.description
        )

    @classmethod
    def _check_simulation_state(cls, simulation_state: str) -> bool:
        return simulation_state in cls.SIMULATION_STATES

    @classmethod
    def _check_name(cls, name: Union[str, None]) -> bool:
        return name is None or isinstance(name, str)

    @classmethod
    def _check_description(cls, description: Union[str, None]) -> bool:
        return description is None or isinstance(description, str)

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[SimulationStateMessage, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON does not contain valid values, returns None."""
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None


SimulationStateMessage.register_to_factory()
