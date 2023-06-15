# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Unit tests for the classes related to the TimeSeriesBlock."""

import datetime
import json
import random
import string
from typing import Dict, Generator, List, Union, cast
import unittest

from tools.datetime_tools import to_iso_format_datetime_string
from tools.exceptions.messages import MessageDateError, MessageValueError, MessageUnitValueError
from tools.message.unit import UnitCode
from tools.message.block import ValueArrayBlock, TimeSeriesBlock, QuantityArrayBlock


def get_unit_code() -> Generator[str, None, None]:
    """Returns a unit code."""
    unit_codes = ["m", "V", "A", "W", "kg"]
    while True:
        yield unit_codes[random.randint(0, len(unit_codes) - 1)]


def get_attribute_name() -> Generator[str, None, None]:
    """Returns an attribute name."""
    letters = string.ascii_lowercase
    while True:
        attribute_name = ""
        for _ in range(8):
            attribute_name += letters[random.randint(0, len(letters) - 1)]
        yield attribute_name.capitalize()


def generate_timeseries_values(unit_code: str, n_values: int) \
        -> Dict[str, Union[str, List[int], List[float], List[bool], List[str]]]:
    """Generates a new timeseries dictionary."""
    value_types = [int, float, bool, str]
    value_type = value_types[random.randint(0, len(value_types) - 1)]
    if isinstance(value_type, int):
        values = [random.randint(-1000, 1000) for _ in range(n_values)]
    elif isinstance(value_type, float):
        values = [random.uniform(-1000.0, 1000.0) for _ in range(n_values)]
    elif isinstance(value_type, bool):
        values = [random.random() >= 0.5 for _ in range(n_values)]
    else:
        values = [next(get_attribute_name()) for _ in range(n_values)]

    return {
        "UnitOfMeasure": unit_code,
        "Values": values
    }


def generate_timeseries_block(start_time: datetime.datetime, n_series: int, series_length: int) -> dict:
    """Return a dictionary for time series block."""
    timeseries_block = {
        "TimeIndex": [],
        "Series": {}
    }
    current_time = start_time
    for series_index in range(series_length):
        if series_index > 0:
            current_time += datetime.timedelta(minutes=random.randint(1, 60))
        timeseries_block["TimeIndex"].append(to_iso_format_datetime_string(current_time))

    for _ in range(n_series):
        timeseries_block["Series"][next(get_attribute_name())] = \
            generate_timeseries_values(next(get_unit_code()), series_length)

    return timeseries_block


class TestUnitCode(unittest.TestCase):
    """Unit tests for the UnitCode class."""

    def test_is_valid(self):
        """Unit test for testing the validity checking of UCUM unit codes."""
        valid_codes = ["m", "ug", "mA", "m3/s", "J", "V", "MW", "kV.A{r}"]
        invalid_codes = ["invalid", "", "mmmm"]

        for valid_code in valid_codes:
            with self.subTest(valid_code=valid_code):
                self.assertTrue(UnitCode.is_valid(valid_code))
        for invalid_code in invalid_codes:
            with self.subTest(invalid_code=invalid_code):
                self.assertFalse(UnitCode.is_valid(invalid_code))


