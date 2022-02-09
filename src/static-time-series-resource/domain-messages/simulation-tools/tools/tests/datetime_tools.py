# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Unit tests for the functions in datetime_tools.py."""

from datetime import datetime, timedelta, timezone
import unittest

from tools.datetime_tools import get_utcnow_in_milliseconds, to_iso_format_datetime_string, to_utc_datetime_object


class TestDatetimeTools(unittest.TestCase):
    """Unit tests for the datetime_tools module."""
    isoformat = "{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}.{millisecond:03d}Z"

    def test_get_utcnow(self):
        """Unit test for get_utcnow_in_milliseconds function."""
        now_before = datetime.utcnow()
        result_string = get_utcnow_in_milliseconds()
        now_after = datetime.utcnow()
        test_string_before = TestDatetimeTools.isoformat.format(
            year=now_before.year, month=now_before.month, day=now_before.day,
            hour=now_before.hour, minute=now_before.minute, second=now_before.second,
            millisecond=now_before.microsecond // 1000)
        test_string_after = TestDatetimeTools.isoformat.format(
            year=now_after.year, month=now_after.month, day=now_after.day,
            hour=now_after.hour, minute=now_after.minute, second=now_after.second,
            millisecond=now_after.microsecond // 1000)

        self.assertGreaterEqual(result_string, test_string_before)
        self.assertLessEqual(result_string, test_string_after)

    def test_to_iso_format(self):
        """Unit test for to_iso_format_datetime_string."""
        test_string = TestDatetimeTools.isoformat.format(
            year=2020, month=5, day=25, hour=15, minute=24, second=59, millisecond=987)

        input_string_valid = "2020-05-25T15:24:59.987654Z"
        input_object_valid1 = datetime(2020, 5, 25, 15, 24, 59, 987654, tzinfo=timezone.utc)
        input_object_valid2 = datetime(2020, 5, 25, 18, 24, 59, 987654, tzinfo=timezone(timedelta(hours=3)))
        input_object_valid3 = datetime(2020, 5, 25, 10, 24, 59, 987654, tzinfo=timezone(timedelta(hours=-5)))

        self.assertEqual(to_iso_format_datetime_string(input_string_valid), test_string)
        self.assertEqual(to_iso_format_datetime_string(input_object_valid1), test_string)
        self.assertEqual(to_iso_format_datetime_string(input_object_valid2), test_string)
        self.assertEqual(to_iso_format_datetime_string(input_object_valid3), test_string)

        input_string_invalid1 = "2020-05-25T25:24:59.987654Z"
        input_string_invalid2 = "2020+05+25T15:24:59.987654Z"
        self.assertRaises(ValueError, to_iso_format_datetime_string, input_string_invalid1)
        self.assertRaises(ValueError, to_iso_format_datetime_string, input_string_invalid2)

    def test_to_utc_datetime(self):
        """Unit test for to_utc_datetime_object."""
        test_object = datetime(2020, 5, 25, 15, 24, 59, 987000, tzinfo=timezone.utc)

        input_string_valid = "2020-05-25T15:24:59.987Z"
        input_string_invalid1 = "2020-05-25T25:24:59.987Z"
        input_string_invalid2 = "2020+05+25T15:24:59.987Z"

        self.assertEqual(to_utc_datetime_object(input_string_valid), test_object)
        self.assertRaises(ValueError, to_utc_datetime_object, input_string_invalid1)
        self.assertRaises(ValueError, to_utc_datetime_object, input_string_invalid2)


if __name__ == '__main__':
    unittest.main()
