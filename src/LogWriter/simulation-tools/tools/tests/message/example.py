# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Unit tests for the ExampleMessage class."""

import copy
import datetime
import json
import unittest

from tools.datetime_tools import to_utc_datetime_object
from tools.exceptions.messages import MessageValueError
from tools.message.abstract import AbstractResultMessage
from tools.message.block import QuantityArrayBlock, QuantityBlock, ValueArrayBlock, TimeSeriesBlock
from tools.message.example import ExampleMessage

EXAMPLE_MESSAGE = {
    "Type": "Example",
    "SimulationId": "2020-11-19T15:00:00.000Z",
    "SourceProcessId": "example-test",
    "MessageId": "example-test-1",
    "EpochNumber": 1,
    "TriggeringMessageIds": ["manager-1"],
    "PositiveInteger": 5,
    "EightCharacters": "someword",
    "PowerQuantity": {
        "UnitOfMeasure": "W",
        "Value": 12.3
    },
    "TimeQuantity": {
        "UnitOfMeasure": "s",
        "Value": 3600
    },
    "CurrentArray": {
        "UnitOfMeasure": "mA",
        "Values": [
            100.2,
            201.4,
            156.7
        ]
    },
    "VoltageArray": {
        "UnitOfMeasure": "V",
        "Values": [
            999.9,
            0.1,
            -999.9
        ]
    },
    "Temperature": {
        "TimeIndex": [
            "2020-10-01T00:00:00.000Z",
            "2020-10-01T01:00:00.000Z",
            "2020-10-01T02:00:00.000Z"
        ],
        "Series": {
            "PlaceA": {
                "UnitOfMeasure": "Cel",
                "Values": [
                    4.5,
                    5.6,
                    6.7
                ]
            },
            "PlaceB": {
                "UnitOfMeasure": "Cel",
                "Values": [
                    -3.1,
                    -2.2,
                    -1.3
                ]
            }
        }
    },
    "Weight": {
        "TimeIndex": [
            "2020-09-05T12:00:00.000Z",
            "2020-09-05T12:00:15.000Z"
        ],
        "Series": {
            "Cargo": {
                "UnitOfMeasure": "kg",
                "Values": [
                    123.567,
                    123.789
                ]
            }
        }
    }
}

ALTERNATE_MESSAGE = {
    **AbstractResultMessage(
        Type="Example",
        SimulationId="2020-11-20T11:22:33.444Z",
        SourceProcessId="alternate",
        MessageId="alternate-1",
        EpochNumber=2,
        TriggeringMessageIds=["manager-2", "resource-2"],
    ).json(),
    "PositiveInteger": 12,
    "PowerQuantity": 100.5,
    "CurrentArray": [
        24.5,
        34.6
    ],
    "Temperature": TimeSeriesBlock(
        TimeIndex=[
            "2020-07-01T13:00:00.000Z",
            "2020-07-02T15:06:16.111Z",
            "2020-07-03T17:12:32.222Z"
        ],
        Series={
            "PlaceA": ValueArrayBlock(
                UnitOfMeasure="Cel",
                Values=[
                    -15.1,
                    -16.7,
                    -4.3
                ]
            ),
            "PlaceB": ValueArrayBlock(
                UnitOfMeasure="Cel",
                Values=[
                    23.7,
                    22.6,
                    21.5
                ]
            )
        }
    ).json()
}


