# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>
#            Otto Hylli <otto.hylli@tuni.fi>

"""This module contains the abstract base classes for the simulation platform messages."""

from __future__ import annotations
import datetime
import json
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from tools.datetime_tools import get_utcnow_in_milliseconds, to_iso_format_datetime_string
from tools.exceptions.messages import (
    MessageDateError, MessageIdError, MessageSourceError, MessageTypeError,
    MessageValueError, MessageEpochValueError, MessageBlockError)
from tools.message.block import QuantityArrayBlock, QuantityBlock, TimeSeriesBlock
from tools.message.factory import MessageFactory
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)

# These attributes will be generated if they are not given when creating message objects.
OPTIONALLY_GENERATED_ATTRIBUTES = [
    "Timestamp"
]


def get_json(message_object: BaseMessage) -> Dict[str, Any]:
    """Returns a JSON based on the values of the given message_object and the attribute parameters."""
    return {
        json_attribute_name: (
            getattr(message_object, object_attribute_name)
            if not hasattr(getattr(message_object, object_attribute_name), 'json')
            else getattr(message_object, object_attribute_name).json()
        )
        for json_attribute_name, object_attribute_name in message_object.__class__.MESSAGE_ATTRIBUTES_FULL.items()
        if (json_attribute_name not in message_object.__class__.OPTIONAL_ATTRIBUTES_FULL or
            getattr(message_object, object_attribute_name) is not None)
    }


def validate_json(message_class: Type[BaseMessage], json_message: Dict[str, Any]) -> bool:
    """Validates the given the given json object for the attributes covered in the given message class.
        Returns True if the message is ok. Otherwise, return False."""
    for json_attribute_name, object_attribute_name in message_class.MESSAGE_ATTRIBUTES_FULL.items():
        if json_attribute_name not in json_message and json_attribute_name in OPTIONALLY_GENERATED_ATTRIBUTES:
            continue

        if (json_attribute_name not in json_message and
                json_attribute_name not in message_class.OPTIONAL_ATTRIBUTES_FULL):
            LOGGER.warning("{:s} attribute is missing from the message".format(json_attribute_name))
            return False

        if not getattr(
                message_class,
                "_".join(["_check", object_attribute_name]))(json_message.get(json_attribute_name, None)):
            # TODO: handle checking for missing timezone information
            LOGGER.warning("'{:s}' is not valid message value for {:s}".format(
                str(json_message[json_attribute_name]), json_attribute_name))
            return False

    return True


