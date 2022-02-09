# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Unit test module for the AbstractSimulationComponent class."""

import os
from typing import Any, List, Tuple, cast

from tools.messages import AbstractMessage, ResultMessage
# Importing TestAbstractSimulationComponent means that also those unit tests
# will be run when running the unit test in this repository.
from tools.tests.components import MessageGenerator, TestAbstractSimulationComponent
from tools.tools import FullLogger

from dummy.dummy import DummyComponent
from dummy.random_series import get_all_random_series, get_latest_values, get_random_initial_values

LOGGER = FullLogger(__name__)


def compare_values(value1: Any, value2: Any) -> bool:
    """Returns True, if the two values are of the same type and contain a similar structure
       in case of lists or dictionaries or are equal in case of strings."""
    if not isinstance(value1, type(value2)):
        return False

    if isinstance(value1, str):
        return value1 == value2

    if isinstance(value1, (list, tuple)):
        if len(value1) != len(value2):
            return False
        for element1, element2 in zip(value1, value2):
            if not compare_values(element1, element2):
                return False

    elif isinstance(value1, dict):
        if set(value1) != set(value2):
            return False
        for attribute_name in value1:
            if not compare_values(value1[attribute_name], value2[attribute_name]):
                return False

    return True


class MessageGeneratorExtended(MessageGenerator):
    """Message generator for unit tests. Extended with result messages produced by DummyComponent."""
    def __init__(self, simulation_id: str, process_id: str) -> None:
        super().__init__(simulation_id, process_id)
        self.values = get_random_initial_values()

    def get_result_message(self, epoch_number: int, triggering_message_ids: List[str]) -> ResultMessage:
        """Returns a result message similar to the dummy component result messages."""
        self.latest_message_id = next(self.id_generator)
        result_message = ResultMessage(**{
            "Type": "Result",
            "SimulationId": self.simulation_id,
            "SourceProcessId": self.process_id,
            "MessageId": self.latest_message_id,
            "EpochNumber": epoch_number,
            "TriggeringMessageIds": triggering_message_ids
        })
        result_values = get_all_random_series(
            self.values, self.get_epoch_start(epoch_number), self.get_epoch_end(epoch_number))
        self.values = get_latest_values(result_values)
        result_message.result_values = result_values
        return result_message


def dummy_component_creator(message: str, **kwargs) -> DummyComponent:
    """An example of using a creator function with Test class. Returns a new Dummy component."""
    if message.lower() == "hello":
        # NOTE: the default log level setting for running the unit tests is critical only
        LOGGER.info("Hello from component_creator!")
    return DummyComponent(**kwargs)


# Use TestAbstractSimulationComponent as a base class to define the unit tests.
class TestDummyComponent(TestAbstractSimulationComponent):
    """Unit tests for sending and receiving messages using DummyComponent object."""
    component_name = "TestDummy"

    component_creator = dummy_component_creator
    component_creator_params = {
        "simulation_id": TestAbstractSimulationComponent.simulation_id,
        "component_name": component_name,
        "message": "hello"
    }
    message_generator_type = MessageGeneratorExtended
    normal_simulation_epochs = 12
    short_wait = 0.5
    long_wait = 2.5

    os.environ["MIN_SLEEP_TIME"] = "0"
    os.environ["MAX_SLEEP_TIME"] = "0"
    os.environ["ERROR_CHANCE"] = "0"
    os.environ["SEND_MISS_CHANCE"] = "0"
    os.environ["RECEIVE_MISS_CHANCE"] = "0"
    os.environ["WARNING_CHANCE"] = "0"

    def get_expected_messages(self, component_message_generator: MessageGeneratorExtended, epoch_number: int,
                              triggering_message_ids: List[str]) -> List[Tuple[AbstractMessage, str]]:
        """Returns the expected messages and topic names that the test component is expected to
           generate at epoch epoch_number, epoch 0 corresponds to the start of the simulation."""
        if epoch_number == 0:
            return [
                (component_message_generator.get_status_message(epoch_number, triggering_message_ids), "Status.Ready")
            ]
        return [
            (component_message_generator.get_result_message(epoch_number, triggering_message_ids), "Result"),
            (component_message_generator.get_status_message(epoch_number, triggering_message_ids), "Status.Ready")
        ]

    def compare_result_message(self, first_message: ResultMessage, second_message: ResultMessage):
        """Asserts that two given result matches each other regarding the required fields and
           that the result fields have similar structure."""
        self.compare_abstract_result_message(first_message, second_message)
        first_result_attributes = set(first_message.result_values)
        seconds_result_attributes = set(second_message.result_values)
        first_json = first_message.json()
        seconds_json = second_message.json()

        # Check that the result values contain the same number of values that are of the same type
        self.assertEqual(first_result_attributes, seconds_result_attributes)
        for attribute_name in first_result_attributes:
            self.assertTrue(compare_values(first_json[attribute_name], seconds_json[attribute_name]))

    def compare_message(self, first_message: AbstractMessage, second_message: AbstractMessage) -> bool:
        """Asserts that the two given messages correspond to each other.
           The function checks only the relevant parts of the message, not for example the timestamps.
           Returns True, if the given messages where of a support type. Otherwise, returns False.
        """
        if super().compare_message(first_message, second_message):
            return True

        if isinstance(second_message, ResultMessage):
            self.compare_result_message(cast(ResultMessage, first_message), second_message)
            return True

        return False
