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
Tests for the RequestMessages class.
"""
import unittest
import json
import copy

from domain_messages.Request import RequestMessage
from tools.message.block import QuantityBlock
from tools.exceptions.messages import MessageValueError

from tools.tests.messages_common import FULL_JSON, DEFAULT_TIMESTAMP

import datetime
from tools.datetime_tools import to_iso_format_datetime_string

# (subclass) Attribute names
ATTRIBUTE_ACTIVATIONTIME = "ActivationTime"
ATTRIBUTE_DURATION = "Duration"
ATTRIBUTE_DIRECTION = "Direction"
ATTRIBUTE_REALPOWERMIN = "RealPowerMin"
ATTRIBUTE_REALPOWERREQUEST = "RealPowerRequest"
ATTRIBUTE_CUSTOMERIDS = "CustomerIds"
ATTRIBUTE_CONGESTIONID = "CongestionId"
ATTRIBUTE_BIDRESOLUTION = "BidResolution"

# Test data
DEF_ACTIVATIONTIME = to_iso_format_datetime_string(datetime.datetime.now())
DEF_DURATION = {
    QuantityBlock.VALUE_ATTRIBUTE: 1.0,
    QuantityBlock.UNIT_OF_MEASURE_ATTRIBUTE: RequestMessage.QUANTITY_BLOCK_ATTRIBUTES[ATTRIBUTE_DURATION]
}
DEF_DIRECTION = "downregulation"
DEF_REALPOWERMIN = {
    QuantityBlock.VALUE_ATTRIBUTE: 1.0,
    QuantityBlock.UNIT_OF_MEASURE_ATTRIBUTE: RequestMessage.QUANTITY_BLOCK_ATTRIBUTES[ATTRIBUTE_REALPOWERMIN]
}
DEF_REALPOWERREQUEST = {
    QuantityBlock.VALUE_ATTRIBUTE: 2.0,
    QuantityBlock.UNIT_OF_MEASURE_ATTRIBUTE: RequestMessage.QUANTITY_BLOCK_ATTRIBUTES[ATTRIBUTE_REALPOWERREQUEST]
}
DEF_CUSTOMERIDS = ["customer1", "customer2"]
DEF_CONGESTIONID = "congestion1"
DEF_BIDRESOLUTION = {
    QuantityBlock.VALUE_ATTRIBUTE: 0.1,
    QuantityBlock.UNIT_OF_MEASURE_ATTRIBUTE: RequestMessage.QUANTITY_BLOCK_ATTRIBUTES[ATTRIBUTE_BIDRESOLUTION]
}

SUBCLASS_JSON = {
    ATTRIBUTE_ACTIVATIONTIME: DEF_ACTIVATIONTIME,
    ATTRIBUTE_DURATION: DEF_DURATION,
    ATTRIBUTE_DIRECTION: DEF_DIRECTION,
    ATTRIBUTE_REALPOWERMIN: DEF_REALPOWERMIN,
    ATTRIBUTE_REALPOWERREQUEST: DEF_REALPOWERREQUEST,
    ATTRIBUTE_CUSTOMERIDS: DEF_CUSTOMERIDS,
    ATTRIBUTE_CONGESTIONID: DEF_CONGESTIONID,
    ATTRIBUTE_BIDRESOLUTION: DEF_BIDRESOLUTION
}

DEF_TYPE = "Request"
FULL_JSON = {**FULL_JSON, "Type": DEF_TYPE}

# Class specific test data and common test data
MESSAGE_JSON = {**FULL_JSON, **SUBCLASS_JSON}
# Without optional attributes
MESSAGE_STRIPPED_JSON = copy.deepcopy(MESSAGE_JSON)
del MESSAGE_STRIPPED_JSON[ATTRIBUTE_BIDRESOLUTION]


class TestRequestMessage(unittest.TestCase):
    """
    Tests for RequestMessage
    """

    def test_message_typ(self):
        """Test message type"""
        self.assertEqual(RequestMessage.CLASS_MESSAGE_TYPE, "Request")
        self.assertEqual(RequestMessage.MESSAGE_TYPE_CHECK, True)

    def test_message_creation(self):
        """Test basic object creation"""

        # With optional parameters:
        message_data = copy.deepcopy(MESSAGE_JSON)
        message = RequestMessage(**message_data)
        self.assertIsInstance(message, RequestMessage)

        # Without optional parameters:
        message_data = copy.deepcopy(MESSAGE_STRIPPED_JSON)
        message = RequestMessage(**message_data)
        self.assertIsInstance(message, RequestMessage)

    def test_message_json(self):
        """Test that the object can be created from JSON"""

        # All attributes
        message_json = RequestMessage.from_json(MESSAGE_JSON).json()
        for attr in RequestMessage.MESSAGE_ATTRIBUTES:
            with self.subTest(attribute=attr):
                self.assertIn(attr, message_json)
                self.assertEqual(message_json[attr], MESSAGE_JSON[attr])

        # Without optional attributes
        message_json = RequestMessage.from_json(MESSAGE_STRIPPED_JSON).json()
        for attr in RequestMessage.MESSAGE_ATTRIBUTES:
            with self.subTest(attribute=attr):
                if attr in RequestMessage.OPTIONAL_ATTRIBUTES:
                    continue
                self.assertIn(attr, message_json)
                self.assertEqual(message_json[attr], MESSAGE_JSON[attr])

    def test_message_bytes(self):
        """Test bytes conversion."""
        message_full = RequestMessage.from_json(MESSAGE_JSON)
        message_copy = RequestMessage.from_json(json.loads(message_full.bytes().decode("UTF-8")))

        self.assertEqual(message_copy.timestamp, message_full.timestamp)
        self.assertEqual(message_copy.message_type, message_full.message_type)
        self.assertEqual(message_copy.simulation_id, message_full.simulation_id)
        self.assertEqual(message_copy.source_process_id, message_full.source_process_id)
        self.assertEqual(message_copy.message_id, message_full.message_id)
        self.assertEqual(message_copy.epoch_number, message_full.epoch_number)
        self.assertEqual(message_copy.last_updated_in_epoch, message_full.last_updated_in_epoch)
        self.assertEqual(message_copy.triggering_message_ids, message_full.triggering_message_ids)
        self.assertEqual(message_copy.warnings, message_full.warnings)
        self.assertEqual(message_copy.activation_time, message_full.activation_time)
        self.assertEqual(message_copy.duration, message_full.duration)
        self.assertEqual(message_copy.direction, message_full.direction)
        self.assertEqual(message_copy.real_power_min, message_full.real_power_min)
        self.assertEqual(message_copy.real_power_request, message_full.real_power_request)
        self.assertEqual(message_copy.customer_ids, message_full.customer_ids)
        self.assertEqual(message_copy.congestion_id, message_full.congestion_id)
        self.assertEqual(message_copy.bid_resolution, message_full.bid_resolution)

    def test_message_equals(self):
        """Test equals method"""
        message_full = RequestMessage(Timestamp=DEFAULT_TIMESTAMP, **MESSAGE_JSON)
        message_copy = RequestMessage(Timestamp=DEFAULT_TIMESTAMP, **MESSAGE_JSON)
        self.assertEqual(message_full, message_copy)

        different_values = {
            "activation_time": to_iso_format_datetime_string(datetime.datetime.now()),
            "duration": {
                QuantityBlock.VALUE_ATTRIBUTE: 2.0,
                QuantityBlock.UNIT_OF_MEASURE_ATTRIBUTE:
                    RequestMessage.QUANTITY_BLOCK_ATTRIBUTES[ATTRIBUTE_DURATION]
            },
            "direction": "upregulation",
            "real_power_min": {
                QuantityBlock.VALUE_ATTRIBUTE: 2.0,
                QuantityBlock.UNIT_OF_MEASURE_ATTRIBUTE:
                    RequestMessage.QUANTITY_BLOCK_ATTRIBUTES[ATTRIBUTE_REALPOWERMIN]
            },
            "real_power_request": {
                QuantityBlock.VALUE_ATTRIBUTE: 3.0,
                QuantityBlock.UNIT_OF_MEASURE_ATTRIBUTE:
                    RequestMessage.QUANTITY_BLOCK_ATTRIBUTES[ATTRIBUTE_REALPOWERREQUEST]
            },
            "customer_ids": ["customer10", "customer11"],
            "congestion_id": "congestion10",
            "bid_resolution": {
                QuantityBlock.VALUE_ATTRIBUTE: 0.5,
                QuantityBlock.UNIT_OF_MEASURE_ATTRIBUTE:
                    RequestMessage.QUANTITY_BLOCK_ATTRIBUTES[ATTRIBUTE_BIDRESOLUTION]
            }
        }

        for attr, value in different_values.items():
            with self.subTest(attribute=attr, value=value):
                old_value = getattr(message_copy, attr)
                setattr(message_copy, attr, value)
                self.assertNotEqual(message_full, message_copy)
                setattr(message_copy, attr, old_value)
                self.assertEqual(message_full, message_copy)

    def test_invalid_values(self):
        """Test invalid attribute values"""

        # ActivationTime # Tested using abstract message _check_datetime

        # Duration
        invalid_durations = [-1.0,
                             {
                                 QuantityBlock.VALUE_ATTRIBUTE: 1.0,
                                 QuantityBlock.UNIT_OF_MEASURE_ATTRIBUTE: "Not_Min"
                             }]
        invalid_json = copy.deepcopy(MESSAGE_JSON)
        for duration in invalid_durations:
            invalid_json[ATTRIBUTE_DURATION] = duration
            with self.subTest(attribute=ATTRIBUTE_DURATION, value=duration):
                with self.assertRaises(MessageValueError):
                    RequestMessage(**invalid_json)

        # Direction
        invalid_direction = "invalidRegulation"
        invalid_json = copy.deepcopy(MESSAGE_JSON)
        invalid_json[ATTRIBUTE_DIRECTION] = invalid_direction
        with self.assertRaises(MessageValueError):
            RequestMessage(**invalid_json)

        # RealPowerMin
        invalid_real_power_min = [-1.0,
                                  {
                                      QuantityBlock.VALUE_ATTRIBUTE: 1.0,
                                      QuantityBlock.UNIT_OF_MEASURE_ATTRIBUTE: "Not_kW"
                                  }]
        invalid_json = copy.deepcopy(MESSAGE_JSON)
        for real_power_min in invalid_real_power_min:
            invalid_json[ATTRIBUTE_REALPOWERMIN] = real_power_min
            with self.subTest(attribute=ATTRIBUTE_REALPOWERMIN, value=real_power_min):
                with self.assertRaises(MessageValueError):
                    RequestMessage(**invalid_json)

        # RealPowerRequest
        invalid_real_power_request = [-1.0,
                                      {
                                          QuantityBlock.VALUE_ATTRIBUTE: 1.0,
                                          QuantityBlock.UNIT_OF_MEASURE_ATTRIBUTE: "Not_kW"
                                      }]
        invalid_json = copy.deepcopy(MESSAGE_JSON)
        for real_power_request in invalid_real_power_request:
            invalid_json[ATTRIBUTE_REALPOWERREQUEST] = real_power_request
            with self.subTest(attribute=ATTRIBUTE_REALPOWERREQUEST, value=real_power_request):
                with self.assertRaises(MessageValueError):
                    RequestMessage(**invalid_json)

        # CustomerIds
        invalid_customer_ids = [list(),
                                2.0]
        invalid_json = copy.deepcopy(MESSAGE_JSON)
        for customer_id in invalid_customer_ids:
            invalid_json[ATTRIBUTE_CUSTOMERIDS] = customer_id
            with self.subTest(attribute=ATTRIBUTE_CUSTOMERIDS, value=customer_id):
                with self.assertRaises(MessageValueError):
                    RequestMessage(**invalid_json)

        # CongestionId
        invalid_congestion_ids = [2.0,
                                  2,
                                  ""]
        invalid_json = copy.deepcopy(MESSAGE_JSON)
        for congestion_id in invalid_congestion_ids:
            invalid_json[ATTRIBUTE_CONGESTIONID] = congestion_id
            with self.subTest(attribute=ATTRIBUTE_CONGESTIONID, value=congestion_id):
                with self.assertRaises(MessageValueError):
                    RequestMessage(**invalid_json)

        # BidResolution
        invalid_bid_resolution = [-1.0,
                                  {
                                      QuantityBlock.VALUE_ATTRIBUTE: 1.0,
                                      QuantityBlock.UNIT_OF_MEASURE_ATTRIBUTE: "Not_kW"
                                  }]
        invalid_json = copy.deepcopy(MESSAGE_JSON)
        for resolution in invalid_bid_resolution:
            invalid_json[ATTRIBUTE_BIDRESOLUTION] = resolution
            with self.subTest(attribute=ATTRIBUTE_BIDRESOLUTION, value=resolution):
                with self.assertRaises(MessageValueError):
                    RequestMessage(**invalid_json)


if __name__ == "__main__":
    unittest.main()
