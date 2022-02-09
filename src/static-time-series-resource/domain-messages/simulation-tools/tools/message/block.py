# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>
#            Otto Hylli <otto.hylli@tuni.fi>

"""
Defines various message attribute value blocks that different kinds of messages can use.
"""

from __future__ import annotations
import datetime
import json
from typing import Any, Dict, List, Union

from tools.datetime_tools import to_iso_format_datetime_string
from tools.exceptions.messages import MessageDateError, MessageError, MessageValueError, MessageUnitValueError
from tools.message.unit import UnitCode
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class QuantityBlock():
    '''
    Represents a float type value and associated measurement unit.
    '''

    # name of block attribute which contains the number value
    VALUE_ATTRIBUTE = 'Value'
    # name of the block attribute which contains the unit of measurement.
    UNIT_OF_MEASURE_ATTRIBUTE = 'UnitOfMeasure'

    def __init__(self, **kwargs):
        '''Create a QuantityBlock from the given Value and UnitOfMeasure.
        Raises MessageValueError if value or measurement unit are missing or invalid.'''
        self.value = kwargs.get(self.VALUE_ATTRIBUTE, None)
        self.unit_of_measure = kwargs.get(self.UNIT_OF_MEASURE_ATTRIBUTE, None)

    @property
    def value(self) -> float:
        '''
        Get the value of the quantity.
        '''
        return self._value

    @property
    def unit_of_measure(self) -> str:
        '''
        Get the unit of measure of the quantity.
        '''
        return self._unit_of_measure

    @value.setter
    def value(self, value: float):
        '''
        Set the value for the quantity.
        Raises MessageValueError if the value is invalid.
        '''
        if value is None:
            raise MessageValueError('Quantity block value cannot be None')

        try:
            self._value = float(value)

        except ValueError as value_error:
            raise MessageValueError(f'Unable to convert {value} to float for quantity block value.') from value_error

    @unit_of_measure.setter
    def unit_of_measure(self, unit_of_measure: str):
        '''
        Set the unit of measure for the quantity.
        Raises MessageValueError if the unit is None.
        '''
        if unit_of_measure is None:
            raise MessageValueError('Unit of measure for quantity block cannot be None')

        self._unit_of_measure = str(unit_of_measure)

    def json(self) -> Dict[str, Union[float, str]]:
        '''
        Convert the quantity block to a dictionary.
        '''
        return {self.VALUE_ATTRIBUTE: self.value, self.UNIT_OF_MEASURE_ATTRIBUTE: self.unit_of_measure}

    def __eq__(self, other):
        '''
        Check that two quantity blocks represent the same quantity.
        '''
        return (isinstance(other, QuantityBlock) and
                self.value == other.value and
                self.unit_of_measure == other.unit_of_measure)

    def __str__(self) -> str:
        '''
        Convert to a string.
        '''
        return json.dumps(self.json())

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def validate_json(cls, json_quantity_block: Dict[str, Any]) -> bool:
        '''
        Check if the given dictionary could be converted to a QuantityBlock.
        '''
        try:
            QuantityBlock(**json_quantity_block)
            return True

        except MessageValueError as err:
            LOGGER.warning("{:s} error '{:s}' encountered when validating quantity block".format(
                str(type(err)), str(err)))
            return False

    @classmethod
    def from_json(cls, json_quantity_block: Dict[str, Any]):
        '''
        Convert the given dictionary to a QuantityBlock.
        If the conversion does not succeed returns None.
        '''
        if cls.validate_json(json_quantity_block):
            return QuantityBlock(**json_quantity_block)

        return None


