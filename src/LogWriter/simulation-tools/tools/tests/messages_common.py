# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Common variable values for the message module unit tests."""

import unittest
from tools.datetime_tools import get_utcnow_in_milliseconds
from tools.messages import get_next_message_id

MESSAGE_TYPE_ATTRIBUTE = "Type"
TIMESTAMP_ATTRIBUTE = "Timestamp"
SIMULATION_ID_ATTRIBUTE = "SimulationId"
SOURCE_PROCESS_ID_ATTRIBUTE = "SourceProcessId"
MESSAGE_ID_ATTRIBUTE = "MessageId"
EPOCH_NUMBER_ATTRIBUTE = "EpochNumber"
LAST_UPDATED_IN_EPOCH_ATTRIBUTE = "LastUpdatedInEpoch"
TRIGGERING_MESSAGE_IDS_ATTRIBUTE = "TriggeringMessageIds"
WARNINGS_ATTRIBUTE = "Warnings"
ITERATION_STATUS_ATTRIBUTE = "IterationStatus"
SIMULATION_STATE_ATTRIBUTE = "SimulationState"
START_TIME_ATTRIBUTE = "StartTime"
END_TIME_ATTRIBUTE = "EndTime"
VALUE_ATTRIBUTE = "Value"
DESCRIPTION_ATTRIBUTE = "Description"
NAME_ATTRIBUTE = "Name"

DEFAULT_TYPE = "SimState"
DEFAULT_TIMESTAMP = get_utcnow_in_milliseconds()
DEFAULT_SIMULATION_ID = "2020-07-31T11:11:11.123Z"
DEFAULT_SOURCE_PROCESS_ID = "component"
DEFAULT_MESSAGE_ID = "component-10"
DEFAULT_EPOCH_NUMBER = 7
DEFAULT_LAST_UPDATED_IN_EPOCH = 7
DEFAULT_TRIGGERING_MESSAGE_IDS = ["manager-7", "other-7"]
DEFAULT_WARNINGS = ["warning.convergence"]
DEFAULT_ITERATION_STATUS = "final"
DEFAULT_SIMULATION_STATE = "running"
DEFAULT_START_TIME = "2001-01-01T00:00:00.000Z"
DEFAULT_END_TIME = "2001-01-01T01:00:00.000Z"
DEFAULT_VALUE = "ready"
DEFAULT_DESCRIPTION = "Random error"
DEFAULT_NAME = "Simulation name"
DEFAULT_EXTRA_ATTRIBUTES = {
    "Extra": "Extra attribute",
    "Extra2": 17
}

FULL_JSON = {
    **{
        MESSAGE_TYPE_ATTRIBUTE: DEFAULT_TYPE,
        SIMULATION_ID_ATTRIBUTE: DEFAULT_SIMULATION_ID,
        SOURCE_PROCESS_ID_ATTRIBUTE: DEFAULT_SOURCE_PROCESS_ID,
        MESSAGE_ID_ATTRIBUTE: DEFAULT_MESSAGE_ID,
        EPOCH_NUMBER_ATTRIBUTE: DEFAULT_EPOCH_NUMBER,
        LAST_UPDATED_IN_EPOCH_ATTRIBUTE: DEFAULT_LAST_UPDATED_IN_EPOCH,
        TRIGGERING_MESSAGE_IDS_ATTRIBUTE: DEFAULT_TRIGGERING_MESSAGE_IDS,
        WARNINGS_ATTRIBUTE: DEFAULT_WARNINGS,
        ITERATION_STATUS_ATTRIBUTE: DEFAULT_ITERATION_STATUS,
        SIMULATION_STATE_ATTRIBUTE: DEFAULT_SIMULATION_STATE,
        START_TIME_ATTRIBUTE: DEFAULT_START_TIME,
        END_TIME_ATTRIBUTE: DEFAULT_END_TIME,
        VALUE_ATTRIBUTE: DEFAULT_VALUE,
        DESCRIPTION_ATTRIBUTE: DEFAULT_DESCRIPTION,
        NAME_ATTRIBUTE: DEFAULT_NAME
    },
    **DEFAULT_EXTRA_ATTRIBUTES
}

ALTERNATE_JSON = {
    MESSAGE_TYPE_ATTRIBUTE: "General",
    SIMULATION_ID_ATTRIBUTE: "2020-08-01T11:11:11.123Z",
    SOURCE_PROCESS_ID_ATTRIBUTE: "manager",
    MESSAGE_ID_ATTRIBUTE: "manager-123",
    TIMESTAMP_ATTRIBUTE: "2020-08-01T11:11:11.123Z",
    EPOCH_NUMBER_ATTRIBUTE: 157,
    LAST_UPDATED_IN_EPOCH_ATTRIBUTE: 156,
    TRIGGERING_MESSAGE_IDS_ATTRIBUTE: ["some-15", "other-16"],
    WARNINGS_ATTRIBUTE: ["warning.internal"],
    ITERATION_STATUS_ATTRIBUTE: "intermediate",
    SIMULATION_STATE_ATTRIBUTE: "stopped",
    START_TIME_ATTRIBUTE: "2001-01-01T00:15:00.000Z",
    END_TIME_ATTRIBUTE: "2001-01-01T00:30:00.000Z",
    VALUE_ATTRIBUTE: "error",
    DESCRIPTION_ATTRIBUTE: "Some error message",
    NAME_ATTRIBUTE: "Alternate name",
    "Extra": "extra",
    "Extra2": 1000,
    "Extra3": "extra-test"
}