class BaseMessage():
    """The base message class for all simulation platform messages."""
    MESSAGE_ENCODING = "UTF-8"
    # The "Type" attribute is checked against CLASS_MESSAGE_TYPE if MESSAGE_TYPE_CHECK is True.
    # For example, for EpochMessage, "Type" must be "Epoch", but for AbstractMessage any string is acceptable.
    CLASS_MESSAGE_TYPE = ""
    MESSAGE_TYPE_CHECK = False

    # The relationships between the JSON attributes and the object properties
    MESSAGE_ATTRIBUTES = {
        "Type": "message_type",
        "SimulationId": "simulation_id",
        "Timestamp": "timestamp"
    }
    # Attributes that can be missing from the message. Missing attributes are set to value None.
    OPTIONAL_ATTRIBUTES = []

    # attributes whose value is a QuantityBlock and the expected unit of measure.
    # https://wiki.eduuni.fi/display/tuniSimCES/Quantity+block
    QUANTITY_BLOCK_ATTRIBUTES = {}
    # attributes whose value is a QuantityArrayBlock and the expected unit of measure.
    # https://wiki.eduuni.fi/display/tuniSimCES/Quantity+array+block
    QUANTITY_ARRAY_BLOCK_ATTRIBUTES = {}
    # a list of attributes whose value is a TimeSeriesBlock.
    # https://wiki.eduuni.fi/pages/viewpage.action?spaceKey=tuniSimCES&title=Time+series+block
    TIMESERIES_BLOCK_ATTRIBUTES = []

    # Full list af all attribute names, any subclass should update these with additional names.
    MESSAGE_ATTRIBUTES_FULL = MESSAGE_ATTRIBUTES
    OPTIONAL_ATTRIBUTES_FULL = OPTIONAL_ATTRIBUTES
    QUANTITY_BLOCK_ATTRIBUTES_FULL = QUANTITY_BLOCK_ATTRIBUTES
    QUANTITY_ARRAY_BLOCK_ATTRIBUTES_FULL = QUANTITY_ARRAY_BLOCK_ATTRIBUTES
    TIMESERIES_BLOCK_ATTRIBUTES_FULL = TIMESERIES_BLOCK_ATTRIBUTES

    DEFAULT_SIMULATION_ID = "2000-01-01T00:00:00.000Z"

    def __init__(self, **kwargs):
        """Only arguments in MESSAGE_ATTRIBUTES_FULL of the message class are considered.
           If Timestamp is missing, it is added with a value corresponding to the current time.
           If one the arguments is not valid, throws an instance of MessageError.
        """
        for json_attribute_name in self.__class__.MESSAGE_ATTRIBUTES_FULL:
            setattr(self, self.__class__.MESSAGE_ATTRIBUTES_FULL[json_attribute_name],
                    kwargs.get(json_attribute_name, None))

    @property
    def message_type(self) -> str:
        """The message type attribute."""
        return self.__message_type

    @property
    def simulation_id(self) -> str:
        """The simulation id."""
        return self.__simulation_id

    @property
    def timestamp(self) -> str:
        """The timestamp for the message in ISO 8601 format."""
        return self.__timestamp

    @message_type.setter
    def message_type(self, message_type: str):
        if not self._check_message_type(message_type):
            raise MessageTypeError("'{:s}' is not an allowed message type".format(str(message_type)))
        self.__message_type = message_type

    @simulation_id.setter
    def simulation_id(self, simulation_id: str):
        if self._check_simulation_id(simulation_id):
            iso_format_string = to_iso_format_datetime_string(simulation_id)
            if isinstance(iso_format_string, str):
                self.__simulation_id = iso_format_string
                return
        raise MessageDateError("'{:s}' is an invalid datetime".format(str(simulation_id)))

    @timestamp.setter
    def timestamp(self, timestamp: Union[str, datetime.datetime, None]):
        if timestamp is None:
            self.__timestamp = get_utcnow_in_milliseconds()
        else:
            if self._check_timestamp(timestamp):
                iso_format_string = to_iso_format_datetime_string(timestamp)
                if isinstance(iso_format_string, str):
                    self.__timestamp = iso_format_string
                    return

            raise MessageDateError("'{:s}' is an invalid datetime".format(str(timestamp)))

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, BaseMessage) and
            self.simulation_id == other.simulation_id and
            self.timestamp == other.timestamp
        )

    def __str__(self) -> str:
        return json.dumps(self.json())

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def _check_datetime(cls, datetime_value: Union[str, datetime.datetime]) -> bool:
        return to_iso_format_datetime_string(datetime_value) is not None

    @classmethod
    def _check_message_type(cls, message_type: str) -> bool:
        if cls.MESSAGE_TYPE_CHECK:
            return message_type == cls.CLASS_MESSAGE_TYPE
        return isinstance(message_type, str)

    @classmethod
    def _check_simulation_id(cls, simulation_id: str) -> bool:
        return cls._check_datetime(simulation_id)

    @classmethod
    def _check_timestamp(cls, timestamp: Union[str, datetime.datetime]) -> bool:
        return cls._check_datetime(timestamp)

    @classmethod
    def _check_quantity_block(cls, value: Union[str, float, QuantityBlock, dict, None],
                              unit: str,
                              can_be_none: bool = False,
                              float_value_check: Callable[[float], bool] = None) -> bool:
        """Check that value for quantity block is valid.
        value: The value to be checked. String can be converted to float or the given QuantityBlock has the given unit
        or the dict has the required attributes and correct unit.
        unit: The unit of measure expected.
        can_be_none: Should a None value be accepted.
        float_value_check: Optional additional check for the float value for example if it has to be positive.
                           Must be a callable which accepts a float argument and returns a boolean.
        """
        if value is None:
            return can_be_none

        # extra check to avoid illegal value types
        if not isinstance(value, (str, float, QuantityBlock, dict)):
            return False

        if isinstance(value, (QuantityBlock, dict)):
            if isinstance(value, dict):
                if not QuantityBlock.validate_json(value):
                    return False
                value = QuantityBlock(**value)

            return value.unit_of_measure == unit and (float_value_check is None or float_value_check(value.value))

        try:
            value = float(value)
            return float_value_check is None or float_value_check(value)

        except (ValueError, TypeError):
            return False

    def _set_quantity_block_value(self, message_attribute: str,
                                  quantity_value: Union[str, float, QuantityBlock, Dict[str, Any], None]):
        """Set value for a quantity block attribute.

        message_attribute: Name of the message attribute e.g. RealPower whose value is set.
        quantity_value: The value to be set which can be float, string, dict, QuantityBlock or None.
        A string value is converted to a float. A float value is converted into a QuantityBlock with the
        default unit for the attribute.
        A dict is assumed to have Value and UnitOfMeasure keys and is converted to a QuantityBlock.

        Throws MessageBlockError if the message_attribute has not been included in QUANTITY_BLOCK_ATTRIBUTES_FULL.
        """
        if message_attribute not in self.QUANTITY_BLOCK_ATTRIBUTES_FULL:
            LOGGER.warning("Attribute {:s} is not registered as a quantity block".format(message_attribute))
            raise MessageBlockError(
                "Attribute {:s} is not registered as a quantity block".format(message_attribute))

        unit = self.QUANTITY_BLOCK_ATTRIBUTES_FULL[message_attribute]
        if isinstance(quantity_value, dict):
            quantity_value = QuantityBlock(**quantity_value)

        elif quantity_value is not None and not isinstance(quantity_value, QuantityBlock):
            quantity_value = QuantityBlock(Value=float(quantity_value), UnitOfMeasure=unit)

        # set value for the attribute
        # Note: attribute name has to include the class name to be of use in subclasses since that is what
        #       the Python interpreter actually uses for self.__attribute_name
        setattr(
            self,
            "_" + self.__class__.__name__ + "__" + self.MESSAGE_ATTRIBUTES_FULL[message_attribute],
            quantity_value)

    @classmethod
    def _check_quantity_array_block(cls, value: Union[List[float], QuantityArrayBlock,
                                                      Dict[str, Union[str, List[float]]], None],
                                    unit: str,
                                    can_be_none: bool = False,
                                    value_array_check: Callable[[List[float]], bool] = None) -> bool:
        """Check that the value for quantity array block is valid.

        value:             The value to be checked.
                           A dictionary has to in a form that can be used to construct a QuantityArrayBlock object.
                           A QuantityArrayBlock has to have the expected unit.
        unit:              The unit of measure expected.
        can_be_none:       Should a None value be accepted.
        value_array_check: Optional additional check for the quantity array. For example if it only positive values
                           are allowed or the length of the value array is required to be a some fixed number.
                           Must be a callable which accepts a list of floats as argument and returns a boolean.
        """
        if value is None:
            return can_be_none

        # extra check to avoid illegal value types
        if not isinstance(value, (list, QuantityArrayBlock, dict)):
            return False

        if isinstance(value, list):
            for list_item in value:
                if not isinstance(list_item, float):
                    return False
            return value_array_check is None or value_array_check(value)

        if isinstance(value, dict):
            if not QuantityArrayBlock.validate_json(value):
                return False
            value = QuantityArrayBlock(**value)  # pyright: reportGeneralTypeIssues=false

        return value.unit_of_measure == unit and (value_array_check is None or value_array_check(value.values))

    def _set_quantity_array_block_value(
            self, message_attribute: str,
            quantity_array_value: Union[List[float], QuantityArrayBlock, Dict[str, Union[str, List[float]]], None]):
        """Sets value for a quantity array block attribute.

        message_attribute:     Name of the message attribute e.g. RatedCurrent whose value is set.
        quantity_array_value:  The value to be set which can be either a dictionary, QuantityArrayBlock or None.
        A dictionary should follow the definition of time series block and it is converted to a QuantityArrayBlock.

        Throws MessageBlockError if the message_attribute has not been included in QUANTITY_ARRAY_BLOCK_ATTRIBUTES_FULL.
        If the quantity_array_value contains invalid values, throws an appropriate exception.
        """
        if message_attribute not in self.QUANTITY_ARRAY_BLOCK_ATTRIBUTES_FULL:
            LOGGER.warning("Attribute {:s} is not registered as a quantity array block".format(message_attribute))
            raise MessageBlockError(
                "Attribute {:s} is not registered as a quantity array block".format(message_attribute))

        if isinstance(quantity_array_value, list):
            unit = self.QUANTITY_ARRAY_BLOCK_ATTRIBUTES_FULL[message_attribute]
            quantity_array_value = QuantityArrayBlock(Values=quantity_array_value, UnitOfMeasure=unit)

        elif isinstance(quantity_array_value, dict):
            quantity_array_value = QuantityArrayBlock(**quantity_array_value)

        # set value for the attribute
        # Note: attribute name has to include the class name to be of use in subclasses since that is what
        #       the Python interpreter actually uses for self.__attribute_name
        setattr(
            self,
            "_" + self.__class__.__name__ + "__" + self.MESSAGE_ATTRIBUTES_FULL[message_attribute],
            quantity_array_value)

    @classmethod
    def _check_timeseries_block(cls, value: Union[TimeSeriesBlock, Dict[str, Any], None],
                                can_be_none: bool = False,
                                block_check: Callable[[TimeSeriesBlock], bool] = None) -> bool:
        """Check that value for time series block is valid.

        value:       The value to be checked.
                     A dictionary has to in a form that can be used to construct a TimeSeriesBlock object.
        can_be_none: Should a None value be accepted.
        block_check: Optional additional check for the time series value. For example if it only certain value series
                     names are allowed or the length of the value series is required to be a some fixed number.
                     Must be a callable which accepts a TimeSeriesBlock argument and returns a boolean.
        """
        if value is None:
            return can_be_none

        # extra check to avoid illegal value types
        if not isinstance(value, (TimeSeriesBlock, dict)):
            return False

        if isinstance(value, dict):
            if not TimeSeriesBlock.validate_json(value):
                return False
            value = TimeSeriesBlock(**value)

        return block_check is None or block_check(value)

    def _set_timeseries_block_value(self, message_attribute: str,
                                    timeseries_value: Union[TimeSeriesBlock, Dict[str, Any], None]):
        """Sets value for a timeseries block attribute.

        message_attribute: Name of the message attribute e.g. Prices whose value is set.
        timeseries_value:  The value to be set which can be either a dictionary, TimeSeriesBlock or None.
        A dictionary should follow the definition of time series block and it is converted to a TimeSeriesBlock.

        Throws MessageBlockError if the message_attribute has not been included in TIMESERIES_BLOCK_ATTRIBUTES_FULL.
        If the timeseries_value contains invalid values, throws an appropriate exception.
        """
        if message_attribute not in self.TIMESERIES_BLOCK_ATTRIBUTES_FULL:
            LOGGER.warning("Attribute {:s} is not registered as an time series block".format(message_attribute))
            raise MessageBlockError(
                "Attribute {:s} is not registered as an time series block".format(message_attribute))

        if isinstance(timeseries_value, dict):
            timeseries_value = TimeSeriesBlock(**timeseries_value)

        # set value for the attribute
        # Note: attribute name has to include the class name to be of use in subclasses since that is what
        #       the Python interpreter actually uses for self.__attribute_name
        setattr(
            self,
            "_" + self.__class__.__name__ + "__" + self.MESSAGE_ATTRIBUTES_FULL[message_attribute],
            timeseries_value)

    def json(self) -> Dict[str, Any]:
        """Returns the message as a JSON object."""
        return get_json(self)

    def bytes(self):
        """Returns the message in bytes format."""
        return bytes(json.dumps(self.json()), encoding=self.__class__.MESSAGE_ENCODING)

    @classmethod
    def validate_json(cls, json_message: Dict[str, Any]) -> bool:
        """Validates the given the given json object for the attributes covered in the given class.
           Returns True if the message is ok. Otherwise, return False."""
        return validate_json(cls, json_message)

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[BaseMessage, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON does not contain valid values, returns None."""
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None

    @classmethod
    def register_to_factory(cls):
        """Registers this message class to the MessageFactory."""
        if cls.CLASS_MESSAGE_TYPE == "":
            LOGGER.warning("Cannot register message class with empty message type to the message factory")
        else:
            MessageFactory.register_message_type(cls)


class AbstractMessage(BaseMessage):
    """The abstract message class that contains the attributes that all simulation specific messages should have."""

    # The relationships between the JSON attributes and the object properties
    MESSAGE_ATTRIBUTES = {
        "SourceProcessId": "source_process_id",
        "MessageId": "message_id"
    }
    # Attributes that can be missing from the message. Missing attributes are set to value None.
    OPTIONAL_ATTRIBUTES = []

    # Full list af all attribute names, any subclass should update these with additional names.
    MESSAGE_ATTRIBUTES_FULL = {
        **BaseMessage.MESSAGE_ATTRIBUTES_FULL,
        **MESSAGE_ATTRIBUTES
    }
    OPTIONAL_ATTRIBUTES_FULL = BaseMessage.OPTIONAL_ATTRIBUTES_FULL + OPTIONAL_ATTRIBUTES

    @property
    def source_process_id(self) -> str:
        """The source process id."""
        return self.__source_process_id

    @property
    def message_id(self) -> str:
        """The message id."""
        return self.__message_id

    @source_process_id.setter
    def source_process_id(self, source_process_id: str):
        if not self._check_source_process_id(source_process_id):
            raise MessageSourceError("'{:s}' is an invalid source process id".format(str(source_process_id)))
        self.__source_process_id = source_process_id

    @message_id.setter
    def message_id(self, message_id: str):
        if not self._check_message_id(message_id):
            raise MessageIdError("'{:s}' is an invalid message id".format(str(message_id)))
        self.__message_id = message_id

    def __eq__(self, other: Any) -> bool:
        return (
            super().__eq__(other) and
            isinstance(other, AbstractMessage) and
            self.message_type == other.message_type and
            self.source_process_id == other.source_process_id and
            self.message_id == other.message_id
        )

    @classmethod
    def _check_source_process_id(cls, source_process_id: str) -> bool:
        return isinstance(source_process_id, str) and len(source_process_id) > 0

    @classmethod
    def _check_message_id(cls, message_id: str) -> bool:
        return isinstance(message_id, str) and len(message_id) > 0

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[AbstractMessage, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON does not contain valid values, returns None."""
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None


class AbstractResultMessage(AbstractMessage):
    """The abstract result message class that contains the attributes that all result messages have."""
    CLASS_MESSAGE_TYPE = ""

    MESSAGE_ATTRIBUTES = {
        "EpochNumber": "epoch_number",
        "LastUpdatedInEpoch": "last_updated_in_epoch",
        "TriggeringMessageIds": "triggering_message_ids",
        "Warnings": "warnings",
        "IterationStatus": "iteration_status"
    }
    OPTIONAL_ATTRIBUTES = ["LastUpdatedInEpoch", "Warnings", "IterationStatus"]

    MESSAGE_ATTRIBUTES_FULL = {
        **AbstractMessage.MESSAGE_ATTRIBUTES_FULL,
        **MESSAGE_ATTRIBUTES
    }
    OPTIONAL_ATTRIBUTES_FULL = AbstractMessage.OPTIONAL_ATTRIBUTES_FULL + OPTIONAL_ATTRIBUTES

    # Any valid warning must start with one of the following.
    WARNING_TYPES = [
        "warning.convergence",
        "warning.input",
        "warning.input-range",
        "warning.input-unreliable",
        "warning.internal",
        "warning.other"
    ]

    # If the iteration status is given, it must be one of the following.
    ITERATION_STATUS_VALUES = [
        "intermediate",
        "final"
    ]

    @property
    def epoch_number(self) -> int:
        """The epoch number attribute."""
        return self.__epoch_number

    @property
    def last_updated_in_epoch(self) -> Optional[int]:
        """The last updated in epoch attribute. It is either an epoch number or None."""
        return self.__last_updated_in_epoch

    @property
    def triggering_message_ids(self) -> List[str]:
        """The triggering message ids attribute. It is a non-empty list."""
        return self.__triggering_message_ids

    @property
    def warnings(self) -> Optional[List[str]]:
        """The warnings attribute. It is either None or a non-empty list."""
        return self.__warnings

    @property
    def iteration_status(self) -> Optional[str]:
        """The iteration status attribute. It is either None or one of the allowed string values."""
        return self.__iteration_status

    @epoch_number.setter
    def epoch_number(self, epoch_number: int):
        if not self._check_epoch_number(epoch_number):
            raise MessageEpochValueError("'{:s}' is not a valid epoch number".format(str(epoch_number)))
        self.__epoch_number = epoch_number

    @last_updated_in_epoch.setter
    def last_updated_in_epoch(self, last_updated_in_epoch: Union[int, None]):
        if not self._check_last_updated_in_epoch(last_updated_in_epoch):
            raise MessageEpochValueError("'{:s}' is not a valid epoch number".format(str(last_updated_in_epoch)))
        self.__last_updated_in_epoch = last_updated_in_epoch

    @triggering_message_ids.setter
    def triggering_message_ids(self, triggering_message_ids: Union[List[str], Tuple[str]]):
        if not self._check_triggering_message_ids(triggering_message_ids):
            raise MessageIdError("'{:s}' is not a valid list of message ids".format(str(triggering_message_ids)))
        self.__triggering_message_ids = list(triggering_message_ids)

    @warnings.setter
    def warnings(self, warnings: Union[List[str], Tuple[str], None]):
        if not self._check_warnings(warnings):
            raise MessageValueError("'{:s}' is not a valid list of warnings".format(str(warnings)))
        if warnings is None or (isinstance(warnings, (list, tuple)) and len(warnings) == 0):
            self.__warnings = None
        else:
            self.__warnings = list(warnings)

    @iteration_status.setter
    def iteration_status(self, iteration_status: Optional[str]):
        if not self._check_iteration_status(iteration_status):
            raise MessageValueError("'{}' is not a valid value for iteration status".format(iteration_status))
        self.__iteration_status = iteration_status

    def __eq__(self, other: Any) -> bool:
        return (
            super().__eq__(other) and
            isinstance(other, AbstractResultMessage) and
            self.epoch_number == other.epoch_number and
            self.last_updated_in_epoch == other.last_updated_in_epoch and
            self.triggering_message_ids == other.triggering_message_ids and
            self.warnings == other.warnings and
            self.iteration_status == other.iteration_status
        )

    @classmethod
    def _check_epoch_number(cls, epoch_number) -> bool:
        # epoch number 0 is reserved for the initialization phase
        return isinstance(epoch_number, int) and epoch_number >= 0

    @classmethod
    def _check_last_updated_in_epoch(cls, last_updated_in_epoch: Union[int, None]) -> bool:
        return last_updated_in_epoch is None or cls._check_epoch_number(last_updated_in_epoch)

    @classmethod
    def _check_triggering_message_ids(cls, triggering_message_ids: Union[List[str], Tuple[str]]) -> bool:
        if (triggering_message_ids is None or
                not isinstance(triggering_message_ids, (list, tuple)) or
                len(triggering_message_ids) == 0):
            return False
        for triggering_message_id in triggering_message_ids:
            if not cls._check_message_id(triggering_message_id):
                return False
        return True

    @classmethod
    def _check_warnings(cls, warnings: Union[List[str], Tuple[str], None]) -> bool:
        if warnings is None:
            return True
        if not isinstance(warnings, (list, tuple)):
            return False

        # the warnings must all start with one of the predefined base warnings
        for warning in warnings:
            validity_check = False
            for valid_warning in cls.WARNING_TYPES:
                validity_check = warning.startswith(valid_warning)
                if validity_check:
                    # jump to checking the next warning in the warnings list
                    break

            if not validity_check:
                return False

        return True

    @classmethod
    def _check_iteration_status(cls, iteration_status: Optional[str]) -> bool:
        return iteration_status is None or iteration_status in cls.ITERATION_STATUS_VALUES

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[AbstractResultMessage, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON does not contain valid values, returns None."""
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None