class TestValueArrayBlock(unittest.TestCase):
    """Unit tests for the ValueArrayBlock class."""

    def test_valid_attributes(self):
        """Unit test for creating ValueArrayBlock objects with valid input."""
        test_attributes = [generate_timeseries_values(next(get_unit_code()), 12) for _ in range(20)]

        for test_attribute in test_attributes:
            # test creating object using from_json method
            attribute_object = ValueArrayBlock(**test_attribute)  # pyright: reportGeneralTypeIssues=false
            self.assertIsInstance(attribute_object, ValueArrayBlock)
            self.assertEqual(attribute_object.unit_of_measure, test_attribute["UnitOfMeasure"])
            self.assertEqual(attribute_object.values, test_attribute["Values"])
            self.assertEqual(attribute_object.json(), test_attribute)

            # test creating object using constructor
            attribute_object2 = ValueArrayBlock(
                UnitOfMeasure=cast(str, test_attribute["UnitOfMeasure"]),
                Values=cast(list, test_attribute["Values"])
            )
            self.assertEqual(attribute_object, attribute_object2)
    
    def test_mixed_ints_and_floats(self):
        """Unit test to check value array block and quantity array block can
        have both ints and floats in the values list."""
        # test data
        data = [
            { 'UnitOfMeasure': 'KWh', 'Values':  [ 1, 2, 0.3 ]},
            { 'UnitOfMeasure': 'KWh', 'Values':  [ 0.1, 2, 3 ]},
            { 'UnitOfMeasure': 'KWh', 'Values':  [ 1, 2, 3 ]},
            { 'UnitOfMeasure': 'KWh', 'Values':  [ 0.1, 0.2, 0.3 ]}
        ]

        for item in data:
            try:
                QuantityArrayBlock( **item )
                ValueArrayBlock( **item )

            except MessageValueError as e:
                self.fail( 'Should not raise MessageValueError: ' +str(e))

    def test_invalid_attributes(self):
        """Unit test for creating ValueArrayBlock objects with invalid input."""
        attribute_valid = {"UnitOfMeasure": "m", "Values": [1, 2, 3]}
        attribute_missing_unit = {"Values": [1, 2, 3]}
        attribute_missing_values = {"UnitOfMeasure": "m"}
        attribute_invalid_unit = {"UnitOfMeasure": "mmmm", "Values": [1, 2, 3]}
        attribute_invalid_values = {"UnitOfMeasure": "m", "Values": [[], []]}
        attribute_inconsistent_values1 = {"UnitOfMeasure": "m", "Values": [1, "2", 3.0]}
        attribute_inconsistent_values2 = {"UnitOfMeasure": "m", "Values": [1, "2", 3]}
        attribute_inconsistent_values3 = {"UnitOfMeasure": "m", "Values": [True, False, 3]}

        self.assertIsInstance(ValueArrayBlock.from_json(attribute_valid), ValueArrayBlock)
        self.assertIsNone(ValueArrayBlock.from_json(attribute_missing_unit))
        self.assertIsNone(ValueArrayBlock.from_json(attribute_missing_values))
        self.assertIsNone(ValueArrayBlock.from_json(attribute_invalid_values))
        self.assertIsNone(ValueArrayBlock.from_json(attribute_inconsistent_values1))
        self.assertIsNone(ValueArrayBlock.from_json(attribute_inconsistent_values2))
        self.assertIsNone(ValueArrayBlock.from_json(attribute_inconsistent_values3))

        # the unit validation should be off by default
        self.assertFalse(ValueArrayBlock.UNIT_CODE_VALIDATION)
        self.assertIsInstance(ValueArrayBlock.from_json(attribute_invalid_unit), ValueArrayBlock)
        ValueArrayBlock.UNIT_CODE_VALIDATION = True  # type: ignore
        self.assertTrue(ValueArrayBlock.UNIT_CODE_VALIDATION)
        self.assertIsNone(ValueArrayBlock.from_json(attribute_invalid_unit))
        ValueArrayBlock.UNIT_CODE_VALIDATION = False

        self.assertRaises(TypeError, ValueArrayBlock, **attribute_missing_unit)
        self.assertRaises(TypeError, ValueArrayBlock, **attribute_missing_values)
        self.assertRaises(MessageValueError, ValueArrayBlock, **attribute_invalid_values)
        self.assertRaises(MessageValueError, ValueArrayBlock, **attribute_inconsistent_values1)
        self.assertRaises(MessageValueError, ValueArrayBlock, **attribute_inconsistent_values2)
        self.assertRaises(MessageValueError, ValueArrayBlock, **attribute_inconsistent_values3)

        self.assertFalse(ValueArrayBlock.UNIT_CODE_VALIDATION)
        ValueArrayBlock(**attribute_invalid_unit)
        ValueArrayBlock.UNIT_CODE_VALIDATION = True  # type: ignore
        self.assertTrue(ValueArrayBlock.UNIT_CODE_VALIDATION)
        self.assertRaises(MessageUnitValueError, ValueArrayBlock, **attribute_invalid_unit)
        ValueArrayBlock.UNIT_CODE_VALIDATION = False


