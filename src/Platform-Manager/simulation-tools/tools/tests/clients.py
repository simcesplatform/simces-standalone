# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Unit tests for the RabbitmqClient class."""

import asyncio
from typing import Iterator, Union

from aiounittest.case import AsyncTestCase

from tools.clients import RabbitmqClient
from tools.messages import BaseMessage, EpochMessage, GeneralMessage, StatusMessage, get_next_message_id
from tools.tests.messages_common import EPOCH_TEST_JSON, ERROR_TEST_JSON, GENERAL_TEST_JSON, STATUS_TEST_JSON


def get_new_message(old_message: BaseMessage, id_generator: Iterator[str]) -> BaseMessage:
    """Returns a new message object with a new Timestamp and MessageId and
       other attributes equal to the old message"""
    json_message = old_message.json()
    json_message["MessageId"] = next(id_generator)
    json_message.pop("Timestamp")

    if isinstance(old_message, EpochMessage):
        return EpochMessage(**json_message)
    if isinstance(old_message, StatusMessage):
        return StatusMessage(**json_message)
    return GeneralMessage(**json_message)


class MessageStorage:
    """Helper class for storing received messages through callback function."""
    def __init__(self):
        self.messages = []

    async def callback(self, message_object: Union[BaseMessage, dict, str], message_topic: str):
        """Adds the given message and topic to the messages list."""
        # print("here", self.messages, message_object.message_id)
        self.messages.append((message_object, message_topic))


class TestRabbitmqClient(AsyncTestCase):
    """Unit tests for sending and receiving messages using RabbitmqClient object."""
    async def test_message_sending_and_receiving(self):
        """Tests sending and receiving message using RabbitMQ message bus using RabbitmqClient.
           Checks that the correct messages are received and in the correct order."""
        # Load the base message objects.
        epoch_message = EpochMessage(**EPOCH_TEST_JSON)
        error_message = StatusMessage(**ERROR_TEST_JSON)
        general_message = GeneralMessage(**GENERAL_TEST_JSON)
        status_message = StatusMessage(**STATUS_TEST_JSON)

        # Setup the RabbitMQ clients and the message storage objects for the callback functions.
        clients = []
        message_storages = []
        for _ in range(3):
            clients.append(RabbitmqClient())
            message_storages.append(MessageStorage())

        # Setup the listeners for the clients.
        client_topic_lists = [
            ["TopicA.*", "TopicB.Error"],
            ["TopicA.Error", "TopicB.Epoch", "TopicB"],
            ["TopicA.Epoch", "TopicA.Status", "TopicB.#"],
            ["#"]
        ]
        for client, message_storage, topic_list in zip(clients, message_storages, client_topic_lists):
            client.add_listener(topic_list, message_storage.callback)

        # Setup the message id generators.
        id_generators = [
            get_next_message_id(process_id)
            for process_id in ["manager", "tester", "helper"]
        ]

        # Setup the check lists that are used to check whether the correct message were received.
        # At the end these should correspond to message_storage1.messages, message_storage2.messages, ...
        check_lists = [[], [], [], []]

        # Setup the test message schema. Each element contains the topic name, base message and
        # a list of the check list indexes that correspond to the lists that are expected to receive the messages.
        test_list = [
            ("TopicA", general_message, [3]),
            ("TopicA.Epoch", epoch_message, [0, 2, 3]),
            ("TopicA.Status", status_message, [0, 2, 3]),
            ("TopicA.Error", error_message, [0, 1, 3]),
            ("TopicA.Error.Special", error_message, [3]),
            ("TopicB", general_message, [1, 2, 3]),
            ("TopicB.Epoch", epoch_message, [1, 2, 3]),
            ("TopicB.Status", status_message, [2, 3]),
            ("TopicB.Error", error_message, [0, 2, 3]),
            ("TopicB.Error.Special", error_message, [2, 3]),
            ("TopicC", general_message, [3])
        ]

        # 5 second wait to allow the listeners to setup.
        await asyncio.sleep(5)
        for client, topic_list in zip(clients, client_topic_lists):
            self.assertEqual(client.listened_topics, list(set(topic_list)))

        # Sends the test messages.
        for send_client, message_id_generator in zip(clients, id_generators):
            for test_topic, test_message, check_list_indexes in test_list:
                # Create a new message with a new timestamp and message id.
                new_test_message = get_new_message(test_message, message_id_generator)
                await send_client.send_message(test_topic, new_test_message.bytes())
                for check_list_index in check_list_indexes:
                    check_lists[check_list_index].append((new_test_message, test_topic))

        # 5 second wait to allow the message handlers to finish.
        await asyncio.sleep(5)

        # Check that the received messages equal to the excpected messages.
        for message_storage, check_list in zip(message_storages, check_lists):
            self.assertEqual(message_storage.messages, check_list)

        # Close the clients.
        for client in clients:
            self.assertFalse(client.is_closed)
            await client.close()
            self.assertTrue(client.is_closed)
            self.assertEqual(client.listened_topics, [])

        # 5 second wait to allow the clients to properly close.
        await asyncio.sleep(5)

    async def test_connection_failures(self):
        """Unit tests for failed connections to the message bus."""
        # TODO: implement test_connection_failures
