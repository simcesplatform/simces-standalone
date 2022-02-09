# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains code examples related to using the message classes."""

import csv
import json
import logging
from typing import Dict, Generator, Optional

# the used message examples are defined in examples/message_json.py
from examples.message_json import (
    status_ready_message, status_error_message, example_message,
    invalid_status_1, invalid_status_2, invalid_status_3)
from tools.exceptions.messages import MessageError
from tools.message.block import QuantityBlock, TimeSeriesBlock, ValueArrayBlock
from tools.message.example import ExampleMessage
from tools.messages import StatusMessage, MessageGenerator
from tools.tools import FullLogger

# use the FullLogger for logging to show the output on the screen as well as to store it to a file
# the default file name for the log output is logfile.out
# the file name can be changed by using the environment variable SIMULATION_LOG_FILE
# in python code that can be done by:
#     import os
#     os.environ["SIMULATION_LOG_FILE"] = "my_logs.txt"
LOGGER = FullLogger(__name__, logger_level=logging.INFO)


def test_from_json():
    """Tests for creating message objects using from_json method."""
    LOGGER.info("Example of creating a Status ready message from JSON")
    status_ready = StatusMessage.from_json(status_ready_message)
    if status_ready is None:
        LOGGER.error("Problem loading example status ready message")
        return

    LOGGER.info("Status ready:   {}".format(type(status_ready)))
    LOGGER.info(json.dumps(status_ready.json(), indent=4))  # output the message as JSON in a readable format
    LOGGER.info("")

    # print out the attributes individually from the Status message
    # NOTE: that the JSON attribute names use Pascal case (e.g. MessageId) as is defined in the wiki
    #       while the message properties use snake case (e.g. message_id) as is usual in Python variables
    LOGGER.info("Type for Status message:                 {}".format(status_ready.message_type))
    LOGGER.info("SourceProcessId for Status message:      {}".format(status_ready.source_process_id))
    LOGGER.info("MessageId for Status message:            {}".format(status_ready.message_id))
    LOGGER.info("Timestamp for Status message:            {}".format(status_ready.timestamp))
    LOGGER.info("EpochNumber for Status message:          {}".format(status_ready.epoch_number))
    LOGGER.info("TriggeringMessageIds for Status message: {}".format(status_ready.triggering_message_ids))
    LOGGER.info("Value for Status message:                {}".format(status_ready.value))
    # the optional attributes will have value None if they have not been explicitly given
    LOGGER.info("LastUpdatedInEpoch for Status message:   {}".format(status_ready.last_updated_in_epoch))
    LOGGER.info("Warnings for Status message:             {}".format(status_ready.warnings))
    LOGGER.info("Descriptions for Status message:         {}".format(status_ready.description))
    LOGGER.info("")

    LOGGER.info("Example of creating a Status error message from JSON")
    status_error = StatusMessage.from_json(status_error_message)
    if status_error is None:
        LOGGER.error("Problem loading example status error message")
        return

    LOGGER.info("Status error:   {}".format(type(status_error)))
    LOGGER.info(json.dumps(status_ready.json(), indent=4))  # output the message as JSON in a readable format
    LOGGER.info("")

    LOGGER.info("Type for Status message:                 {}".format(status_error.message_type))
    LOGGER.info("SourceProcessId for Status message:      {}".format(status_error.source_process_id))
    LOGGER.info("MessageId for Status message:            {}".format(status_error.message_id))
    LOGGER.info("Timestamp for Status message:            {}".format(status_error.timestamp))
    LOGGER.info("EpochNumber for Status message:          {}".format(status_error.epoch_number))
    LOGGER.info("LastUpdatedInEpoch for Status message:   {}".format(status_error.last_updated_in_epoch))
    LOGGER.info("TriggeringMessageIds for Status message: {}".format(status_error.triggering_message_ids))
    LOGGER.info("Warnings for Status message:             {}".format(status_error.warnings))
    LOGGER.info("Value for Status message:                {}".format(status_error.value))
    LOGGER.info("Descriptions for Status message:         {}".format(status_error.description))
    LOGGER.info("")

    LOGGER.info("Example of creating a message of type Example from JSON")
    example = ExampleMessage.from_json(example_message)
    if example is None or example.time_quantity is None or example.voltage_array is None or example.weight is None:
        LOGGER.error("Problem loading example message")
        return

    LOGGER.info("Example:   {}".format(type(example)))
    LOGGER.info(json.dumps(example.json(), indent=4))  # output the message as JSON in a readable format
    LOGGER.info("")

    LOGGER.info("Type for Example message:                      {}".format(example.message_type))
    LOGGER.info("SourceProcessId for Example message:           {}".format(example.source_process_id))
    LOGGER.info("MessageId for Example message:                 {}".format(example.message_id))
    LOGGER.info("Timestamp for Example message:                 {}".format(example.timestamp))
    LOGGER.info("EpochNumber for Example message:               {}".format(example.epoch_number))
    LOGGER.info("LastUpdatedInEpoch for Example message:        {}".format(example.last_updated_in_epoch))
    LOGGER.info("TriggeringMessageIds for Example message:      {}".format(example.triggering_message_ids))
    LOGGER.info("Warnings for Example message:                  {}".format(example.warnings))
    LOGGER.info("")
    LOGGER.info("PositiveInteger for Example message:           {}".format(example.positive_integer))
    LOGGER.info("EightCharacters for Example message:           {}".format(example.eight_characters))
    LOGGER.info("PowerQuantity value for Example message:       {}".format(example.power_quantity.value))
    LOGGER.info("PowerQuantity unit for Example message:        {}".format(example.power_quantity.unit_of_measure))
    LOGGER.info("TimeQuantity value for Example message:        {}".format(example.time_quantity.value))
    LOGGER.info("TimeQuantity unit for Example message:         {}".format(example.time_quantity.unit_of_measure))
    LOGGER.info("")
    LOGGER.info("CurrentArray values for Example message:       {}".format(example.current_array.values))
    LOGGER.info("CurrentArray unit for Example message:         {}".format(example.current_array.unit_of_measure))
    LOGGER.info("VoltageArray values for Example message:       {}".format(example.voltage_array.values))
    LOGGER.info("VoltageArray unit for Example message:         {}".format(example.voltage_array.unit_of_measure))
    LOGGER.info("")
    LOGGER.info("Temperature time index for Example message:    {}".format(example.temperature.time_index))
    LOGGER.info("Temperature PlaceA series for Example message: {}".format(example.temperature.series["PlaceA"]))
    temperature_place_b = example.temperature.get_single_series("PlaceB")
    if temperature_place_b is not None:
        LOGGER.info("Temperature PlaceB values for Example message: {}".format(temperature_place_b.values))
        LOGGER.info("Temperature PlaceB unit for Example message:   {}".format(temperature_place_b.unit_of_measure))
    LOGGER.info("Weight time index for Example message:         {}".format(example.weight.time_index))
    LOGGER.info("Weight series for Example message:             {}".format(example.weight.series))
    LOGGER.info("")


