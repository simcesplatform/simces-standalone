# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Unit test module for the AbstractSimulationComponent class."""

import asyncio
import datetime
import os
from typing import List, Tuple, Union, cast

from aiounittest.case import AsyncTestCase

from tools.clients import RabbitmqClient
from tools.components import AbstractSimulationComponent
from tools.datetime_tools import to_iso_format_datetime_string
from tools.messages import (
    BaseMessage, AbstractMessage, AbstractResultMessage, EpochMessage,
    SimulationStateMessage, StatusMessage, get_next_message_id)


async def send_message(message_client: RabbitmqClient, message_object: AbstractMessage, topic_name: str) -> None:
    """Sends the given message to the message bus using the given message client."""
    await message_client.send_message(topic_name, message_object.bytes())


class MessageStorage:
    """Helper class for storing received messages through callback function."""
    def __init__(self, ignore_source_process_id: str):
        self.messages_and_topics = []
        self.ignore_source_process_id = ignore_source_process_id

    async def callback(self, message_object: Union[BaseMessage, dict, str], message_topic: str) -> None:
        """Adds the given message and topic to the messages list."""
        if not isinstance(message_object, AbstractMessage):
            raise ValueError(message_object)
        if message_object.source_process_id != self.ignore_source_process_id:
            self.messages_and_topics.append((message_object, message_topic))


class MessageGenerator:
    """Message generator for unit tests."""
    def __init__(self, simulation_id: str, process_id: str):
        self.simulation_id = simulation_id
        self.process_id = process_id
        self.id_generator = get_next_message_id(self.process_id)
        self.initial_time = datetime.datetime(2020, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc)
        self.epoch_interval = 3600
        self.latest_message_id = "-".join([process_id, "0"])

    def get_epoch_start(self, epoch_number: int) -> str:
        """Returns the start time for the given epoch in ISO 8601 format."""
        return cast(str, to_iso_format_datetime_string(
            self.initial_time + (epoch_number - 1) * datetime.timedelta(seconds=self.epoch_interval)))

    def get_epoch_end(self, epoch_number: int) -> str:
        """Returns the start time for the given epoch in ISO 8601 format."""
        return cast(str, to_iso_format_datetime_string(
            self.initial_time + epoch_number * datetime.timedelta(seconds=self.epoch_interval)))

    def get_simulation_state_message(self, is_running: bool) -> SimulationStateMessage:
        """Returns a simulation state message."""
        self.latest_message_id = next(self.id_generator)
        return SimulationStateMessage(**{
            "Type": "SimState",
            "SimulationId": self.simulation_id,
            "SourceProcessId": self.process_id,
            "MessageId": self.latest_message_id,
            "SimulationState": "running" if is_running else "stopped"
        })

    def get_epoch_message(self, epoch_number: int, triggering_message_ids: List[str]) -> EpochMessage:
        """Returns an epoch messages."""
        self.latest_message_id = next(self.id_generator)
        return EpochMessage(**{
            "Type": "Epoch",
            "SimulationId": self.simulation_id,
            "SourceProcessId": self.process_id,
            "MessageId": self.latest_message_id,
            "EpochNumber": epoch_number,
            "TriggeringMessageIds": triggering_message_ids,
            "StartTime": self.get_epoch_start(epoch_number),
            "EndTime": self.get_epoch_end(epoch_number)
        })

    def get_status_message(self, epoch_number: int, triggering_message_ids: List[str]) -> StatusMessage:
        """Returns a status message."""
        self.latest_message_id = next(self.id_generator)
        return StatusMessage(**{
            "Type": "Status",
            "SimulationId": self.simulation_id,
            "SourceProcessId": self.process_id,
            "MessageId": self.latest_message_id,
            "EpochNumber": epoch_number,
            "TriggeringMessageIds": triggering_message_ids,
            "Value": "ready"
        })

    def get_error_message(self, epoch_number: int, triggering_message_ids: List[str],
                          description: str) -> StatusMessage:
        """Returns an error message."""
        self.latest_message_id = next(self.id_generator)
        return StatusMessage(**{
            "Type": "Status",
            "SimulationId": self.simulation_id,
            "SourceProcessId": self.process_id,
            "MessageId": self.latest_message_id,
            "EpochNumber": epoch_number,
            "TriggeringMessageIds": triggering_message_ids,
            "Value": "error",
            "Description": description
        })


