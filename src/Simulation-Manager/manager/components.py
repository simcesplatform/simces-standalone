# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains a class for keeping track of the simulation components."""

import dataclasses
from typing import List, Optional

import tools.tools as tools

LOGGER = tools.FullLogger(__name__)


@dataclasses.dataclass
class ComponentState:
    """Class for keeping track of the state of a simulation component.."""
    epoch_number: int
    error_state: bool = False


class SimulationComponents():
    """Keeps a list of components for the simulation and the latest epoch number
       for which a ready message was received from the component.
       Also keeps track if the component is in an error state."""
    NO_MESSAGES = -1
    MISSING_MESSAGE_ID = ""

    def __init__(self):
        self.__components = {}  # The values are ComponentState objects
        self.__latest_status_message_ids = []
        LOGGER.debug("New SimulationComponents object created.")

        # invariant: self.__latest_full_epoch <= for all self.__components[component_value].epoch_number
        self.__latest_full_epoch = SimulationComponents.NO_MESSAGES

    def add_component(self, component_name: str):
        """Adds a new component to the simulation component list.
           If the given component_name is already in the list, the function prints an error message."""
        if component_name not in self.__components:
            self.__components[component_name] = ComponentState(SimulationComponents.NO_MESSAGES, False)
            LOGGER.info("Component: {:s} registered to SimulationComponents.".format(component_name))
        else:
            LOGGER.warning("{:s} is already registered to the simulation component list".format(component_name))

    def remove_component(self, component_name: str):
        """Removes the given component from the simulation component list.
           If the given component_name is not found in the list, the function prints an error message."""
        if self.__components.pop(component_name, None) is None:
            LOGGER.warning("{:s} was not found in the simulation component list".format(component_name))
        else:
            LOGGER.info("Component: {:s} removed from SimulationComponents.".format(component_name))

        self._update_latest_full_epoch()

    def register_status_message(self, component_name: str, epoch_number: int,
                                status_message_id: str, error_state: bool = False):
        """Registers a new ready message for the given component and epoch number."""
        if component_name not in self.__components:
            LOGGER.warning("{:s} was not found in the simulation component list".format(component_name))
            return

        component_state = self.__components[component_name]
        if epoch_number < 0:
            LOGGER.warning("{:d} is not acceptable epoch number".format(epoch_number))
        elif component_state.error_state and not error_state:
            LOGGER.warning("Cannot register ready status for component {:s} because it is in an error state".format(
                component_name
            ))
        elif epoch_number <= component_state.epoch_number:
            LOGGER.debug("Epoch {:d} for {:s} is not larger epoch number than the previous {:d}".format(
                epoch_number, component_name, component_state.epoch_number))
        else:
            if (epoch_number != component_state.epoch_number + 1 and
                    component_state.epoch_number != SimulationComponents.NO_MESSAGES):
                LOGGER.warning("{:d} is not the next epoch, previous was {:d}".format(
                    epoch_number, component_state.epoch_number))
            if not status_message_id:
                LOGGER.warning("Status message id should not be empty.")

            if max(self._get_all_epoch_values()) < epoch_number:
                # the first status message for the epoch
                self.__latest_status_message_ids = [status_message_id]
            else:
                self.__latest_status_message_ids.append(status_message_id)

            component_state.epoch_number = epoch_number
            component_state.error_state = error_state
            self._update_latest_full_epoch()
            LOGGER.debug("{state_type:s} message for epoch {epoch:d} from component {component:s} registered.".format(
                state_type="Error" if error_state else "Ready",
                epoch=epoch_number,
                component=component_name))

    def get_component_list(self, latest_epoch_less_than=None) -> List[str]:
        """Returns a list of the registered simulation components."""
        if latest_epoch_less_than is None:
            return list(self.__components.keys())
        return [
            component_name
            for component_name, component_status in self.__components.items()
            if component_status.epoch_number < latest_epoch_less_than
        ]

    def get_latest_epoch_for_component(self, component_name: str) -> Optional[int]:
        """Returns the latest epoch number for which the component has responded with a status message."""
        component_status = self.__components.get(component_name, None)
        if component_status is None:
            return None
        return component_status.epoch_number

    def get_latest_full_epoch(self) -> int:
        """Returns the latest epoch number for which all registered components have responded with a status message."""
        return self.__latest_full_epoch

    def get_latest_status_message_ids(self) -> List[str]:
        """Returns the status message ids for the latest epoch as a list.
           The ids are given in the order they have been registered."""
        return self.__latest_status_message_ids

    def is_in_normal_state(self) -> bool:
        """Returns True, if none of the components are in an error state."""
        return True not in self._get_all_error_states()

    def is_component_in_normal_state(self, component_name: str) -> Optional[bool]:
        """Returns True, if the given component is registered and it is not in an error state.
           Otherwise, returns False, if the given component is registered and None if it is not."""
        if component_name not in self.__components:
            return None
        return not self.__components[component_name].error_state

    def __str__(self) -> str:
        """Returns a list of the component names with the latest epoch numbers and error states
           given in parenthesis after each name."""
        return ", ".join([
            "{:s} ({:d}, {:s})".format(
                component_name, component_status.epoch_number, str(component_status.error_state))
            for component_name, component_status in self.__components.items()
        ])

    def _get_all_epoch_values(self) -> List[int]:
        """Returns all the epoch numbers (the epochs with the most recent received status message per component)
           for the components as a list."""
        return [component_state.epoch_number for component_state in self.__components.values()]

    def _get_all_error_states(self) -> List[bool]:
        """Returns all the error state for the components as a list."""
        return [component_state.error_state for component_state in self.__components.values()]

    def _update_latest_full_epoch(self):
        """Updates the value for the latest full epoch."""
        self.__latest_full_epoch = min(self._get_all_epoch_values())