def test_invalid_status():
    """Tests for trying to create status message instances with invalid values."""
    LOGGER.info("")
    # from_json method returns None if there is invalid values from some of the attributes
    invalid1 = StatusMessage.from_json(invalid_status_1)  # the Value attribute is missing
    LOGGER.info("{} : {}".format(type(invalid1), invalid1))
    LOGGER.info("")
    invalid2 = StatusMessage.from_json(invalid_status_2)  # the Value attribute has an invalid value
    LOGGER.info("{} : {}".format(type(invalid2), invalid2))
    LOGGER.info("")
    invalid3 = StatusMessage.from_json(invalid_status_3)  # the EpochNumber attribute has an invalid value
    LOGGER.info("{} : {}".format(type(invalid3), invalid3))
    LOGGER.info("")

    # Note:     StatusMessage(**{"attr1": value1, "attr2": value2})
    # is the as StatusMessage(attr1=value1, attr2=value)
    try:
        # using the constructor directly throws an exception when there is invalid attribute values
        invalid1 = StatusMessage(**invalid_status_1)
        LOGGER.info(str(invalid1))
    except MessageError as message_error:
        LOGGER.warning("Received an exception {}: {}".format(type(message_error), message_error))

    try:
        invalid2 = StatusMessage(**invalid_status_2)
        LOGGER.info(str(invalid2))
    except MessageError as message_error:
        LOGGER.warning("Received an exception {}: {}".format(type(message_error), message_error))

    try:
        invalid3 = StatusMessage(**invalid_status_3)
        LOGGER.info(str(invalid3))
    except MessageError as message_error:
        LOGGER.warning("Received an exception {}: {}".format(type(message_error), message_error))