class TestAbstractSimulationComponent(AsyncTestCase):
    """Unit tests for sending and receiving messages using AbstractSimulationComponent object."""
    simulation_id = "2020-01-01T00:00:00.000Z"
    component_name = "TestComponent"
    other_topics = []

    short_wait = 0.5
    long_wait = 2.5

    # A callable function that returns an instance of the simulation component used for the unit tests.
    # NOTE: this can also be the component type if the constructor can be used to create the component.
    component_creator = AbstractSimulationComponent
    # The keyword arguments for the component creator.
    # NOTE: for the AbstractSimulationComponent the parameters can be given
    #       either as constructor arguments or as environmental variables
    component_creator_params = {}
    # The generator class that can produce messages comparable to the ones produced by the test component.
    message_generator_type = MessageGenerator

    # The last epoch number for the normal simulation test scenario.
    normal_simulation_epochs = 10

    test_manager_name = "TestManager"
    manager_message_generator = MessageGenerator(simulation_id, test_manager_name)

    def __init__(self, *args, **kwargs):
        # to be more compatible with components that take all the base arguments from environment variables
        super().__init__(*args, **kwargs)
        if "simulation_id" not in self.__class__.component_creator_params:
            os.environ["SIMULATION_ID"] = self.__class__.simulation_id
        if "component_name" not in self.__class__.component_creator_params:
            os.environ["SIMULATION_COMPONENT_NAME"] = self.__class__.component_name

    def get_expected_messages(self, component_message_generator: MessageGenerator, epoch_number: int,
                              triggering_message_ids: List[str]) -> List[Tuple[AbstractMessage, str]]:
        """Returns the expected messages and topic names that the test component is expected to
           generate at epoch epoch_number, epoch 0 corresponds to the start of the simulation."""
        return [
            (component_message_generator.get_status_message(epoch_number, triggering_message_ids), "Status.Ready")
        ]

    def compare_abstract_message(self, first_message: AbstractMessage, second_message: AbstractMessage):
        """Asserts that the two given abstract result messages correspond to each other."""
        self.assertEqual(first_message.message_type, second_message.message_type)
        self.assertEqual(first_message.simulation_id, second_message.simulation_id)
        self.assertEqual(first_message.source_process_id, second_message.source_process_id)
        # The id number in the message id does not have to be exactly the exprected but check the starting string.
        self.assertEqual("-".join(first_message.message_id.split("-")[:-1]),
                         "-".join(second_message.message_id.split("-")[:-1]))

    def compare_abstract_result_message(self, first_message: AbstractResultMessage,
                                        second_message: AbstractResultMessage):
        """Asserts that the two given abstract result messages correspond to each other."""
        self.compare_abstract_message(first_message, second_message)
        self.assertEqual(first_message.epoch_number, second_message.epoch_number)
        self.assertEqual(first_message.triggering_message_ids, second_message.triggering_message_ids)

    def compare_status_message(self, first_message: StatusMessage, second_message: StatusMessage):
        """Asserts that two given status messages correspond to each other."""
        self.compare_abstract_result_message(first_message, second_message)
        self.assertEqual(first_message.value, second_message.value)
        self.assertEqual(first_message.description, second_message.description)

    def compare_message(self, first_message: AbstractMessage, second_message: AbstractMessage) -> bool:
        """Asserts that the two given messages correspond to each other.
           The function checks only the relevant parts of the message, not for example the timestamps.
           Returns True, if the given messages where of a support type. Otherwise, returns False.
        """
        self.assertEqual(type(first_message), type(second_message))

        if isinstance(second_message, StatusMessage):
            self.compare_status_message(cast(StatusMessage, first_message), second_message)
            return True

        return False

    async def start_tester(self) -> Tuple[RabbitmqClient, MessageStorage,
                                          MessageGenerator, AbstractSimulationComponent]:
        """Tests the creation of the test component at the start of the simulation and returns a 4-tuple containing
           the message bus client, message storage object, test component message generator object and
           the test component object for the use of further tests."""
        message_storage = MessageStorage(self.__class__.test_manager_name)
        message_client = RabbitmqClient()
        message_client.add_listener("#", message_storage.callback)

        component_message_generator = self.__class__.message_generator_type(
            self.__class__.simulation_id, self.__class__.component_name)
        test_component = self.__class__.component_creator(**self.__class__.component_creator_params)
        await test_component.start()

        # Wait for a few seconds to allow the component to setup.
        await asyncio.sleep(self.__class__.long_wait)
        self.assertFalse(message_client.is_closed)
        self.assertFalse(test_component.is_stopped)
        self.assertFalse(test_component.is_client_closed)

        self.assertEqual(test_component.simulation_id, self.__class__.simulation_id)
        self.assertEqual(test_component.component_name, self.__class__.component_name)

        return (message_client, message_storage, component_message_generator, test_component)

    async def epoch_tester(self, epoch_number: int, message_client: RabbitmqClient,
                           message_storage: MessageStorage, component_message_generator: MessageGenerator):
        """Test the behavior of the test_component in one epoch."""
        number_of_previous_messages = len(message_storage.messages_and_topics)
        if epoch_number == 0:
            # Epoch number 0 corresponds to the start of the simulation.
            manager_message = self.__class__.manager_message_generator.\
                get_simulation_state_message(True)
        else:
            manager_message = self.__class__.manager_message_generator.get_epoch_message(
                epoch_number, [component_message_generator.latest_message_id])
        expected_responds = self.get_expected_messages(
            component_message_generator, epoch_number, [manager_message.message_id])

        # TODO: the following needs to modified if the test component requires more than just the epoch message
        await send_message(message_client, manager_message, manager_message.message_type)

        # Wait a short time to allow the message storage to store the respond.
        # TODO: figure out how to tie connect the message checking to the message receiver => remove this sleep
        await asyncio.sleep(self.__class__.short_wait)

        received_messages = message_storage.messages_and_topics
        self.assertEqual(len(received_messages), number_of_previous_messages + len(expected_responds))

        # Compare the received messages to the expected messages.
        # TODO: implement message checking that does not care about the order of the received messages
        for index, (received_responce, expected_responce) in enumerate(
                zip(received_messages[-len(expected_responds):], expected_responds),
                start=1):
            with self.subTest(message_index=index):
                received_message, received_topic = received_responce
                expected_message, expected_topic = expected_responce
                self.assertEqual(received_topic, expected_topic)
                self.assertTrue(self.compare_message(received_message, expected_message))

    async def end_tester(self, message_client: RabbitmqClient, test_component: AbstractSimulationComponent):
        """Tests the behavior of the test component at the end of the simulation."""
        end_message = self.__class__.manager_message_generator.get_simulation_state_message(False)
        await send_message(message_client, end_message, end_message.message_type)
        await message_client.close()

        # Wait a few seconds to allow the test component and the message clients to close.
        await asyncio.sleep(self.__class__.long_wait)

        # Check that the component is stopped and the message clients are closed.
        self.assertTrue(test_component.is_stopped)
        self.assertTrue(test_component.is_client_closed)
        self.assertTrue(message_client.is_closed)

    async def test_normal_simulation(self):
        """A test with a normal input in a simulation containing only manager and test component."""
        # Test the creation of the test component.
        message_client, message_storage, component_message_generator, test_component = \
            await self.start_tester()

        # Test the component with the starting simulation state message (epoch 0) and 10 normal epochs.
        for epoch_number in range(0, self.__class__.normal_simulation_epochs + 1):
            with self.subTest(epoch_number=epoch_number):
                await self.epoch_tester(epoch_number, message_client, message_storage, component_message_generator)

        # Test the closing down of the test component after simulation state message "stopped".
        await self.end_tester(message_client, test_component)

    async def test_error_message(self):
        """Unit test for simulation component sending an error message."""
        # Setup the component and start the simulation.
        message_client, message_storage, component_message_generator, test_component = \
            await self.start_tester()
        await self.epoch_tester(0, message_client, message_storage, component_message_generator)

        # Generate the expected error message and check if it matches to the one the test component sends.
        error_description = "Testing error message"
        expected_message = component_message_generator.get_error_message(
            epoch_number=0,
            triggering_message_ids=[self.__class__.manager_message_generator.latest_message_id],
            description=error_description)
        number_of_previous_messages = len(message_storage.messages_and_topics)
        await test_component.send_error_message(error_description)

        # Wait a short time to ensure that the message receiver has received the error message.
        await asyncio.sleep(self.__class__.short_wait)

        # Check that the correct error message was received.
        self.assertEqual(len(message_storage.messages_and_topics), number_of_previous_messages + 1)
        received_message, received_topic = message_storage.messages_and_topics[-1]
        self.assertEqual(received_topic, "Status.Error")
        self.assertTrue(self.compare_message(received_message, expected_message))

        await self.end_tester(message_client, test_component)

    # async def test_component_robustness(self):
    #     """Unit test for testing simulation component behavior when simulation does not go smoothly."""
    #     # TODO: implement test_component_robustness