class TestExampleMessage(unittest.TestCase):
    """Unit tests for the ExampleMessage class. Only attributes added in ExampleMessage are tested."""

    def test_message_type(self):
        """Unit test for the ExampleMessage type."""
        self.assertEqual(ExampleMessage.CLASS_MESSAGE_TYPE, "Example")
        self.assertEqual(ExampleMessage.MESSAGE_TYPE_CHECK, True)

    def test_message_creation(self):
        """Unit test for creating instances of ExampleMessage class."""

        # When message is created without a Timestamp attribute,
        # the current time in millisecond precision is used as the default value.
        utcnow1 = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        utcnow1 -= datetime.timedelta(microseconds=utcnow1.microsecond % 1000)
        example_message = ExampleMessage(**EXAMPLE_MESSAGE)
        message_timestamp = to_utc_datetime_object(example_message.timestamp)
        utcnow2 = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        utcnow1 -= datetime.timedelta(microseconds=utcnow2.microsecond % 1000)

        # the AbstractResult attributes
        self.assertGreaterEqual(message_timestamp, utcnow1)
        self.assertLessEqual(message_timestamp, utcnow2)
        self.assertEqual(example_message.message_type, EXAMPLE_MESSAGE["Type"])
        self.assertEqual(example_message.simulation_id, EXAMPLE_MESSAGE["SimulationId"])
        self.assertEqual(example_message.source_process_id, EXAMPLE_MESSAGE["SourceProcessId"])
        self.assertEqual(example_message.message_id, EXAMPLE_MESSAGE["MessageId"])
        self.assertEqual(example_message.epoch_number, EXAMPLE_MESSAGE["EpochNumber"])
        self.assertEqual(example_message.triggering_message_ids, EXAMPLE_MESSAGE["TriggeringMessageIds"])
        self.assertIsNone(example_message.last_updated_in_epoch)
        self.assertIsNone(example_message.warnings)

        # the attributes added in ExampleMessage
        self.assertEqual(example_message.positive_integer, EXAMPLE_MESSAGE["PositiveInteger"])
        self.assertEqual(example_message.eight_characters, EXAMPLE_MESSAGE["EightCharacters"])

        self.assertEqual(example_message.power_quantity.unit_of_measure,
                         EXAMPLE_MESSAGE["PowerQuantity"]["UnitOfMeasure"])
        self.assertEqual(example_message.power_quantity.value, EXAMPLE_MESSAGE["PowerQuantity"]["Value"])
        self.assertIsNotNone(example_message.time_quantity)
        time_quantity = (
            QuantityBlock(Value=0.0, UnitOfMeasure="s") if example_message.time_quantity is None
            else example_message.time_quantity)
        self.assertEqual(time_quantity.unit_of_measure,
                         EXAMPLE_MESSAGE["TimeQuantity"]["UnitOfMeasure"])
        self.assertEqual(time_quantity.value, EXAMPLE_MESSAGE["TimeQuantity"]["Value"])

        self.assertEqual(example_message.current_array.unit_of_measure,
                         EXAMPLE_MESSAGE["CurrentArray"]["UnitOfMeasure"])
        self.assertEqual(example_message.current_array.values, EXAMPLE_MESSAGE["CurrentArray"]["Values"])
        voltage_array = (
            QuantityArrayBlock(Values=[0.0], UnitOfMeasure="V") if example_message.voltage_array is None
            else example_message.voltage_array)
        self.assertEqual(voltage_array.unit_of_measure,
                         EXAMPLE_MESSAGE["VoltageArray"]["UnitOfMeasure"])
        self.assertEqual(voltage_array.values, EXAMPLE_MESSAGE["VoltageArray"]["Values"])

        self.assertEqual(example_message.temperature.time_index, EXAMPLE_MESSAGE["Temperature"]["TimeIndex"])
        for series_name, series_values in EXAMPLE_MESSAGE["Temperature"]["Series"].items():
            with self.subTest(series_name=series_name):
                self.assertEqual(example_message.temperature.series[series_name].unit_of_measure,
                                 series_values["UnitOfMeasure"])
                self.assertEqual(example_message.temperature.series[series_name].values,
                                 series_values["Values"])
        weight = (
            TimeSeriesBlock(
                TimeIndex=["1970-01-01T00:00:00Z"],
                Series={"temp": ValueArrayBlock(Values=[0.0], UnitOfMeasure="kg")})
            if example_message.weight is None
            else example_message.weight)
        self.assertEqual(weight.time_index, EXAMPLE_MESSAGE["Weight"]["TimeIndex"])
        for series_name, series_values in EXAMPLE_MESSAGE["Weight"]["Series"].items():
            with self.subTest(series_name=series_name):
                self.assertEqual(weight.series[series_name].unit_of_measure,
                                 series_values["UnitOfMeasure"])
                self.assertEqual(weight.series[series_name].values,
                                 series_values["Values"])

        # Test message creation without the optional attributes.
        stripped_json = copy.deepcopy(EXAMPLE_MESSAGE)
        stripped_json.pop("EightCharacters")
        stripped_json.pop("TimeQuantity")
        stripped_json.pop("VoltageArray")
        stripped_json.pop("Weight")
        message_stripped = ExampleMessage(Timestamp=example_message.timestamp, **stripped_json)
        self.assertEqual(message_stripped.timestamp, example_message.timestamp)
        self.assertEqual(message_stripped.message_type, example_message.message_type)
        self.assertEqual(message_stripped.simulation_id, example_message.simulation_id)
        self.assertEqual(message_stripped.source_process_id, example_message.source_process_id)
        self.assertEqual(message_stripped.message_id, example_message.message_id)
        self.assertEqual(message_stripped.epoch_number, example_message.epoch_number)
        self.assertEqual(message_stripped.triggering_message_ids, example_message.triggering_message_ids)
        self.assertEqual(message_stripped.positive_integer, example_message.positive_integer)
        self.assertEqual(message_stripped.power_quantity, example_message.power_quantity)
        self.assertEqual(message_stripped.current_array, example_message.current_array)
        self.assertEqual(message_stripped.temperature, example_message.temperature)
        self.assertIsNone(message_stripped.eight_characters)
        self.assertIsNone(message_stripped.time_quantity)
        self.assertIsNone(message_stripped.voltage_array)
        self.assertIsNone(message_stripped.weight)

    def test_message_json(self):
        """Unit test for testing that the json from a message has correct attributes."""
        message_json = {
            **EXAMPLE_MESSAGE,
            "Timestamp": "2020-01-01T00:00:00.000Z"
        }
        message_json_copy = ExampleMessage(**message_json).json()
        self.assertEqual(message_json_copy, message_json)

    def test_message_bytes(self):
        """Unit test for testing that the bytes conversion works correctly."""
        # Convert to bytes and back to Message instance
        message_original = ExampleMessage(**EXAMPLE_MESSAGE)
        message_copy = ExampleMessage(**json.loads(message_original.bytes().decode("UTF-8")))

        self.assertEqual(message_copy.positive_integer, message_original.positive_integer)
        self.assertEqual(message_copy.eight_characters, message_original.eight_characters)
        self.assertEqual(message_copy.power_quantity, message_original.power_quantity)
        self.assertEqual(message_copy.time_quantity, message_original.time_quantity)
        self.assertEqual(message_copy.current_array, message_original.current_array)
        self.assertEqual(message_copy.voltage_array, message_original.voltage_array)
        self.assertEqual(message_copy.temperature, message_original.temperature)
        self.assertEqual(message_copy.weight, message_original.weight)

    def test_message_equals(self):
        """Unit test for testing if the __eq__ comparison works correctly."""
        timestamp = "2018-11-11T15:15:15.987Z"
        message_original = ExampleMessage(Timestamp=timestamp, **EXAMPLE_MESSAGE)
        message_copy = ExampleMessage(Timestamp=timestamp, **EXAMPLE_MESSAGE)
        message_alternate = ExampleMessage(**ALTERNATE_MESSAGE)

        self.assertEqual(message_copy, message_original)
        self.assertNotEqual(message_copy, message_alternate)

        attributes = [
            "simulation_id",
            "source_process_id",
            "message_id",
            "timestamp",
            "epoch_number",
            "triggering_message_ids",
            "positive_integer",
            "eight_characters",
            "power_quantity",
            "time_quantity",
            "current_array",
            "voltage_array",
            "temperature",
            "weight"
        ]
        for attribute_name in attributes:
            with self.subTest(attribute=attribute_name):
                setattr(message_copy, attribute_name, getattr(message_alternate, attribute_name))
                self.assertNotEqual(message_copy, message_original)
                setattr(message_copy, attribute_name, getattr(message_original, attribute_name))
                self.assertEqual(message_copy, message_original)

    def test_invalid_values(self):
        """Unit tests for testing that invalid attribute values are recognized."""
        example_message = ExampleMessage(**EXAMPLE_MESSAGE)
        message_json = example_message.json()

        optional_attributes = [
            "EightCharacters",
            "TimeQuantity",
            "VoltageArray",
            "Weight"
        ]

        invalid_attribute_exceptions = {
            "PositiveInteger": MessageValueError,
            "EightCharacters": MessageValueError,
            "PowerQuantity": MessageValueError,
            "TimeQuantity": MessageValueError,
            "CurrentArray": MessageValueError,
            "VoltageArray": MessageValueError,
            "Temperature": MessageValueError,
            "Weight": MessageValueError,
        }
        invalid_attribute_values = {
            "PositiveInteger": ["hello", 0, -1, -55, 23.4, [], ["hello"]],
            "EightCharacters": [12, 456.234, "eight", "1234567", "123456789", [], ["hello"]],
            "PowerQuantity": ["hello", [], ["hello"], {"UnitOfMeasure": "MW", "Value": 12.3},
                              QuantityBlock(UnitOfMeasure="A", Value=0.1)],
            "TimeQuantity": [-5, 86400.1, "hello", [], ["hello"], {"UnitOfMeasure": "h", "Value": 12.3},
                             QuantityBlock(UnitOfMeasure="min", Value=0.1)],
            "CurrentArray": [12, "hello", ["hello"], {"UnitOfMeasure": "mA", "Values": "12.3"},
                             QuantityArrayBlock(UnitOfMeasure="A", Values=[12.3])],
            "VoltageArray": [12, "hello", ["hello"], {"UnitOfMeasure": "V", "Values": "12.3"},
                             QuantityArrayBlock(UnitOfMeasure="mV", Values=[12.3]),
                             QuantityArrayBlock(UnitOfMeasure="V", Values=[1000.0]),
                             QuantityArrayBlock(UnitOfMeasure="V", Values=[-1000.0])],
            "Temperature": [
                12, "hello", [], ["hello"],
                {"TimeIndex": [], "Series": {}},
                {"TimeIndex": [], "Series": {
                    "PlaceA": {"UnitOfMeasure": "Cel", "Values": []},
                    "PlaceB": {"UnitOfMeasure": "Cel", "Values": []}
                }},
                {"TimeIndex": ["2000-13-01T00:00:00Z"], "Series": {
                    "PlaceA": {"UnitOfMeasure": "Cel", "Values": [12.3]},
                    "PlaceB": {"UnitOfMeasure": "Cel", "Values": [1.2]}
                }},
                {"TimeIndex": ["2000-01-01T00:00:00Z"], "Series": {
                    "PlaceA": {"UnitOfMeasure": "Cel", "Values": [12.3]},
                    "PlaceB": {"UnitOfMeasure": "Cel", "Values": [1.2]}
                }},
                {"TimeIndex": ["2000-01-01T00:00:00Z", "2000-01-02T00:00:00Z", "2000-01-03T00:00:00Z"], "Series": {
                    "PlaceA": {"UnitOfMeasure": "Cel", "Values": [12.3, 12.4, 12.5]}
                }},
                {"TimeIndex": ["2000-01-01T00:00:00Z", "2000-01-02T00:00:00Z", "2000-01-03T00:00:00Z"], "Series": {
                    "PlaceA": {"UnitOfMeasure": "Cel", "Values": [12.3, 12.4, 12.5]},
                    "PlaceB": {"UnitOfMeasure": "[degF]", "Values": [1.2, 1.3, 1.4]}
                }},
                {"TimeIndex": ["2000-01-01T00:00:00Z", "2000-01-02T00:00:00Z", "2000-01-03T00:00:00Z"], "Series": {
                    "PlaceA": {"UnitOfMeasure": "Cel", "Values": [12.3, 12.4, 12.5]},
                    "PlaceC": {"UnitOfMeasure": "Cel", "Values": [1.2, 1.3, 1.4]}
                }},
                TimeSeriesBlock(
                    TimeIndex=["2000-01-01T00:00:00Z", "2000-01-02T00:00:00Z", "2000-01-03T00:00:00Z"],
                    Series={
                        "PlaceA": ValueArrayBlock(UnitOfMeasure="Cel", Values=[12.3, 12.4, 12.5]),
                        "PlaceB": ValueArrayBlock(UnitOfMeasure="Cel", Values=[13.3, 14.4, 15.5]),
                        "PlaceC": ValueArrayBlock(UnitOfMeasure="Cel", Values=[1.3, 1.4, 1.5])
                    }
                )
            ],
            "Weight": [
                12, "hello", [], ["hello"],
                {"TimeIndex": [], "Series": {}},
                {"TimeIndex": [], "Series": {
                    "Test": {"UnitOfMeasure": "m", "Values": []}
                }},
                {"TimeIndex": ["2000-13-01T00:00:00Z"], "Series": {
                    "Test": {"UnitOfMeasure": "m", "Values": [12.3]}
                }},
                TimeSeriesBlock(
                    TimeIndex=["2000-01-01T00:00:00Z", "2000-01-02T00:00:00Z", "2000-01-03T00:00:00Z"],
                    Series={
                        "Cargo1": ValueArrayBlock(UnitOfMeasure="kg", Values=[12.3, 12.4, 12.5]),
                        "Cargo2": ValueArrayBlock(UnitOfMeasure="g", Values=[13.3, 14.4, 15.5]),
                        "Cargo3": ValueArrayBlock(UnitOfMeasure="mg", Values=[1.3, 1.4, 1.5])
                    }
                )
            ]
        }

        for invalid_attribute in invalid_attribute_exceptions:
            if invalid_attribute not in optional_attributes:
                json_invalid_attribute = copy.deepcopy(message_json)
                json_invalid_attribute.pop(invalid_attribute)
                with self.subTest(invalid_attribute=invalid_attribute):
                    with self.assertRaises(invalid_attribute_exceptions[invalid_attribute]):
                        ExampleMessage(**json_invalid_attribute)

            for invalid_value in invalid_attribute_values[invalid_attribute]:
                json_invalid_attribute = copy.deepcopy(message_json)
                json_invalid_attribute[invalid_attribute] = invalid_value
                with self.subTest(invalid_attribute=invalid_attribute, value=invalid_value):
                    with self.assertRaises((ValueError, invalid_attribute_exceptions[invalid_attribute])):
                        ExampleMessage(**json_invalid_attribute)


if __name__ == '__main__':
    unittest.main()