def test_message_generator():
    """Examples for using the message generator class to help creating message objects."""
    LOGGER.info("")
    # The message generator takes the simulation id and the source process id as parameters
    # since they remain the same throughout the entire simulation run.
    message_generator = MessageGenerator(
        simulation_id="2020-11-01T00:00:00.000Z",
        source_process_id="Storage")

    # Using the general get_message method to create a Status ready message.
    LOGGER.info("Generating the first status message")
    status1 = message_generator.get_message(
        StatusMessage,
        EpochNumber=0,
        TriggeringMessageIds=["manager-1"],
        Value="ready")
    LOGGER.info("{}".format(type(status1)))
    LOGGER.info(json.dumps(status1.json(), indent=4))
    LOGGER.info("")

    # Using the direct helper method get_status_ready_message to create a Status ready message
    LOGGER.info("Generating the second status message")
    status2 = message_generator.get_status_ready_message(
        EpochNumber=1,
        TriggeringMessageIds=["manager-2"])
    LOGGER.info("{}".format(type(status2)))
    LOGGER.info(json.dumps(status2.json(), indent=4))
    LOGGER.info("")

    # Using the general get_message method to create an Example message.
    LOGGER.info("Generating an example message")
    example = message_generator.get_message(
        ExampleMessage,
        EpochNumber=5,
        TriggeringMessageIds=["manager-6"],
        PositiveInteger=42,
        PowerQuantity=10.1,
        TimeQuantity=QuantityBlock(
            UnitOfMeasure="s",
            Value=60
        ),
        CurrentArray=[111.1, 122.2, 133.3],
        Temperature=TimeSeriesBlock(
            TimeIndex=["2010-01-01T00:00:00Z", "2010-01-02T00:00:00Z", "2010-01-03T00:00:00Z"],
            Series={
                "PlaceA": ValueArrayBlock(
                    UnitOfMeasure="Cel",
                    Values=[-10.1, -12.3, -11.2]
                ),
                "PlaceB": ValueArrayBlock(
                    UnitOfMeasure="Cel",
                    Values=[-5.6, -7.9, -8.2]
                )
            }
        ))
    LOGGER.info("{}".format(type(example)))
    LOGGER.info(json.dumps(example.json(), indent=4))
    LOGGER.info("")

    # Examples of trying to create an invalid status messages
    try:
        LOGGER.info("Trying to create a status message with missing triggering message ids")
        invalid1 = message_generator.get_message(
            StatusMessage,
            EpochNumber=12,
            Value="ready"
        )
        LOGGER.info(str(invalid1))
    except (TypeError, MessageError) as message_error:
        LOGGER.warning("Received an exception {}: {}".format(type(message_error), message_error))
    LOGGER.info("")

    try:
        LOGGER.info("Trying to create a status message with invalid value for epoch number")
        invalid2 = message_generator.get_status_ready_message(
            EpochNumber=-1,
            TriggeringMessageIds=[]
        )
        LOGGER.info(str(invalid2))
    except MessageError as message_error:
        LOGGER.warning("Received an exception {}: {}".format(type(message_error), message_error))
    LOGGER.info("")


