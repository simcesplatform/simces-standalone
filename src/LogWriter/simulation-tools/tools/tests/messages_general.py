# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Unit test for the GeneralMessage class."""

import copy
import datetime
import json
import unittest

import tools.exceptions.messages
import tools.messages
from tools.datetime_tools import to_utc_datetime_object

from tools.tests.messages_common import (
    MESSAGE_TYPE_ATTRIBUTE, TIMESTAMP_ATTRIBUTE, SIMULATION_ID_ATTRIBUTE, SOURCE_PROCESS_ID_ATTRIBUTE,
    MESSAGE_ID_ATTRIBUTE, EPOCH_NUMBER_ATTRIBUTE, LAST_UPDATED_IN_EPOCH_ATTRIBUTE,
    TRIGGERING_MESSAGE_IDS_ATTRIBUTE, WARNINGS_ATTRIBUTE, ITERATION_STATUS_ATTRIBUTE, SIMULATION_STATE_ATTRIBUTE,
    START_TIME_ATTRIBUTE, END_TIME_ATTRIBUTE, VALUE_ATTRIBUTE, DESCRIPTION_ATTRIBUTE, NAME_ATTRIBUTE,
    DEFAULT_TYPE, DEFAULT_TIMESTAMP, DEFAULT_SIMULATION_ID, DEFAULT_SOURCE_PROCESS_ID, DEFAULT_MESSAGE_ID,
    DEFAULT_EPOCH_NUMBER, DEFAULT_LAST_UPDATED_IN_EPOCH, DEFAULT_TRIGGERING_MESSAGE_IDS, DEFAULT_WARNINGS,
    DEFAULT_ITERATION_STATUS, DEFAULT_SIMULATION_STATE, DEFAULT_START_TIME, DEFAULT_END_TIME, DEFAULT_VALUE,
    DEFAULT_DESCRIPTION, DEFAULT_NAME, DEFAULT_EXTRA_ATTRIBUTES,
    FULL_JSON, ALTERNATE_JSON
)

DEFAULT_TYPE = "General"
FULL_JSON = {**FULL_JSON, "Type": DEFAULT_TYPE}
ALTERNATE_JSON = {**ALTERNATE_JSON, "Type": DEFAULT_TYPE}


