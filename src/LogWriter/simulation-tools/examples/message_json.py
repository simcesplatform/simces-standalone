# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains some message examples in JSON format."""

# NOTE: Here all examples are given as Python dictionaries that are a superset for JSON objects.
#       I.e. all JSON objects cab be Python dictionaries but not all Python dictionaries are JSON objects.

from tools.message.abstract import AbstractResultMessage
from tools.message.block import QuantityArrayBlock, QuantityBlock, TimeSeriesBlock, ValueArrayBlock

# define example status ready message in JSON format (without timestamp or optional attributes)
status_ready_message = {
    "Type": "Status",
    "SimulationId": "2020-11-04T07:08:56.198Z",
    "SourceProcessId": "Grid",
    "MessageId": "Grid-1",
    "EpochNumber": 0,
    "TriggeringMessageIds": [
        "simulation_manager-1"
    ],
    "Value": "ready"
}

# define example status error message in JSON format
status_error_message = {
    "Type": "Status",
    "SimulationId": "2020-11-04T07:15:00.222Z",
    "SourceProcessId": "Grid",
    "MessageId": "Grid-6",
    "EpochNumber": 5,
    "TriggeringMessageIds": [
        "simulation_manager-1"
    ],
    "LastUpdatedInEpoch": 5,
    "Warnings": ["warning.internal"],
    "Value": "error",
    "Description": "Description for the error"
}

# create JSON representing the example message type using the classes from tools.message.block
example_message = {
    **AbstractResultMessage(
        Type="Example",
        SimulationId="2020-11-20T11:22:33.444Z",
        SourceProcessId="example_process",
        MessageId="example_process-3",
        EpochNumber=2,
        TriggeringMessageIds=["manager-3", "resource-3"],
    ).json(),                       # .json() here to generate a dictionary corresponding with the JSON format
    "PositiveInteger": 12,
    "EightCharacters": "abcdefgh",
    "PowerQuantity": 100.5,         # the QuantityBlock values can be given with just the float values
    "TimeQuantity": QuantityBlock(  # or by the QuantityBlock objects
        UnitOfMeasure="s",
        Value=3600
    ),
    "CurrentArray": [100.1, 120.1, 111.3],  # the QuantityArrayBlock values can be given with a list of floats
    "VoltageArray": QuantityArrayBlock(
        Values=[-50.1, 12.3, 100.2],
        UnitOfMeasure="V"
    ),
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
    ).json(),
    "Weight": {
        "TimeIndex": [
            "2019-12-12T01:02:03.456Z",
            "2019-12-12T02:02:03.456Z"
        ],
        "Series": {
            "Cargo": {
                "UnitOfMeasure": "kg",
                "Values": [
                    1.2,
                    1.3
                ]
            }
        }
    }
}

# example of an invalid Status message that is missing the "Value" attribute
invalid_status_1 = {
    "Type": "Status",
    "SimulationId": "2020-11-04T07:08:56.198Z",
    "SourceProcessId": "Grid",
    "MessageId": "Grid-1",
    "EpochNumber": 0,
    "TriggeringMessageIds": [
        "simulation_manager-1"
    ]
}

# example of an invalid Status message that has an invalid value for the attribute "Value"
invalid_status_2 = {
    "Type": "Status",
    "SimulationId": "2020-11-04T07:08:56.198Z",
    "SourceProcessId": "Grid",
    "MessageId": "Grid-1",
    "EpochNumber": 0,
    "TriggeringMessageIds": [
        "simulation_manager-1"
    ],
    "Value": "hello"
}

# example of an invalid Status message that has an invalid value for the attribute "EpochNumber"
invalid_status_3 = {
    "Type": "Status",
    "SimulationId": "2020-11-04T07:08:56.198Z",
    "SourceProcessId": "Grid",
    "MessageId": "Grid-1",
    "EpochNumber": -5,
    "TriggeringMessageIds": [
        "simulation_manager-1"
    ],
    "Value": "ready"
}
