# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Unit test for the ResultMessage class."""

import copy
import datetime
import json
import unittest

import tools.exceptions.messages
import tools.messages
from tools.datetime_tools import to_utc_datetime_object

from tools.tests.messages_common import (
    MESSAGE_TYPE_ATTRIBUTE, TIMESTAMP_ATTRIBUTE, SIMULATION_ID_ATTRIBUTE, SOURCE_PROCESS_ID_ATTRIBUTE,
    MESSAGE_ID_ATTRIBUTE, EPOCH_NUMBER_ATTRIBUTE, LAST_UPDATED_IN_EPOCH_ATTRIBUTE, TRIGGERING_MESSAGE_IDS_ATTRIBUTE,
    WARNINGS_ATTRIBUTE, ITERATION_STATUS_ATTRIBUTE, SIMULATION_STATE_ATTRIBUTE, START_TIME_ATTRIBUTE,
    END_TIME_ATTRIBUTE, VALUE_ATTRIBUTE, DESCRIPTION_ATTRIBUTE, NAME_ATTRIBUTE,
    DEFAULT_TYPE, DEFAULT_TIMESTAMP, DEFAULT_SIMULATION_ID, DEFAULT_SOURCE_PROCESS_ID, DEFAULT_MESSAGE_ID,
    DEFAULT_EPOCH_NUMBER, DEFAULT_LAST_UPDATED_IN_EPOCH, DEFAULT_TRIGGERING_MESSAGE_IDS, DEFAULT_WARNINGS,
    DEFAULT_ITERATION_STATUS, DEFAULT_SIMULATION_STATE, DEFAULT_START_TIME, DEFAULT_END_TIME, DEFAULT_VALUE,
    DEFAULT_DESCRIPTION, DEFAULT_NAME, DEFAULT_EXTRA_ATTRIBUTES,
    FULL_JSON, ALTERNATE_JSON
)


