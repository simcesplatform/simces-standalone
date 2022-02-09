# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Unit tests for the RabbitmqClient class."""

# import asyncio
import json
from json.decoder import JSONDecodeError
import subprocess
from typing import Union

from aiounittest.case import AsyncTestCase

import tools.messages as messages
from tools.db_clients import MongodbClient
from tools.tests.messages_common import EPOCH_TEST_JSON, RESULT_TEST_JSON, STATUS_TEST_JSON
from tools.tools import load_environmental_variables

MONGO_COMMAND = ' '.join([
    'mongo {host:s}:{port:d}/{database:s}',
    '-u {username:s} -p{password:s} --authenticationDatabase admin',
    '--quiet --eval "JSON.stringify({query:s})"'
])

ENV_VARIABLES = load_environmental_variables(
    ("MONGODB_HOST", str, "localhost"),
    ("MONGODB_PORT", int, 27017),
    ("MONGODB_USERNAME", str, ""),
    ("MONGODB_PASSWORD", str, ""),
    ("MONGODB_DATABASE", str, "db"),
    ("MONGODB_METADATA_COLLECTION", str, "simulations"),
    ("MONGODB_MESSAGES_COLLECTION_PREFIX", str, "simulation_"),
    ("MONGODB_COLLECTION_IDENTIFIER", str, "SimulationId")
)


def run_mongo_query(mongo_query: str) \
        -> Union[subprocess.CompletedProcess, subprocess.CalledProcessError]:
    """Runs a query in the Mongo database and returns the result."""
    mongo_command = MONGO_COMMAND.format(
        host=ENV_VARIABLES["MONGODB_HOST"],
        port=ENV_VARIABLES["MONGODB_PORT"],
        database=ENV_VARIABLES["MONGODB_DATABASE"],
        username=ENV_VARIABLES["MONGODB_USERNAME"],
        password=ENV_VARIABLES["MONGODB_PASSWORD"],
        query=mongo_query)
    try:
        process = subprocess.run(mongo_command, shell=True, check=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
    except subprocess.CalledProcessError as process_error:
        return process_error


def get_collection_name(message_object: messages.AbstractMessage) -> str:
    """Returns the expected simulation-specific collection name for the message."""
    return "{collection_prefix:s}{simulation_id:s}".format(
        collection_prefix=ENV_VARIABLES["MONGODB_MESSAGES_COLLECTION_PREFIX"],
        simulation_id=message_object.simulation_id
    )


def document_exists(message_object: messages.AbstractMessage, topic_name: str) -> bool:
    """Checks if the given message with the given topic exists in the given collection.
       Returns True if the message is found. Otherwise, returns False."""
    find_attributes = [
        "SimulationId: '{:s}'".format(message_object.simulation_id),
        "Type: '{:s}'".format(message_object.message_type),
        "Timestamp: ISODate('{:s}')".format(message_object.timestamp),
        "SourceProcessId: '{:s}'".format(message_object.source_process_id),
        "MessageId: '{:s}'".format(message_object.message_id),
        "Topic: '{:s}'".format(topic_name)
    ]
    query_str = "db.getCollection('{:s}').findOne({{{:s}}})".format(
        get_collection_name(message_object), ", ".join(find_attributes))
    result = run_mongo_query(query_str)

    if isinstance(result, subprocess.CalledProcessError) or result.returncode != 0:
        return False
    try:
        json_output = json.loads(result.stdout.decode("UTF-8"))
        return (
            json_output is not None and
            json_output.get("SimulationId", None) == message_object.simulation_id and
            json_output.get("Type", None) == message_object.message_type and
            json_output.get("Timestamp", None) == message_object.timestamp and
            json_output.get("SourceProcessId", None) == message_object.source_process_id and
            json_output.get("MessageId", None) == message_object.message_id and
            json_output.get("Topic", None) == topic_name
        )
    except JSONDecodeError:
        return False


class TestMongodbClient(AsyncTestCase):
    """Unit tests for MongodbClient object."""
    async def test_adding_single_document(self):
        """Unit test for adding documents to MongoDB one document at a time."""
        client = MongodbClient()
        status_message = messages.StatusMessage.from_json(STATUS_TEST_JSON)
        epoch_message = messages.EpochMessage.from_json(EPOCH_TEST_JSON)
        result_message = messages.ResultMessage.from_json(RESULT_TEST_JSON)

        for simulation_message, topic_name in zip(
                [status_message, epoch_message, result_message],
                ["Status", "Epoch", "Result"]):
            with self.subTest(topic_name=topic_name, simulation_message=simulation_message):
                self.assertIsNotNone(simulation_message)
                if isinstance(simulation_message, messages.AbstractMessage):
                    self.assertFalse(document_exists(simulation_message, topic_name))
                    write_result = await client.store_message(simulation_message.json(), topic_name)
                    self.assertTrue(write_result)
                    self.assertTrue(document_exists(simulation_message, topic_name))

    async def test_adding_many_documents(self):
        """Unit test for adding documents to MongoDB several documents at a time."""
        client = MongodbClient()

        # Use the Message classes to get a current timestamp attribute to the messages.
        simulation_messages = [
            messages.StatusMessage.from_json(STATUS_TEST_JSON),
            messages.EpochMessage.from_json(EPOCH_TEST_JSON),
            messages.ResultMessage.from_json(RESULT_TEST_JSON)
        ]

        messages_with_topics = []
        for simulation_message, topic_name in zip(simulation_messages, ["Status", "Epoch", "Result"]):
            with self.subTest(topic_name=topic_name, simulation_message=simulation_message):
                self.assertFalse(document_exists(simulation_message, topic_name))
                messages_with_topics.append((simulation_message.json(), topic_name))

        write_result = await client.store_messages(messages_with_topics)
        self.assertEqual(len(write_result), len(simulation_messages))

        for simulation_message, topic_name in zip(simulation_messages, ["Status", "Epoch", "Result"]):
            with self.subTest(topic_name=topic_name, simulation_message=simulation_message):
                self.assertTrue(document_exists(simulation_message, topic_name))

    async def test_updating_metadata(self):
        """Unit test adding or updating a simulation metadata record."""
        # TODO: implement test_updating_metadata

    async def test_adding_metadata_indexes(self):
        """Unit test for adding or updating metadata collection indexes."""
        # TODO: implement test_adding_metadata_indexes

    async def test_adding_simulation_indexes(self):
        """Unit test for adding or updating simulation specific collection indexes."""
        # TODO: implement test_adding_simulation_indexes

    async def test_connection_failures(self):
        """Unit tests for failed connections to the database."""
        # TODO: implement test_connection_failures
