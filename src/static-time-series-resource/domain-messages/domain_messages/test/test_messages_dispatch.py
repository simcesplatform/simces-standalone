# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Amir Safdarian <amir.safdarian@vtt.fi>
#            Kalle Ruuth (TAU) <kalle.ruuth@tuni.fi>
#            Keski-Koukkari Antti <antti.keski-koukkari@vtt.fi>
#            Md Tanjimuddin <md.tanjimuddin@tuni.fi>
#            Olli Suominen <olli.suominen@tuni.fi>
#            Otto Hylli <otto.hylli@tuni.fi>
#            Tanjim <tanjim0023@gmail.com>
#            Ville Heikkilä <ville.heikkila@tuni.fi>
#            Ville Mörsky (TAU) <ville.morsky@tuni.fi>
"""
Tests for the ResourceForecastStateDispatchMessage class.
"""
import unittest
import json
import copy

from domain_messages.dispatch  import ResourceForecastStateDispatchMessage

from tools.message.block import TimeSeriesBlock
from tools.exceptions.messages import MessageValueError

from tools.tests.messages_common import DEFAULT_TYPE, FULL_JSON, DEFAULT_TIMESTAMP

TIME_INDEX = [
    "2020-06-25T00:00:00.000Z",
    "2020-06-25T01:00:00.000Z",
    "2020-06-25T02:00:00.000Z",
    "2020-06-25T03:00:00.000Z"
    ]

GEN1_DISPATCH_VALUES = [0.0, 0.2, 0.27, 0.1]
GEN1_SERIES = {
    "RealPower": {
        "UnitOfMeasure": "kW",
        "Values": GEN1_DISPATCH_VALUES
    }
}
GEN1_DISPATCH = {
    "TimeIndex": TIME_INDEX,
    "Series": GEN1_SERIES
}

GEN2_DISPATCH_VALUES = [0.09, 0.21, 0.16, 0.29]
GEN2_SERIES = {
    "RealPower": {
        "UnitOfMeasure": "kW",
        "Values": GEN2_DISPATCH_VALUES
    }
}
GEN2_DISPATCH = {
    "TimeIndex": TIME_INDEX,
    "Series": GEN2_SERIES
}

SUBCLASS_JSON = {
    "Dispatch": {
        "Gen1": GEN1_DISPATCH,
        "Gen2": GEN2_DISPATCH
    }
}

DEFAULT_TYPE = "ResourceForecastState.Dispatch"
FULL_JSON = {**FULL_JSON, "Type": DEFAULT_TYPE}

MESSAGE_JSON = {**FULL_JSON, **SUBCLASS_JSON}

class TestResourceForecastStateDispatchMessage(unittest.TestCase):

    def test_message_type(self):
        """Unit test for the ResourceStateMessage type."""
        self.assertEqual(ResourceForecastStateDispatchMessage.CLASS_MESSAGE_TYPE, 
                        "ResourceForecastState.Dispatch")
        self.assertEqual(ResourceForecastStateDispatchMessage.MESSAGE_TYPE_CHECK, True)


    def test_message_creation(self):
        """Test basic object creation does not produce any errors."""
        message_data = copy.deepcopy(MESSAGE_JSON)
        message = ResourceForecastStateDispatchMessage(**message_data)
        self.assertIsInstance(message, ResourceForecastStateDispatchMessage)

    def test_message_json(self):
        """Test that object can be created from JSON."""
        # test with all attributes
        message_json = ResourceForecastStateDispatchMessage.from_json(MESSAGE_JSON).json()
        # check that new object has all subclass specific attributes with correct values.
        for attr in ResourceForecastStateDispatchMessage.MESSAGE_ATTRIBUTES:
            with self.subTest(attribute=attr):
                self.assertIn(attr, message_json)
                self.assertEqual(message_json[attr], MESSAGE_JSON[attr])

    def test_message_bytes(self):
        """Unit test for testing that the bytes conversion works correctly."""
        message_full = ResourceForecastStateDispatchMessage.from_json(MESSAGE_JSON)
        message_copy = ResourceForecastStateDispatchMessage.from_json(json.loads(message_full.bytes().decode("UTF-8")))

        self.assertEqual(message_copy.timestamp, message_full.timestamp)
        self.assertEqual(message_copy.message_type, message_full.message_type)
        self.assertEqual(message_copy.simulation_id, message_full.simulation_id)
        self.assertEqual(message_copy.source_process_id, message_full.source_process_id)
        self.assertEqual(message_copy.message_id, message_full.message_id)
        self.assertEqual(message_copy.epoch_number, message_full.epoch_number)
        self.assertEqual(message_copy.last_updated_in_epoch, message_full.last_updated_in_epoch)
        self.assertEqual(message_copy.triggering_message_ids, message_full.triggering_message_ids)
        self.assertEqual(message_copy.warnings, message_full.warnings)
        self.assertEqual(message_copy.dispatch, message_full.dispatch)

    def test_message_equals(self):
        """Test that equals method works correctly."""
        message_full = ResourceForecastStateDispatchMessage(Timestamp=DEFAULT_TIMESTAMP, **MESSAGE_JSON)
        message_copy = ResourceForecastStateDispatchMessage(Timestamp=DEFAULT_TIMESTAMP, **MESSAGE_JSON)
        self.assertEqual(message_full, message_copy)

        # test with different values
        gen2_old_values = message_copy.dispatch["Gen2"].series["RealPower"].values
        gen2_new_values = [0.09, 0.21, 0.17, 0.29] # 0.16 -> 0.17
        message_copy.dispatch["Gen2"].series["RealPower"].values = gen2_new_values
        self.assertNotEqual(message_full, message_copy)
        message_copy.dispatch["Gen2"].series["RealPower"].values = gen2_old_values
        self.assertEqual(message_full, message_copy)

        # test with different resource names
        gen2_dispatch = message_copy.dispatch["Gen2"]
        message_copy.dispatch.remove_component_dispatch("Gen2")
        self.assertNotEqual(message_full, message_copy)
        message_copy.dispatch["Gen3"] = gen2_dispatch
        self.assertNotEqual(message_full, message_copy)

    @unittest.skip("not implemented")
    def test_invalid_values(self):
        invalid_values = [] # TODO

        invalid_json = copy.deepcopy(MESSAGE_JSON)
        for value in invalid_values:
            invalid_json['Dispatch'] = value
            with self.subTest(attribute='Dispatch', value=value):
                with self.assertRaises(MessageValueError):
                    ResourceForecastStateDispatchMessage(**invalid_json)


if __name__ == "__main__":
    unittest.main()