class TestResultMessage(unittest.TestCase):
    """Unit tests for the ResultMessage class."""

    def test_message_type(self):
        """Unit test for the ResultMessage type."""
        self.assertEqual(tools.messages.ResultMessage.CLASS_MESSAGE_TYPE, "Result")
        self.assertEqual(tools.messages.ResultMessage.MESSAGE_TYPE_CHECK, False)

    def test_message_creation(self):
        """Unit test for creating instances of ResultMessage class."""

        # When message is created without a Timestamp attribute,
        # the current time in millisecond precision is used as the default value.
        utcnow1 = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        utcnow1 -= datetime.timedelta(microseconds=utcnow1.microsecond % 1000)
        message_full = tools.messages.ResultMessage(**FULL_JSON)
        message_timestamp = to_utc_datetime_object(message_full.timestamp)
        utcnow2 = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        utcnow1 -= datetime.timedelta(microseconds=utcnow2.microsecond % 1000)

        self.assertGreaterEqual(message_timestamp, utcnow1)
        self.assertLessEqual(message_timestamp, utcnow2)
        self.assertEqual(message_full.message_type, DEFAULT_TYPE)
        self.assertEqual(message_full.simulation_id, DEFAULT_SIMULATION_ID)
        self.assertEqual(message_full.source_process_id, DEFAULT_SOURCE_PROCESS_ID)
        self.assertEqual(message_full.message_id, DEFAULT_MESSAGE_ID)
        self.assertEqual(message_full.epoch_number, DEFAULT_EPOCH_NUMBER)
        self.assertEqual(message_full.last_updated_in_epoch, DEFAULT_LAST_UPDATED_IN_EPOCH)
        self.assertEqual(message_full.triggering_message_ids, DEFAULT_TRIGGERING_MESSAGE_IDS)
        self.assertEqual(message_full.warnings, DEFAULT_WARNINGS)
        self.assertEqual(message_full.iteration_status, DEFAULT_ITERATION_STATUS)
        self.assertEqual(message_full.result_values[SIMULATION_STATE_ATTRIBUTE], DEFAULT_SIMULATION_STATE)
        self.assertEqual(message_full.result_values[START_TIME_ATTRIBUTE], DEFAULT_START_TIME)
        self.assertEqual(message_full.result_values[END_TIME_ATTRIBUTE], DEFAULT_END_TIME)
        self.assertEqual(message_full.result_values[VALUE_ATTRIBUTE], DEFAULT_VALUE)
        self.assertEqual(message_full.result_values[DESCRIPTION_ATTRIBUTE], DEFAULT_DESCRIPTION)
        self.assertEqual(message_full.result_values[NAME_ATTRIBUTE], DEFAULT_NAME)
        for extra_attribute_name, extra_attribute_value in DEFAULT_EXTRA_ATTRIBUTES.items():
            self.assertEqual(message_full.result_values[extra_attribute_name], extra_attribute_value)

        # Test with explicitely set timestamp
        message_timestamped = tools.messages.ResultMessage(Timestamp=DEFAULT_TIMESTAMP, **FULL_JSON)
        self.assertEqual(message_timestamped.timestamp, DEFAULT_TIMESTAMP)
        self.assertEqual(message_timestamped.message_type, DEFAULT_TYPE)
        self.assertEqual(message_timestamped.simulation_id, DEFAULT_SIMULATION_ID)
        self.assertEqual(message_timestamped.source_process_id, DEFAULT_SOURCE_PROCESS_ID)
        self.assertEqual(message_timestamped.message_id, DEFAULT_MESSAGE_ID)
        self.assertEqual(message_timestamped.epoch_number, DEFAULT_EPOCH_NUMBER)
        self.assertEqual(message_timestamped.last_updated_in_epoch, DEFAULT_LAST_UPDATED_IN_EPOCH)
        self.assertEqual(message_timestamped.triggering_message_ids, DEFAULT_TRIGGERING_MESSAGE_IDS)
        self.assertEqual(message_timestamped.warnings, DEFAULT_WARNINGS)
        self.assertEqual(message_timestamped.iteration_status, DEFAULT_ITERATION_STATUS)
        self.assertEqual(message_timestamped.result_values[SIMULATION_STATE_ATTRIBUTE], DEFAULT_SIMULATION_STATE)
        self.assertEqual(message_timestamped.result_values[START_TIME_ATTRIBUTE], DEFAULT_START_TIME)
        self.assertEqual(message_timestamped.result_values[END_TIME_ATTRIBUTE], DEFAULT_END_TIME)
        self.assertEqual(message_timestamped.result_values[VALUE_ATTRIBUTE], DEFAULT_VALUE)
        self.assertEqual(message_timestamped.result_values[DESCRIPTION_ATTRIBUTE], DEFAULT_DESCRIPTION)
        self.assertEqual(message_timestamped.result_values[NAME_ATTRIBUTE], DEFAULT_NAME)
        for extra_attribute_name, extra_attribute_value in DEFAULT_EXTRA_ATTRIBUTES.items():
            self.assertEqual(message_timestamped.result_values[extra_attribute_name], extra_attribute_value)

        # Test message creation without the optional attributes.
        stripped_json = copy.deepcopy(FULL_JSON)
        stripped_json.pop(LAST_UPDATED_IN_EPOCH_ATTRIBUTE)
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
        message_stripped = tools.messages.ResultMessage(Timestamp=DEFAULT_TIMESTAMP, **stripped_json)
        self.assertEqual(message_stripped.timestamp, DEFAULT_TIMESTAMP)
        self.assertEqual(message_stripped.message_type, DEFAULT_TYPE)
        self.assertEqual(message_stripped.simulation_id, DEFAULT_SIMULATION_ID)
        self.assertEqual(message_stripped.source_process_id, DEFAULT_SOURCE_PROCESS_ID)
        self.assertEqual(message_stripped.message_id, DEFAULT_MESSAGE_ID)
        self.assertEqual(message_stripped.epoch_number, DEFAULT_EPOCH_NUMBER)
        self.assertEqual(message_stripped.last_updated_in_epoch, None)
        self.assertEqual(message_stripped.triggering_message_ids, DEFAULT_TRIGGERING_MESSAGE_IDS)
        self.assertEqual(message_stripped.warnings, None)
        self.assertEqual(message_stripped.iteration_status, None)
        self.assertEqual(message_stripped.result_values, {})

    def test_message_json(self):
        """Unit test for testing that the json from a message has correct attributes."""
        message_full_json = tools.messages.ResultMessage(**FULL_JSON).json()

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
        message_full = tools.messages.ResultMessage(**FULL_JSON)
        message_copy = tools.messages.ResultMessage(**json.loads(message_full.bytes().decode("UTF-8")))

        self.assertEqual(message_copy.timestamp, message_full.timestamp)
        self.assertEqual(message_copy.message_type, message_full.message_type)
        self.assertEqual(message_copy.simulation_id, message_full.simulation_id)
        self.assertEqual(message_copy.source_process_id, message_full.source_process_id)
        self.assertEqual(message_copy.message_id, message_full.message_id)
        self.assertEqual(message_copy.epoch_number, message_full.epoch_number)
        self.assertEqual(message_copy.last_updated_in_epoch, message_full.last_updated_in_epoch)
        self.assertEqual(message_copy.triggering_message_ids, message_full.triggering_message_ids)
        self.assertEqual(message_copy.warnings, message_full.warnings)
        self.assertEqual(message_copy.iteration_status, message_full.iteration_status)
        result_values_original = message_full.result_values
        result_values_copy = message_copy.result_values
        self.assertEqual(len(result_values_copy), len(result_values_original))
        for attribute_name in result_values_original:
            self.assertEqual(result_values_copy[attribute_name], result_values_original[attribute_name])

    def test_message_equals(self):
        """Unit test for testing if the __eq__ comparison works correctly."""
        message_full = tools.messages.ResultMessage(Timestamp=DEFAULT_TIMESTAMP, **FULL_JSON)
        message_copy = tools.messages.ResultMessage(Timestamp=DEFAULT_TIMESTAMP, **FULL_JSON)
        message_alternate = tools.messages.ResultMessage.from_json(ALTERNATE_JSON)

        self.assertEqual(message_copy, message_full)
        self.assertNotEqual(message_copy, message_alternate)

        attributes = [
            "message_type",
            "simulation_id",
            "source_process_id",
            "message_id",
            "timestamp",
            "epoch_number",
            "last_updated_in_epoch",
            "triggering_message_ids",
            "warnings",
            "iteration_status",
            "result_values"
        ]
        for attribute_name in attributes:
            with self.subTest(attribute=attribute_name):
                setattr(message_copy, attribute_name, getattr(message_alternate, attribute_name))
                self.assertNotEqual(message_copy, message_full)
                setattr(message_copy, attribute_name, getattr(message_full, attribute_name))
                self.assertEqual(message_copy, message_full)

    def test_invalid_values(self):
        """Unit tests for testing that invalid attribute values are recognized."""
        message_full = tools.messages.ResultMessage(**FULL_JSON)
        message_full_json = message_full.json()

        allowed_warning_types = [
            "warning.convergence",
            "warning.input",
            "warning.input.range",
            "warning.input.unreliable",
            "warning.internal",
            "warning.other"
        ]
        message_full.warnings = allowed_warning_types
        self.assertEqual(message_full.warnings, allowed_warning_types)
        message_full.warnings = []
        self.assertEqual(message_full.warnings, None)
        for allowed_warning_str in allowed_warning_types:
            message_full.warnings = [allowed_warning_str]
            self.assertEqual(message_full.warnings, [allowed_warning_str])

        allowed_iterations_status = [
            "intermediate",
            "final"
        ]
        message_full.iteration_status = None
        self.assertEqual(message_full.iteration_status, None)
        for allowed_iterations_status_str in allowed_iterations_status:
            message_full.iteration_status = allowed_iterations_status_str
            self.assertEqual(message_full.iteration_status, allowed_iterations_status_str)

        optional_attributes = [
            LAST_UPDATED_IN_EPOCH_ATTRIBUTE,
            WARNINGS_ATTRIBUTE,
            ITERATION_STATUS_ATTRIBUTE
        ]

        invalid_attribute_exceptions = {
            MESSAGE_TYPE_ATTRIBUTE: tools.exceptions.messages.MessageTypeError,
            SIMULATION_ID_ATTRIBUTE: tools.exceptions.messages.MessageDateError,
            SOURCE_PROCESS_ID_ATTRIBUTE: tools.exceptions.messages.MessageSourceError,
            MESSAGE_ID_ATTRIBUTE: tools.exceptions.messages.MessageIdError,
            TIMESTAMP_ATTRIBUTE: tools.exceptions.messages.MessageDateError,
            EPOCH_NUMBER_ATTRIBUTE: tools.exceptions.messages.MessageEpochValueError,
            LAST_UPDATED_IN_EPOCH_ATTRIBUTE: tools.exceptions.messages.MessageEpochValueError,
            TRIGGERING_MESSAGE_IDS_ATTRIBUTE: tools.exceptions.messages.MessageIdError,
            WARNINGS_ATTRIBUTE: tools.exceptions.messages.MessageValueError,
            ITERATION_STATUS_ATTRIBUTE: tools.exceptions.messages.MessageValueError
        }
        invalid_attribute_values = {
            MESSAGE_TYPE_ATTRIBUTE: [12, True, []],
            SIMULATION_ID_ATTRIBUTE: ["simulation-id", 12, "2020-07-31T24:11:11.123Z", ""],
            SOURCE_PROCESS_ID_ATTRIBUTE: [12, ""],
            MESSAGE_ID_ATTRIBUTE: [12, True, ""],
            TIMESTAMP_ATTRIBUTE: ["timestamp", 12, "2020-07-31T24:11:11.123Z", ""],
            EPOCH_NUMBER_ATTRIBUTE: [-1, "epoch", "12", ""],
            LAST_UPDATED_IN_EPOCH_ATTRIBUTE: [-1, "epoch", "12", ""],
            TRIGGERING_MESSAGE_IDS_ATTRIBUTE: [["process-12", ""], [""], []],
            WARNINGS_ATTRIBUTE: [["warning.convergence", "warning"], ["warning."], ["warning.random"]],
            ITERATION_STATUS_ATTRIBUTE: ["", "beginning", 12, []]
        }
        for invalid_attribute in invalid_attribute_exceptions:
            if invalid_attribute != TIMESTAMP_ATTRIBUTE and invalid_attribute not in optional_attributes:
                json_invalid_attribute = copy.deepcopy(message_full_json)
                json_invalid_attribute.pop(invalid_attribute)
                with self.subTest(attribute=invalid_attribute):
                    with self.assertRaises(invalid_attribute_exceptions[invalid_attribute]):
                        tools.messages.ResultMessage(**json_invalid_attribute)

            for invalid_value in invalid_attribute_values[invalid_attribute]:
                json_invalid_attribute = copy.deepcopy(message_full_json)
                json_invalid_attribute[invalid_attribute] = invalid_value
                with self.subTest(attribute=invalid_attribute, value=invalid_value):
                    with self.assertRaises((ValueError, invalid_attribute_exceptions[invalid_attribute])):
                        tools.messages.ResultMessage(**json_invalid_attribute)

        message_full.result_values = {}
        self.assertEqual(len(message_full.json()), 10)
        self.assertEqual(message_full.result_values, {})
        self.assertRaises(
            tools.exceptions.messages.MessageValueError,
            setattr, *(message_full, "result_values", []))
        self.assertRaises(
            tools.exceptions.messages.MessageValueError,
            setattr, *(message_full, "result_values", "extra"))


if __name__ == '__main__':
    unittest.main()
