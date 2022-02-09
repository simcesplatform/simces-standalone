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
Tests for the ResourceStatesMessages class.
"""
import unittest
import json
import copy

from domain_messages.resource  import ResourceStateMessage
from tools.message.block import QuantityBlock
from tools.exceptions.messages import MessageValueError

from tools.tests.messages_common import DEFAULT_TYPE, FULL_JSON, DEFAULT_TIMESTAMP

# define some test data
CUSTOMERID_ATTRIBUTE = "CustomerId"
#BUS_ATTRIBUTE = "Bus"
REAL_POWER_ATTRIBUTE = "RealPower"
REACTIVE_POWER_ATTRIBUTE = "ReactivePower"
NODE_ATTRIBUTE = "Node"
STATE_OF_CHARGE_ATTRIBUTE = "StateOfCharge"

DEFAULT_CUSTOMERID = "customerid"
DEFAULT_REACTIVE_POWER = {
    QuantityBlock.VALUE_ATTRIBUTE: 5.0,
    QuantityBlock.UNIT_OF_MEASURE_ATTRIBUTE: ResourceStateMessage.QUANTITY_BLOCK_ATTRIBUTES[REACTIVE_POWER_ATTRIBUTE]
}
DEFAULT_REAL_POWER = {
    QuantityBlock.VALUE_ATTRIBUTE: 100.0,
    QuantityBlock.UNIT_OF_MEASURE_ATTRIBUTE: ResourceStateMessage.QUANTITY_BLOCK_ATTRIBUTES[REAL_POWER_ATTRIBUTE]
}
DEFAULT_STATE_OF_CHARGE = {
    QuantityBlock.VALUE_ATTRIBUTE: 90.0,
    QuantityBlock.UNIT_OF_MEASURE_ATTRIBUTE: ResourceStateMessage.QUANTITY_BLOCK_ATTRIBUTES[STATE_OF_CHARGE_ATTRIBUTE]
}
DEFAULT_NODE = 2

SUBCLASS_JSON = {
    CUSTOMERID_ATTRIBUTE: DEFAULT_CUSTOMERID,
   # BUS_ATTRIBUTE: DEFAULT_BUS,
    REAL_POWER_ATTRIBUTE: DEFAULT_REAL_POWER,
    REACTIVE_POWER_ATTRIBUTE: DEFAULT_REACTIVE_POWER,
    STATE_OF_CHARGE_ATTRIBUTE: DEFAULT_STATE_OF_CHARGE,
    NODE_ATTRIBUTE: DEFAULT_NODE
}

DEFAULT_TYPE = "ResourceState"
FULL_JSON = {**FULL_JSON, "Type": DEFAULT_TYPE}

# combine class specific test data with common test data
MESSAGE_JSON = {**FULL_JSON, **SUBCLASS_JSON}
# without optional attributes
MESSAGE_STRIPPED_JSON = copy.deepcopy(MESSAGE_JSON)
del MESSAGE_STRIPPED_JSON[NODE_ATTRIBUTE]
del MESSAGE_STRIPPED_JSON[STATE_OF_CHARGE_ATTRIBUTE]


class TestResourceStateMessage(unittest.TestCase):
    """
    Tests for ResourceStateMessage.
    """

    def test_message_type(self):
        """Unit test for the ResourceStateMessage type."""
        self.assertEqual(ResourceStateMessage.CLASS_MESSAGE_TYPE, "ResourceState")
        self.assertEqual(ResourceStateMessage.MESSAGE_TYPE_CHECK, True)

    def test_message_creation(self):
        """Test basic object creation does not produce any errors."""
        message_data = copy.deepcopy(MESSAGE_JSON)
        # with optional parameterS
        message = ResourceStateMessage(**message_data)
        self.assertIsInstance(message, ResourceStateMessage)
        # without optional parameterS
        del message_data[NODE_ATTRIBUTE]
        del message_data[STATE_OF_CHARGE_ATTRIBUTE]
        message = ResourceStateMessage(**message_data)
        self.assertIsInstance(message, ResourceStateMessage)

    def test_message_json(self):
        """Test that object can be created from JSON."""
        # test with all attributes
        message_json = ResourceStateMessage.from_json(MESSAGE_JSON).json()
        # check that new object has all subclass specific attributes with correct values.
        for attr in ResourceStateMessage.MESSAGE_ATTRIBUTES:
            with self.subTest(attribute=attr):
                self.assertIn(attr, message_json)
                self.assertEqual(message_json[attr], MESSAGE_JSON[attr])

        # test without optional attributes
        message_json = ResourceStateMessage.from_json(MESSAGE_STRIPPED_JSON).json()
        # check that new object has all subclass specific attributes with correct values.
        for attr in ResourceStateMessage.MESSAGE_ATTRIBUTES:
            with self.subTest(attribute=attr):
                if attr in ResourceStateMessage.OPTIONAL_ATTRIBUTES:
                    continue

                self.assertIn(attr, message_json)
                self.assertEqual(message_json[attr], MESSAGE_JSON[attr])

    def test_message_bytes(self):
        """Unit test for testing that the bytes conversion works correctly."""
        message_full = ResourceStateMessage.from_json(MESSAGE_JSON)
        message_copy = ResourceStateMessage.from_json(json.loads(message_full.bytes().decode("UTF-8")))

        self.assertEqual(message_copy.timestamp, message_full.timestamp)
        self.assertEqual(message_copy.message_type, message_full.message_type)
        self.assertEqual(message_copy.simulation_id, message_full.simulation_id)
        self.assertEqual(message_copy.source_process_id, message_full.source_process_id)
        self.assertEqual(message_copy.message_id, message_full.message_id)
        self.assertEqual(message_copy.epoch_number, message_full.epoch_number)
        self.assertEqual(message_copy.last_updated_in_epoch, message_full.last_updated_in_epoch)
        self.assertEqual(message_copy.triggering_message_ids, message_full.triggering_message_ids)
        self.assertEqual(message_copy.warnings, message_full.warnings)
        #self.assertEqual(message_copy.bus, message_full.bus)
        self.assertEqual(message_copy.customerid, message_full.customerid)
        self.assertEqual(message_copy.real_power, message_full.real_power)
        self.assertEqual(message_copy.reactive_power, message_full.reactive_power)
        self.assertEqual(message_copy.node, message_full.node)

    def test_message_equals(self):
        """Test that equals method works correctly."""
        message_full = ResourceStateMessage(Timestamp=DEFAULT_TIMESTAMP, **MESSAGE_JSON)
        message_copy = ResourceStateMessage(Timestamp=DEFAULT_TIMESTAMP, **MESSAGE_JSON)
        self.assertEqual(message_full, message_copy)

        # check that when subclass specific attributes have different values
        # objects will not be equal
        different_values = {
            "customerid": "foo",
            "real_power": 200.0,
            "reactive_power": 10.0,
            "node": 3,
            "state_of_charge": 42.0
        }

        for attr, value in different_values.items():
            with self.subTest(attribute=attr, value=value):
                old_value = getattr(message_copy, attr)
                setattr(message_copy, attr, value)
                self.assertNotEqual(message_full, message_copy)
                setattr(message_copy, attr, old_value)
                self.assertEqual(message_full, message_copy)

    def test_invalid_values(self):
        """Test that invalid attribute values are not accepted."""
        invalid_values = {
            "CustomerId": [1],
            "ReactivePower": ['foo', QuantityBlock(Value=1.0, UnitOfMeasure='kW')],
            "RealPower": [None, {QuantityBlock.VALUE_ATTRIBUTE: 'foo', QuantityBlock.UNIT_OF_MEASURE_ATTRIBUTE: 'kW'}],
            "Node": [4, "foo"],
            "StateOfCharge": [ 150.0, QuantityBlock( Value = -1.0, UnitOfMeasure = "%" ), QuantityBlock( Value = 10.0, UnitOfMeasure = "x" ) ]
        }

        # try to create object with invalid values for each attribute in turn
        for attr, values in invalid_values.items():
            invalid_json = copy.deepcopy(MESSAGE_JSON)
            for value in values:
                invalid_json[attr] = value
                with self.subTest(attribute=attr, value=value):
                    with self.assertRaises(MessageValueError):
                        ResourceStateMessage(**invalid_json)


if __name__ == "__main__":
    unittest.main()