class TestTimeSeriesBlock(unittest.TestCase):
    """Unit tests for the TimeSeriesBlock class."""

    def test_valid_blocks(self):
        """Unit test for creating TimeSeriesBlock objects with valid input."""
        test_blocks = [
            generate_timeseries_block(datetime.datetime.utcnow(), index, 24)
            for index in range(1, 21)
        ]

        for test_block in test_blocks:
            # test creating object using from_json method
            attribute_object = TimeSeriesBlock(**test_block)
            self.assertIsInstance(attribute_object, TimeSeriesBlock)
            self.assertEqual(attribute_object.time_index, test_block["TimeIndex"])

            attribute_series_names = list(test_block["Series"].keys())
            object_series_names = list(attribute_object.series.keys())
            self.assertEqual(object_series_names, attribute_series_names)
            for series_name in attribute_series_names:
                self.assertEqual(attribute_object.series[series_name].json(), test_block["Series"][series_name])
            self.assertEqual(attribute_object.json(), test_block)
            self.assertEqual(str(attribute_object), json.dumps(test_block))

            # test creating object using constructor
            attribute_object2 = TimeSeriesBlock(
                TimeIndex=test_block["TimeIndex"],
                Series=test_block["Series"]
            )
            self.assertEqual(attribute_object2, attribute_object)

            # test adding additional series by add_series method
            series_names = list(test_block["Series"].keys())
            attribute_object3 = TimeSeriesBlock(
                TimeIndex=test_block["TimeIndex"],
                Series={series_names[0]: test_block["Series"][series_names[0]]}
            )
            for series_name in series_names[1:]:
                attribute_object3.add_series(
                    series_name, ValueArrayBlock(**test_block["Series"][series_name]))
            self.assertEqual(attribute_object3, attribute_object)

    def test_invalid_blocks(self):
        """Unit test for creating TimeSeriesBlock objects with invalid input."""
        time_index_valid_3 = ["2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z", "2020-01-01T02:00:00Z"]
        time_index_valid_4 = ["2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z", "2020-01-01T02:00:00Z",
                              "2020-01-01T03:00:00Z"]
        invalid_time_index = ["2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z", "invalid"]

        attribute_valid_3 = {"UnitOfMeasure": "m", "Values": [1, 2, 3]}
        attribute_valid_4 = {"UnitOfMeasure": "m", "Values": [1, 2, 3, 4]}
        invalid_attribute = {"UnitOfMeasure": "m", "Values": [1, 2.0, "3"]}

        valid_block_3 = {"TimeIndex": time_index_valid_3, "Series": {"X": attribute_valid_3, "Y": attribute_valid_3}}
        valid_block_4 = {"TimeIndex": time_index_valid_4, "Series": {"X": attribute_valid_4, "Y": attribute_valid_4}}

        block_missing_timeindex = {"Series": {"X": attribute_valid_3, "Y": attribute_valid_3}}
        block_missing_series1 = {"TimeIndex": time_index_valid_3}
        block_missing_series2 = {"TimeIndex": time_index_valid_3, "Series": {}}
        block_invalid_timeindex = {"TimeIndex": invalid_time_index, "Series": {"X": attribute_valid_3}}
        block_invalid_series = {"TimeIndex": time_index_valid_3, "Series": {"X": invalid_attribute}}
        block_different_length1 = {"TimeIndex": time_index_valid_3, "Series": {"X": attribute_valid_4}}
        block_different_length2 = {"TimeIndex": time_index_valid_4, "Series": {"X": attribute_valid_3}}

        valid_object_3 = TimeSeriesBlock(**valid_block_3)
        valid_object_4 = TimeSeriesBlock(**valid_block_4)
        self.assertIsInstance(valid_object_3, TimeSeriesBlock)
        self.assertIsInstance(valid_object_4, TimeSeriesBlock)

        self.assertIsNone(TimeSeriesBlock.from_json(block_missing_timeindex))
        self.assertIsNone(TimeSeriesBlock.from_json(block_missing_series1))
        self.assertIsNone(TimeSeriesBlock.from_json(block_missing_series2))
        self.assertIsNone(TimeSeriesBlock.from_json(block_invalid_timeindex))
        self.assertIsNone(TimeSeriesBlock.from_json(block_invalid_series))
        self.assertIsNone(TimeSeriesBlock.from_json(block_different_length1))
        self.assertIsNone(TimeSeriesBlock.from_json(block_different_length2))

        self.assertRaises(TypeError, TimeSeriesBlock, **block_missing_timeindex)
        self.assertRaises(TypeError, TimeSeriesBlock, **block_missing_series1)
        self.assertRaises(MessageValueError, TimeSeriesBlock, **block_missing_series2)
        self.assertRaises(MessageDateError, TimeSeriesBlock, **block_invalid_timeindex)
        self.assertRaises(MessageValueError, TimeSeriesBlock, **block_invalid_series)
        self.assertRaises(MessageValueError, TimeSeriesBlock, **block_different_length1)
        self.assertRaises(MessageValueError, TimeSeriesBlock, **block_different_length2)

        self.assertRaises(MessageDateError, setattr, valid_object_3, "time_index", time_index_valid_4)
        self.assertRaises(MessageValueError, setattr, valid_object_3, "series", {"X": attribute_valid_4})
        self.assertRaises(MessageDateError, setattr, valid_object_4, "time_index", time_index_valid_3)
        self.assertRaises(MessageValueError, setattr, valid_object_4, "series", {"X": attribute_valid_3})

        self.assertRaises(MessageValueError, valid_object_3.add_series,
                          "Z", ValueArrayBlock(**attribute_valid_4))
        self.assertRaises(MessageValueError, valid_object_4.add_series,
                          "Z", ValueArrayBlock(**attribute_valid_3))


if __name__ == '__main__':
    unittest.main()