def get_timeseries_from_csv(filename: str,
                            timestamp_column: str,
                            unit_of_measures: Dict[str, str],
                            column_separator: str,
                            rows: Optional[int] = None) -> Generator[TimeSeriesBlock, None, None]:
    """
    Reads a CSV file and converts it to a Time series block object.
    Returns only block created from the asked number of rows at a time.
    No error handling regarding file reading errors is done.
    - filename: the name of the CSV file (the file must contain a header row)
    - timestamp_column: the column name that is to be used as timestamp list, i.e. the TimeIndex attribute
    - unit_of_measures: a dictionary containing the units for each value column in the CSV file
    - column_separator: the character used as a column separator in the CSV file
    - rows: how many values are taken into the Time series block (if None or missing, the entire file is used)
    """
    with open(filename, mode="r", encoding="UTF-8") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=column_separator)

        if timestamp_column not in [] if csv_reader.fieldnames is None else csv_reader.fieldnames:
            LOGGER.warning("No timestamp column found from the CSV file {}".format(filename))
            # Return None on error.
            return None

        # The other column names except the timestamp column as a list
        series_names = [
            field_name
            for field_name in ([] if csv_reader.fieldnames is None else csv_reader.fieldnames)
            if field_name != timestamp_column
        ]

        # Check that the columns from the CSV file matches the given unit of measures
        if set(series_names) != set(unit_of_measures):
            LOGGER.warning("The unit of measure list, {}, does not match with the column names, {}".format(
                list(unit_of_measures), series_names
            ))
            return None

        # Setup variables for the time_index and the value series
        time_index = []
        series = {
            series_name: []
            for series_name in series_names
        }

        row_count = 0
        at_the_beginning = True
        for csv_row in csv_reader:
            if row_count == 0 and not at_the_beginning:
                # Clear the variables for new a Time series block
                time_index = []
                series = {
                    series_name: []
                    for series_name in series_names
                }

            row_count += 1
            time_index.append(csv_row[timestamp_column])
            for series_name in series_names:
                # assume all the values for the time series are floats
                # NOTE: no error checking if the value is not convertable
                series[series_name].append(float(csv_row[series_name]))

            if rows is not None and row_count == rows:
                row_count = 0
                at_the_beginning = False
                # After reading the wanted number of rows return a Time series block object.
                yield TimeSeriesBlock(
                    TimeIndex=time_index,
                    Series={
                        series_name: ValueArrayBlock(  # with float values also QuantityArrayBlock could be used
                            Values=series_values,
                            UnitOfMeasure=unit_of_measures[series_name]
                        )
                        for series_name, series_values in series.items()
                    }
                )

    # Return the last rows as a time series block even if there were not enough rows left.
    # NOTE: this is also used to return the Time series block object if the entire CSV file
    # is wanted (when rows is None or it is missing) as a single Time series block object.
    if row_count > 0 or rows is None:
        yield TimeSeriesBlock(
            TimeIndex=time_index,
            Series={
                series_name: ValueArrayBlock(
                    Values=series_values,
                    UnitOfMeasure=unit_of_measures[series_name]
                )
                for series_name, series_values in series.items()
            }
        )

    return None


def test_timeseries_from_csv():
    """Examples for creating time series blocks from a csv file."""
    single_value_csv_filename = "examples/timeseries_single.csv"
    multi_value_csv_filename = "examples/timeseries_multi.csv"
    column_separator = ";"
    timestamp_column = "timestamp"

    # load an entire CSV file to a Time series block object
    timeseries_single = next(get_timeseries_from_csv(
        filename=single_value_csv_filename,
        timestamp_column=timestamp_column,
        unit_of_measures={"Cargo": "g"},
        column_separator=column_separator
    ))

    # Print out the Time series block in a human-readable manner
    LOGGER.info("The Time series block containing a single value series column")
    LOGGER.info("{}".format(json.dumps(timeseries_single.json(), indent=4)))
    LOGGER.info("")

    # load a CSV file to a Time series block 6 rows at a time
    timeseries_multi_generator = get_timeseries_from_csv(
        filename=multi_value_csv_filename,
        timestamp_column=timestamp_column,
        unit_of_measures={
            "PlaceA": "Cel",
            "PlaceB": "Cel"
        },
        column_separator=column_separator,
        rows=6
    )
    for index, timeseries_multi in enumerate(timeseries_multi_generator, start=1):
        LOGGER.info("The Time series block {} from the multi column CSV".format(index))
        LOGGER.info("{}".format(json.dumps(timeseries_multi.json(), indent=4)))

    # Use the Time series blocks as the attribute values for a message object
    example = ExampleMessage.from_json(example_message)
    if example is None or example.time_quantity is None or example.voltage_array is None or example.weight is None:
        LOGGER.error("Problem loading example message")
        return

    # Use the latest multi column series as the value for Temperature attribute in ExampleMessage
    example.temperature = timeseries_multi  # type: ignore  # pylint: disable=undefined-loop-variable
    # Use the single column series as the value for Weight attribute in ExampleMessage
    example.weight = timeseries_single

    # Output the message as JSON in a readable format
    LOGGER.info("")
    LOGGER.info("The example message with new Temperature and Weight attributes:")
    LOGGER.info(json.dumps(example.json(), indent=4))