class TestGeneralMessage(unittest.TestCase):
    """Unit tests for the GeneralMessage class."""

    def test_message_type(self):
        """Unit test for the GeneralMessage type."""
        self.assertEqual(tools.messages.GeneralMessage.CLASS_MESSAGE_TYPE, "General")
        self.assertEqual(tools.messages.GeneralMessage.MESSAGE_TYPE_CHECK, False)

    def test_message_creation(self):
        """Unit test for creating instances of GeneralMessage class."""

        # When message is created without a Timestamp attribute,
        # the current time in millisecond precision is used as the default value.
        utcnow1 = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        utcnow1 -= datetime.timedelta(microseconds=utcnow1.microsecond % 1000)
        message_full = tools.messages.GeneralMessage(**FULL_JSON)
        message_timestamp = to_utc_datetime_object(message_full.timestamp)
        utcnow2 = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        utcnow1 -= datetime.timedelta(microseconds=utcnow2.microsecond % 1000)

        self.assertGreaterEqual(message_timestamp, utcnow1)
        self.assertLessEqual(message_timestamp, utcnow2)
        self.assertEqual(message_full.message_type, DEFAULT_TYPE)
        self.assertEqual(message_full.simulation_id, DEFAULT_SIMULATION_ID)
        self.assertEqual(message_full.general_attributes[SOURCE_PROCESS_ID_ATTRIBUTE], DEFAULT_SOURCE_PROCESS_ID)
        self.assertEqual(message_full.general_attributes[MESSAGE_ID_ATTRIBUTE], DEFAULT_MESSAGE_ID)
        self.assertEqual(message_full.general_attributes[EPOCH_NUMBER_ATTRIBUTE], DEFAULT_EPOCH_NUMBER)
        self.assertEqual(message_full.general_attributes[LAST_UPDATED_IN_EPOCH_ATTRIBUTE],
                         DEFAULT_LAST_UPDATED_IN_EPOCH)
        self.assertEqual(message_full.general_attributes[TRIGGERING_MESSAGE_IDS_ATTRIBUTE],
                         DEFAULT_TRIGGERING_MESSAGE_IDS)
        self.assertEqual(message_full.general_attributes[WARNINGS_ATTRIBUTE], DEFAULT_WARNINGS)
        self.assertEqual(message_full.general_attributes[ITERATION_STATUS_ATTRIBUTE], DEFAULT_ITERATION_STATUS)
        self.assertEqual(message_full.general_attributes[SIMULATION_STATE_ATTRIBUTE], DEFAULT_SIMULATION_STATE)
        self.assertEqual(message_full.general_attributes[START_TIME_ATTRIBUTE], DEFAULT_START_TIME)
        self.assertEqual(message_full.general_attributes[END_TIME_ATTRIBUTE], DEFAULT_END_TIME)
        self.assertEqual(message_full.general_attributes[VALUE_ATTRIBUTE], DEFAULT_VALUE)
        self.assertEqual(message_full.general_attributes[DESCRIPTION_ATTRIBUTE], DEFAULT_DESCRIPTION)
        self.assertEqual(message_full.general_attributes[NAME_ATTRIBUTE], DEFAULT_NAME)
        for extra_attribute_name, extra_attribute_value in DEFAULT_EXTRA_ATTRIBUTES.items():
            self.assertEqual(message_full.general_attributes[extra_attribute_name], extra_attribute_value)

        # Test with explicitely set timestamp
        message_timestamped = tools.messages.GeneralMessage(Timestamp=DEFAULT_TIMESTAMP, **FULL_JSON)
        self.assertEqual(message_timestamped.timestamp, DEFAULT_TIMESTAMP)
        self.assertEqual(message_timestamped.simulation_id, DEFAULT_SIMULATION_ID)
        self.assertEqual(message_timestamped.message_type, DEFAULT_TYPE)
        self.assertEqual(message_timestamped.general_attributes[SOURCE_PROCESS_ID_ATTRIBUTE], DEFAULT_SOURCE_PROCESS_ID)
        self.assertEqual(message_timestamped.general_attributes[MESSAGE_ID_ATTRIBUTE], DEFAULT_MESSAGE_ID)
        self.assertEqual(message_timestamped.general_attributes[EPOCH_NUMBER_ATTRIBUTE], DEFAULT_EPOCH_NUMBER)
        self.assertEqual(message_timestamped.general_attributes[LAST_UPDATED_IN_EPOCH_ATTRIBUTE],
                         DEFAULT_LAST_UPDATED_IN_EPOCH)
        self.assertEqual(message_timestamped.general_attributes[TRIGGERING_MESSAGE_IDS_ATTRIBUTE],
                         DEFAULT_TRIGGERING_MESSAGE_IDS)
        self.assertEqual(message_timestamped.general_attributes[WARNINGS_ATTRIBUTE], DEFAULT_WARNINGS)
        self.assertEqual(message_timestamped.general_attributes[ITERATION_STATUS_ATTRIBUTE], DEFAULT_ITERATION_STATUS)
        self.assertEqual(message_timestamped.general_attributes[SIMULATION_STATE_ATTRIBUTE], DEFAULT_SIMULATION_STATE)
        self.assertEqual(message_timestamped.general_attributes[START_TIME_ATTRIBUTE], DEFAULT_START_TIME)
        self.assertEqual(message_timestamped.general_attributes[END_TIME_ATTRIBUTE], DEFAULT_END_TIME)
        self.assertEqual(message_timestamped.general_attributes[VALUE_ATTRIBUTE], DEFAULT_VALUE)
        self.assertEqual(message_timestamped.general_attributes[DESCRIPTION_ATTRIBUTE], DEFAULT_DESCRIPTION)
        self.assertEqual(message_timestamped.general_attributes[NAME_ATTRIBUTE], DEFAULT_NAME)
        for extra_attribute_name, extra_attribute_value in DEFAULT_EXTRA_ATTRIBUTES.items():
            self.assertEqual(message_timestamped.general_attributes[extra_attribute_name], extra_attribute_value)

        # Test message creation without the optional attributes.
        stripped_json = copy.deepcopy(FULL_JSON)
        stripped_json.pop(SOURCE_PROCESS_ID_ATTRIBUTE)
        stripped_json.pop(MESSAGE_ID_ATTRIBUTE)
        stripped_json.pop(EPOCH_NUMBER_ATTRIBUTE)
        stripped_json.pop(LAST_UPDATED_IN_EPOCH_ATTRIBUTE)
        stripped_json.pop(TRIGGERING_MESSAGE_IDS_ATTRIBUTE)
        stripped_json.pop(WARNINGS_ATTRIBUTE)
        stripped_json.pop(ITERATION_STATUS_ATTRIBUTE)
        stripped_json.pop(SIMULATION_STATE_ATTRIBUTE)
        stripped_json.pop(START_TIME_ATTRIBUTE)
        stripped_json.pop(END_TIME_ATTRIBUTE)
        stripped_json.pop(VALUE_ATTRIBUTE)
        stripped_json.pop(DESCRIPTION_ATTRIBUTE)
        stripped_json.pop(NAME_ATTRIBUTE)
        for extra_attribute_name in DEFAULT_EXTRA_ATTRIBUTES:
            stripped_json.pop(extra_attribute_name)
        message_stripped = tools.messages.GeneralMessage(Timestamp=DEFAULT_TIMESTAMP, **stripped_json)
        self.assertEqual(message_stripped.timestamp, DEFAULT_TIMESTAMP)
        self.assertEqual(message_stripped.message_type, DEFAULT_TYPE)
        self.assertEqual(message_stripped.simulation_id, DEFAULT_SIMULATION_ID)
        self.assertEqual(message_stripped.general_attributes, {})

    def test_message_json(self):
        """Unit test for testing that the json from a message has correct attributes."""
        message_full_json = tools.messages.GeneralMessage(**FULL_JSON).json()

        self.assertIn(MESSAGE_TYPE_ATTRIBUTE, message_full_json)
        self.assertIn(SIMULATION_ID_ATTRIBUTE, message_full_json)
        self.assertIn(SOURCE_PROCESS_ID_ATTRIBUTE, message_full_json)
        self.assertIn(MESSAGE_ID_ATTRIBUTE, message_full_json)
        self.assertIn(TIMESTAMP_ATTRIBUTE, message_full_json)
        self.assertIn(EPOCH_NUMBER_ATTRIBUTE, message_full_json)
        self.assertIn(LAST_UPDATED_IN_EPOCH_ATTRIBUTE, message_full_json)
        self.assertIn(TRIGGERING_MESSAGE_IDS_ATTRIBUTE, message_full_json)
        self.assertIn(WARNINGS_ATTRIBUTE, message_full_json)
        self.assertIn(ITERATION_STATUS_ATTRIBUTE, message_full_json)
        self.assertIn(SIMULATION_STATE_ATTRIBUTE, message_full_json)
        self.assertIn(START_TIME_ATTRIBUTE, message_full_json)
        self.assertIn(END_TIME_ATTRIBUTE, message_full_json)
        self.assertIn(VALUE_ATTRIBUTE, message_full_json)
        self.assertIn(DESCRIPTION_ATTRIBUTE, message_full_json)
        self.assertIn(NAME_ATTRIBUTE, message_full_json)
        for extra_attribute_name in DEFAULT_EXTRA_ATTRIBUTES:
            self.assertIn(extra_attribute_name, message_full_json)
        self.assertEqual(len(message_full_json), 18)

    def test_message_bytes(self):
        """Unit test for testing that the bytes conversion works correctly."""
        # Convert to bytes and back to Message instance
        message_full = tools.messages.GeneralMessage(**FULL_JSON)
        message_copy = tools.messages.GeneralMessage(**json.loads(message_full.bytes().decode("UTF-8")))

        self.assertEqual(message_copy.timestamp, message_full.timestamp)
        self.assertEqual(message_copy.simulation_id, message_full.simulation_id)
        general_attributes_original = message_full.general_attributes
        general_attributes_copy = message_copy.general_attributes
        self.assertEqual(len(general_attributes_copy), len(general_attributes_original))
        for attribute_name in general_attributes_original:
            self.assertEqual(general_attributes_copy[attribute_name], general_attributes_original[attribute_name])

    def test_message_equals(self):
        """Unit test for testing if the __eq__ comparison works correctly."""
        message_full = tools.messages.GeneralMessage(Timestamp=DEFAULT_TIMESTAMP, **FULL_JSON)
        message_copy = tools.messages.GeneralMessage(Timestamp=DEFAULT_TIMESTAMP, **FULL_JSON)
        message_alternate = tools.messages.GeneralMessage.from_json(ALTERNATE_JSON)

        self.assertEqual(message_copy, message_full)
        self.assertNotEqual(message_copy, message_alternate)

        attributes = [
            "simulation_id",
            "timestamp",
            "general_attributes"
        ]
        for attribute_name in attributes:
            with self.subTest(attribute=attribute_name):
                setattr(message_copy, attribute_name, getattr(message_alternate, attribute_name))
                self.assertNotEqual(message_copy, message_full)
                setattr(message_copy, attribute_name, getattr(message_full, attribute_name))
                self.assertEqual(message_copy, message_full)

    def test_invalid_values(self):
        """Unit tests for testing that invalid attribute values are recognized."""
        message_full = tools.messages.GeneralMessage(**FULL_JSON)
        message_full_json = message_full.json()

        invalid_attribute_exceptions = {
            MESSAGE_TYPE_ATTRIBUTE: tools.exceptions.messages.MessageTypeError,
            SIMULATION_ID_ATTRIBUTE: tools.exceptions.messages.MessageDateError
        }
        invalid_attribute_values = {
            MESSAGE_TYPE_ATTRIBUTE: [12, True, []],
            SIMULATION_ID_ATTRIBUTE: ["simulation-id", 12, "2020-07-31T24:11:11.123Z", ""],
        }
        for invalid_attribute in invalid_attribute_exceptions:
            if invalid_attribute != TIMESTAMP_ATTRIBUTE:
                json_invalid_attribute = copy.deepcopy(message_full_json)
                json_invalid_attribute.pop(invalid_attribute)
                with self.subTest(attribute=invalid_attribute):
                    with self.assertRaises(invalid_attribute_exceptions[invalid_attribute]):
                        tools.messages.GeneralMessage(**json_invalid_attribute)

            for invalid_value in invalid_attribute_values[invalid_attribute]:
                json_invalid_attribute = copy.deepcopy(message_full_json)
                json_invalid_attribute[invalid_attribute] = invalid_value
                with self.subTest(attribute=invalid_attribute, value=invalid_value):
                    with self.assertRaises((ValueError, invalid_attribute_exceptions[invalid_attribute])):
                        tools.messages.GeneralMessage(**json_invalid_attribute)

        message_full.general_attributes = {}
        self.assertEqual(len(message_full.json()), 3)
        self.assertEqual(message_full.general_attributes, {})
        self.assertRaises(
            tools.exceptions.messages.MessageValueError,
            setattr, *(message_full, "general_attributes", []))
        self.assertRaises(
            tools.exceptions.messages.MessageValueError,
            setattr, *(message_full, "general_attributes", "general"))


if __name__ == '__main__':
    unittest.main()
