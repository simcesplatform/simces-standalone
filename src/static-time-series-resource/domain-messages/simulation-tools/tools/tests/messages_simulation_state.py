# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Unit tests for the SimulationStateMessage class."""

import copy
import datetime
import json
import unittest

import tools.exceptions.messages
import tools.messages
from tools.datetime_tools import to_utc_datetime_object

from tools.tests.messages_common import (
    MESSAGE_TYPE_ATTRIBUTE, TIMESTAMP_ATTRIBUTE, SIMULATION_ID_ATTRIBUTE, SOURCE_PROCESS_ID_ATTRIBUTE,
    MESSAGE_ID_ATTRIBUTE, SIMULATION_STATE_ATTRIBUTE, NAME_ATTRIBUTE, DESCRIPTION_ATTRIBUTE,
    DEFAULT_TYPE, DEFAULT_TIMESTAMP, DEFAULT_SIMULATION_ID, DEFAULT_SOURCE_PROCESS_ID, DEFAULT_MESSAGE_ID,
    DEFAULT_SIMULATION_STATE, DEFAULT_NAME, DEFAULT_DESCRIPTION,
    FULL_JSON, ALTERNATE_JSON
)

DEFAULT_TYPE = "SimState"
FULL_JSON = {**FULL_JSON, "Type": DEFAULT_TYPE}
ALTERNATE_JSON = {**ALTERNATE_JSON, "Type": DEFAULT_TYPE}