class ValueArrayBlock:
    """
    Represents an array of values with an associated unit of measurement.
    The allowed value types are int, float, str and bool. The value array can contain only one type of values.
    """
    ALLOWED_VALUE_TYPES = [int, float, str, bool]

    # name of block attribute which contains the array of number values
    VALUES_ATTRIBUTE = 'Values'
    # name of the block attribute which contains the unit of measurement.
    UNIT_OF_MEASURE_ATTRIBUTE = 'UnitOfMeasure'

    # By default the unit code validator is not in use.
    UNIT_CODE_VALIDATION = False

    def __init__(self, Values: Union[List[int], List[float], List[str], List[bool]], UnitOfMeasure: str):
        """Creates a new value array block. Throws an exception if parameters contain invalid values."""
        self.values = Values
        self.unit_of_measure = UnitOfMeasure

    @property
    def unit_of_measure(self) -> str:
        """The unit of measurement for the value array block."""
        return self.__unit_of_measure

    @property
    def values(self) -> Union[List[bool], List[int], List[float], List[str]]:
        """The values for the value array block"""
        return self.__values

    @unit_of_measure.setter
    def unit_of_measure(self, unit_of_measure: str):
        if not self._check_unit_of_measure(unit_of_measure):
            raise MessageUnitValueError("'{:s}' is not an allowed unit of measurement".format(str(unit_of_measure)))
        self.__unit_of_measure = unit_of_measure

    @values.setter
    def values(self, values: Union[List[bool], List[int], List[float], List[str]]):
        if not self._check_values(values):
            raise MessageValueError("'{:s}' is not a valid for value array block".format(str(values)))
        self.__values = values

    @classmethod
    def _check_unit_of_measure(cls, unit_of_measure: str) -> bool:
        return (
            isinstance(unit_of_measure, str) and
            (not cls.UNIT_CODE_VALIDATION or UnitCode.is_valid(unit_of_measure))
        )

    @classmethod
    def _check_values(cls, values: Union[List[bool], List[int], List[float], List[str]]) -> bool:
        if not isinstance(values, list):
            return False
        if not values:  # accept empty list
            return True

        value_type = type(values[0])
        if value_type not in cls.ALLOWED_VALUE_TYPES:  # check that the first value is a valid type
            return False

        for value in values:
            # Check that all the values in the list are of the same type.
            if not isinstance(value, value_type):
                return False
        return True

    def json(self) -> Dict[str, Any]:
        """Returns the time series attribute as JSON object."""
        return {
            self.UNIT_OF_MEASURE_ATTRIBUTE: self.unit_of_measure,
            self.VALUES_ATTRIBUTE: self.values
        }

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, self.__class__) and
            self.unit_of_measure == other.unit_of_measure and
            self.values == other.values
        )

    def __str__(self) -> str:
        return json.dumps(self.json())

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def validate_json(cls, json_value_array_block: Dict[str, Any]) -> bool:
        """Validates if the given json object can be used to create a valid ValueArrayBlock instance.
        Returns True if the value array block is ok. Otherwise, returns False."""
        if not isinstance(json_value_array_block, dict):
            return False
        try:
            cls(**json_value_array_block)
            return True

        except (MessageValueError, ValueError, TypeError) as message_error:
            LOGGER.warning("{:s} error '{:s}' encountered when validating value array block".format(
                str(type(message_error)), str(message_error)))
            return False

    @classmethod
    def from_json(cls, json_value_array_block: Dict[str, Any]) -> Union[ValueArrayBlock, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON is contains invalid values, returns None."""
        if cls.validate_json(json_value_array_block):
            return cls(**json_value_array_block)
        return None


class QuantityArrayBlock(ValueArrayBlock):
    """
    Represents an array of float values with an associated unit of measurement.
    """
    ALLOWED_VALUE_TYPES = [float]

    @property
    def values(self) -> List[float]:
        """The values for the value array block"""
        return self.__values

    @values.setter
    def values(self, values: List[float]):
        if not self._check_values(values):
            raise MessageValueError("'{:s}' is not a valid for value array block".format(str(values)))
        self.__values = values


class TimeSeriesBlock():
    """Class for containing one time series block for a message in the simulation platform. """
    TIMEINDEX_ATTRIBUTE = "TimeIndex"
    SERIES_ATTRIBUTE = "Series"

    def __init__(self, TimeIndex: List[Union[str, datetime.datetime]],
                 Series: Dict[str, Union[ValueArrayBlock, Dict[str, Any]]]):
        """Creates a new Time series block. Throws an exception if parameters contain invalid values."""
        self.time_index = TimeIndex
        self.series = Series

    @property
    def time_index(self) -> List[str]:
        """The list of date times for the time series in ISO 8601 format (UTC)."""
        return self.__time_index

    @property
    def series(self) -> Dict[str, ValueArrayBlock]:
        """The list of the time series values as dictionary with the series name as keys and
           ValueArrayBlock objects as values."""
        return self.__series

    def get_single_series(self, series_name: str) -> Union[ValueArrayBlock, None]:
        """Returns the corresponding time series values as a ValueArrayBlock object.
           Returns None if the series does not exist."""
        return self.__series.get(series_name, None)

    @time_index.setter
    def time_index(self, time_index: List[Union[str, datetime.datetime]]):
        if getattr(self, "series", None) is None:
            expected_list_length = None
        else:
            # Check that the time series list is the same length as the first value series list.
            expected_list_length = len(self.series[next(iter(self.series))].values)

        if self._check_time_index(time_index, expected_list_length):
            new_time_index_list = []
            for datetime_value in time_index:
                iso_format_string = to_iso_format_datetime_string(datetime_value)
                if isinstance(iso_format_string, str):
                    new_time_index_list.append(iso_format_string)
                else:
                    raise MessageDateError("'{:s}' is not a valid date time value".format(str(datetime_value)))
            self.__time_index = new_time_index_list

        else:
            raise MessageDateError("'{:s}' is not a valid list of date times".format(str(time_index)))

    @series.setter
    def series(self, series: Dict[str, Union[ValueArrayBlock, Dict[str, Any]]]):
        if getattr(self, "time_index", None) is None:
            expected_list_length = None
        else:
            # Check that all the values series lists are the same length as the time series list.
            expected_list_length = len(self.time_index)

        if not self._check_series(series, expected_list_length):
            raise MessageValueError("'{:s}' is not a valid dictionary of time series values".format(str(series)))

        self.__series = {}
        for series_name, series_values in series.items():
            if isinstance(series_values, ValueArrayBlock):
                self.__series[series_name] = series_values
            else:
                self.__series[series_name] = ValueArrayBlock(**series_values)

    def add_series(self, series_name: str, series_values: ValueArrayBlock):
        """Adds a new or replaces an old value series for the TimeSeriesBlock."""
        if self._check_series({series_name: series_values}, len(self.__time_index)):
            self.series[series_name] = series_values
        else:
            raise MessageValueError("'{:s}' is not a valid value series for {:s}".format(
                str(series_name), str(series_values)))

    @classmethod
    def _check_time_index(cls, time_index: List[Union[str, datetime.datetime]], list_length: int = None) -> bool:
        if not isinstance(time_index, list):
            return False
        if list_length is not None and len(time_index) != list_length:
            return False

        for datetime_value in time_index:
            try:
                if to_iso_format_datetime_string(datetime_value) is None:
                    return False
            except ValueError:
                return False

        return True

    @classmethod
    def _check_series(cls, series: Dict[str, Union[ValueArrayBlock, Dict[str, Any]]], list_length: int = None) -> bool:
        # There must be at least one series
        if not isinstance(series, dict) or len(series) == 0:
            return False

        for series_name, series_values in series.items():
            if not isinstance(series_name, str) or len(series_name) == 0:
                return False

            if isinstance(series_values, ValueArrayBlock):
                if list_length is not None and len(series_values.values) != list_length:
                    return False
            else:
                try:
                    timeseries_attribute = ValueArrayBlock(**series_values)
                    if list_length is not None and len(timeseries_attribute.values) != list_length:
                        return False
                except (MessageError, ValueError):
                    return False

        return True

    def json(self) -> Dict[str, Any]:
        """Returns the Time series block as a JSON object."""
        return {
            self.TIMEINDEX_ATTRIBUTE: self.time_index,
            self.SERIES_ATTRIBUTE: {
                attribute_name: attribute_value.json()
                for attribute_name, attribute_value in self.series.items()
            }
        }

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, self.__class__) and
            self.time_index == other.time_index and
            self.series == other.series
        )

    def __str__(self) -> str:
        return json.dumps(self.json())

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def validate_json(cls, json_timeseries_block: Dict[str, Any]) -> bool:
        """Validates the given the given json object for the attributes covered in TimeSeriesBlock class.
           Returns True if the time series block is ok. Otherwise, return False."""
        try:
            _ = cls(**json_timeseries_block)
            return True

        except (MessageError, ValueError, TypeError) as time_series_error:
            LOGGER.warning("{:s} error '{:s}' encountered when validating time series block".format(
                str(type(time_series_error)), str(time_series_error)))
            return False

    @classmethod
    def from_json(cls, json_timeseries_block: Dict[str, Any]) -> Union[TimeSeriesBlock, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON is not validated returns None."""
        if cls.validate_json(json_timeseries_block):
            return cls(**json_timeseries_block)
        return None