EPOCH_TEST_JSON = {
    MESSAGE_TYPE_ATTRIBUTE: "Epoch",
    SIMULATION_ID_ATTRIBUTE: "2020-05-05T01:02:03.456Z",
    SOURCE_PROCESS_ID_ATTRIBUTE: "tester",
    MESSAGE_ID_ATTRIBUTE: "tester-10",
    EPOCH_NUMBER_ATTRIBUTE: 5,
    TRIGGERING_MESSAGE_IDS_ATTRIBUTE: ["tester-9"],
    START_TIME_ATTRIBUTE: "2020-01-01T12:00:00.000Z",
    END_TIME_ATTRIBUTE: "2020-01-01T13:00:00.000Z"
}

ERROR_TEST_JSON = {
    MESSAGE_TYPE_ATTRIBUTE: "Status",
    SIMULATION_ID_ATTRIBUTE: "2020-05-05T01:02:03.456Z",
    SOURCE_PROCESS_ID_ATTRIBUTE: "tester",
    MESSAGE_ID_ATTRIBUTE: "tester-10",
    EPOCH_NUMBER_ATTRIBUTE: 5,
    TRIGGERING_MESSAGE_IDS_ATTRIBUTE: ["tester-9"],
    VALUE_ATTRIBUTE: "error",
    DESCRIPTION_ATTRIBUTE: "Test error"
}

STATUS_TEST_JSON = {
    MESSAGE_TYPE_ATTRIBUTE: "Status",
    SIMULATION_ID_ATTRIBUTE: "2020-05-05T01:02:03.456Z",
    SOURCE_PROCESS_ID_ATTRIBUTE: "tester",
    MESSAGE_ID_ATTRIBUTE: "tester-10",
    EPOCH_NUMBER_ATTRIBUTE: 5,
    TRIGGERING_MESSAGE_IDS_ATTRIBUTE: ["tester-9"],
    VALUE_ATTRIBUTE: "ready",
}

GENERAL_TEST_JSON = {
    MESSAGE_TYPE_ATTRIBUTE: "General",
    SIMULATION_ID_ATTRIBUTE: "2020-05-05T01:02:03.456Z",
    SOURCE_PROCESS_ID_ATTRIBUTE: "tester",
    MESSAGE_ID_ATTRIBUTE: "tester-10",
    EPOCH_NUMBER_ATTRIBUTE: 5,
    TRIGGERING_MESSAGE_IDS_ATTRIBUTE: ["tester-9"],
    "Value1": 12,
    "Value2": "hello",
}

RESULT_TEST_JSON = {
    MESSAGE_TYPE_ATTRIBUTE: "Result",
    SIMULATION_ID_ATTRIBUTE: "2020-05-05T01:02:03.456Z",
    SOURCE_PROCESS_ID_ATTRIBUTE: "tester",
    MESSAGE_ID_ATTRIBUTE: "tester-25",
    EPOCH_NUMBER_ATTRIBUTE: 11,
    TRIGGERING_MESSAGE_IDS_ATTRIBUTE: ["tester-24"],
    "Values": {
        "TimeIndex": [
            "2020-01-01T00:00:00.000Z",
            "2020-01-01T01:00:00.000Z",
            "2020-01-01T02:00:00.000Z",
            "2020-01-01T03:00:00.000Z"
        ],
        "Series": {
            "X": {
                "UnitOfMeasure": "m",
                "Values": [
                    111,
                    222,
                    333,
                    444
                ]
            },
            "Y": {
                "UnitOfMeasure": "kg",
                "Values": [
                    12.3,
                    12.4,
                    12.6,
                    12.9
                ]
            }
        }
    }
}


class TestMessageHelpers(unittest.TestCase):
    """Unit tests for the Message class helper functions."""

    def test_get_next_message_id(self):
        """Unit test for the get_next_message_id function."""
        id_generator1 = get_next_message_id("dummy")
        id_generator2 = get_next_message_id("manager", 7)

        self.assertEqual(next(id_generator1), "dummy-1")
        self.assertEqual(next(id_generator1), "dummy-2")
        self.assertEqual(next(id_generator2), "manager-7")
        self.assertEqual(next(id_generator1), "dummy-3")
        self.assertEqual(next(id_generator2), "manager-8")
        self.assertEqual(next(id_generator2), "manager-9")
        self.assertEqual(next(id_generator1), "dummy-4")
        self.assertEqual(next(id_generator2), "manager-10")


if __name__ == '__main__':
    unittest.main()