class SimulationStateMessage(unittest.TestCase):
    """Unit tests for the SimulationStateMessage class."""

    def test_message_type(self):
        """Unit test for the SimulationStateMessage type."""
        self.assertEqual(tools.messages.SimulationStateMessage.CLASS_MESSAGE_TYPE, "SimState")
        self.assertEqual(tools.messages.SimulationStateMessage.MESSAGE_TYPE_CHECK, True)

    def test_message_creation(self):
        """Unit test for creating instances of SimulationStateMessage class."""

        # When message is created without a Timestamp attribute,
        # the current time in millisecond precision is used as the default value.
        utcnow1 = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        utcnow1 -= datetime.timedelta(microseconds=utcnow1.microsecond % 1000)
        message_full = tools.messages.SimulationStateMessage(**FULL_JSON)
        message_timestamp = to_utc_datetime_object(message_full.timestamp)
        utcnow2 = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        utcnow1 -= datetime.timedelta(microseconds=utcnow2.microsecond % 1000)

        self.assertGreaterEqual(message_timestamp, utcnow1)
        self.assertLessEqual(message_timestamp, utcnow2)
        self.assertEqual(message_full.message_type, DEFAULT_TYPE)
        self.assertEqual(message_full.simulation_id, DEFAULT_SIMULATION_ID)
        self.assertEqual(message_full.source_process_id, DEFAULT_SOURCE_PROCESS_ID)
        self.assertEqual(message_full.message_id, DEFAULT_MESSAGE_ID)
        self.assertEqual(message_full.simulation_state, DEFAULT_SIMULATION_STATE)
        self.assertEqual(message_full.name, DEFAULT_NAME)
        self.assertEqual(message_full.description, DEFAULT_DESCRIPTION)

        # Test with explicitely set timestamp
        message_timestamped = tools.messages.SimulationStateMessage(Timestamp=DEFAULT_TIMESTAMP, **FULL_JSON)
        self.assertEqual(message_timestamped.timestamp, DEFAULT_TIMESTAMP)
        self.assertEqual(message_timestamped.message_type, DEFAULT_TYPE)
        self.assertEqual(message_timestamped.simulation_id, DEFAULT_SIMULATION_ID)
        self.assertEqual(message_timestamped.source_process_id, DEFAULT_SOURCE_PROCESS_ID)
        self.assertEqual(message_timestamped.message_id, DEFAULT_MESSAGE_ID)
        self.assertEqual(message_timestamped.simulation_state, DEFAULT_SIMULATION_STATE)
        self.assertEqual(message_timestamped.name, DEFAULT_NAME)
        self.assertEqual(message_timestamped.description, DEFAULT_DESCRIPTION)

    def test_message_json(self):
        """Unit test for testing that the json from a message has correct attributes."""
        message_full_json = tools.messages.SimulationStateMessage(**FULL_JSON).json()

        self.assertIn(MESSAGE_TYPE_ATTRIBUTE, message_full_json)
        self.assertIn(SIMULATION_ID_ATTRIBUTE, message_full_json)
        self.assertIn(SOURCE_PROCESS_ID_ATTRIBUTE, message_full_json)
        self.assertIn(MESSAGE_ID_ATTRIBUTE, message_full_json)
        self.assertIn(TIMESTAMP_ATTRIBUTE, message_full_json)
        self.assertIn(SIMULATION_STATE_ATTRIBUTE, message_full_json)
        self.assertIn(NAME_ATTRIBUTE, message_full_json)
        self.assertIn(DESCRIPTION_ATTRIBUTE, message_full_json)
        self.assertEqual(len(message_full_json), 8)

    def test_message_bytes(self):
        """Unit test for testing that the bytes conversion works correctly."""
        # Convert to bytes and back to Message instance
        message_full = tools.messages.SimulationStateMessage(**FULL_JSON)
        message_copy = tools.messages.SimulationStateMessage(**json.loads(message_full.bytes().decode("UTF-8")))

        self.assertEqual(message_copy.timestamp, message_full.timestamp)
        self.assertEqual(message_copy.message_type, message_full.message_type)
        self.assertEqual(message_copy.simulation_id, message_full.simulation_id)
        self.assertEqual(message_copy.source_process_id, message_full.source_process_id)
        self.assertEqual(message_copy.message_id, message_full.message_id)
        self.assertEqual(message_copy.simulation_state, message_full.simulation_state)
        self.assertEqual(message_copy.name, message_full.name)
        self.assertEqual(message_copy.description, message_full.description)

    def test_message_equals(self):
        """Unit test for testing if the __eq__ comparison works correctly."""
        message_full = tools.messages.SimulationStateMessage(Timestamp=DEFAULT_TIMESTAMP, **FULL_JSON)
        message_copy = tools.messages.SimulationStateMessage(Timestamp=DEFAULT_TIMESTAMP, **FULL_JSON)
        message_alternate = tools.messages.SimulationStateMessage.from_json(ALTERNATE_JSON)

        self.assertEqual(message_copy, message_full)
        self.assertNotEqual(message_copy, message_alternate)

        attributes = [
            "simulation_id",
            "source_process_id",
            "message_id",
            "timestamp",
            "simulation_state",
            "name",
            "description"
        ]
        for attribute_name in attributes:
            with self.subTest(attribute=attribute_name):
                setattr(message_copy, attribute_name, getattr(message_alternate, attribute_name))
                self.assertNotEqual(message_copy, message_full)
                setattr(message_copy, attribute_name, getattr(message_full, attribute_name))
                self.assertEqual(message_copy, message_full)

    def test_invalid_values(self):
        """Unit tests for testing that invalid attribute values are recognized."""
        message_full = tools.messages.SimulationStateMessage(**FULL_JSON)
        message_full_json = message_full.json()

        allowed_simulation_states = [
            "running",
            "stopped"
        ]
        for simulation_state_str in allowed_simulation_states:
            message_full.simulation_state = simulation_state_str
            self.assertEqual(message_full.simulation_state, simulation_state_str)

        optional_attributes = [
            NAME_ATTRIBUTE,
            DESCRIPTION_ATTRIBUTE
        ]

        invalid_attribute_exceptions = {
            MESSAGE_TYPE_ATTRIBUTE: tools.exceptions.messages.MessageTypeError,
            SIMULATION_ID_ATTRIBUTE: tools.exceptions.messages.MessageDateError,
            SOURCE_PROCESS_ID_ATTRIBUTE: tools.exceptions.messages.MessageSourceError,
            MESSAGE_ID_ATTRIBUTE: tools.exceptions.messages.MessageIdError,
            TIMESTAMP_ATTRIBUTE: tools.exceptions.messages.MessageDateError,
            SIMULATION_STATE_ATTRIBUTE: tools.exceptions.messages.MessageStateValueError,
            NAME_ATTRIBUTE: tools.exceptions.messages.MessageValueError,
            DESCRIPTION_ATTRIBUTE: tools.exceptions.messages.MessageValueError
        }
        invalid_attribute_values = {
            MESSAGE_TYPE_ATTRIBUTE: ["Test", 12, "", "Epoch"],
            SIMULATION_ID_ATTRIBUTE: ["simulation-id", 12, "2020-07-31T24:11:11.123Z", ""],
            SOURCE_PROCESS_ID_ATTRIBUTE: [12, ""],
            MESSAGE_ID_ATTRIBUTE: [12, True, ""],
            TIMESTAMP_ATTRIBUTE: ["timestamp", 12, "2020-07-31T24:11:11.123Z", ""],
            SIMULATION_STATE_ATTRIBUTE: ["waiting", 12, ""],
            NAME_ATTRIBUTE: [1, 15],
            DESCRIPTION_ATTRIBUTE: [1, 15]
        }
        for invalid_attribute in invalid_attribute_exceptions:
            if invalid_attribute != TIMESTAMP_ATTRIBUTE and invalid_attribute not in optional_attributes:
                json_invalid_attribute = copy.deepcopy(message_full_json)
                json_invalid_attribute.pop(invalid_attribute)
                with self.subTest(attribute=invalid_attribute):
                    with self.assertRaises(invalid_attribute_exceptions[invalid_attribute]):
                        tools.messages.SimulationStateMessage(**json_invalid_attribute)

            for invalid_value in invalid_attribute_values[invalid_attribute]:
                json_invalid_attribute = copy.deepcopy(message_full_json)
                json_invalid_attribute[invalid_attribute] = invalid_value
                with self.subTest(attribute=invalid_attribute, value=invalid_value):
                    with self.assertRaises((ValueError, invalid_attribute_exceptions[invalid_attribute])):
                        tools.messages.SimulationStateMessage(**json_invalid_attribute)


if __name__ == '__main__':
    unittest.main()
