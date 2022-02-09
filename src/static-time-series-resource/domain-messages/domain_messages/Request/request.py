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
"""This module contains the message class for the simulation platform request messages."""

from __future__ import annotations
from typing import Union, List, Dict, Any

from tools.exceptions.messages import MessageValueError
from tools.message.abstract import AbstractResultMessage
from tools.tools import FullLogger

import datetime
from tools.datetime_tools import to_iso_format_datetime_string
from tools.message.block import QuantityBlock

LOGGER = FullLogger(__name__)

# Example:
# newMessage = RequestMessage(**{
#     "Type": "Request",
#     "SimulationId": to_iso_format_datetime_string(datetime.datetime.now()),
#     "SourceProcessId": "source1",
#     "MessageId": "messageid1",
#     "EpochNumber": 1,
#     "TriggeringMessageIds": ["messageid1.1","messageid1.2"],
#     "ActivationTime": datetime.datetime.now(),
#     "Duration": "1",
#     "Direction": "downregulation",
#     "RealPowerMin": 1.0,
#     "RealPowerRequest": 2.0,
#     "CustomerIds": "id1",
#     "CongestionId": "congestionId1",
#     "BidResolution": 0.1
# })


class RequestMessage(AbstractResultMessage):
    """Class containing all the attributes for a Request message."""

    # message type for these messages
    CLASS_MESSAGE_TYPE = "Request"
    MESSAGE_TYPE_CHECK = True

    # Mapping from message JSON attributes to class attributes
    MESSAGE_ATTRIBUTES = {
        "ActivationTime": "activation_time",
        "Duration": "duration",
        "Direction": "direction",
        "RealPowerMin": "real_power_min",
        "RealPowerRequest": "real_power_request",
        "CustomerIds": "customer_ids",
        "CongestionId": "congestion_id",
        "BidResolution": "bid_resolution"
    }
    OPTIONAL_ATTRIBUTES = ["BidResolution"]

    # Values accepted for direction
    ALLOWED_DIRECTION_VALUES = ["upregulation", "downregulation"]

    # Attribute names
    ATTRIBUTE_DURATION = "Duration"
    ATTRIBUTE_REALPOWERMIN = "RealPowerMin"
    ATTRIBUTE_REALPOWERREQUEST = "RealPowerRequest"
    ATTRIBUTE_BIDRESOLUTION = "BidResolution"

    # attributes whose value should be a QuantityBlock and the expected unit of measure.
    QUANTITY_BLOCK_ATTRIBUTES = {
        ATTRIBUTE_DURATION: "Minute",
        ATTRIBUTE_REALPOWERMIN: "kW",
        ATTRIBUTE_REALPOWERREQUEST: "kW",
        ATTRIBUTE_BIDRESOLUTION: "kW"
    }

    # attributes whose value should be a Array Block.
    QUANTITY_ARRAY_BLOCK_ATTRIBUTES = {}

    # attributes whose value should be a Timeseries Block.
    TIMESERIES_BLOCK_ATTRIBUTES = []

    MESSAGE_ATTRIBUTES_FULL = {
        **AbstractResultMessage.MESSAGE_ATTRIBUTES_FULL,
        **MESSAGE_ATTRIBUTES
    }
    OPTIONAL_ATTRIBUTES_FULL = AbstractResultMessage.OPTIONAL_ATTRIBUTES_FULL + OPTIONAL_ATTRIBUTES
    QUANTITY_BLOCK_ATTRIBUTES_FULL = {
        **AbstractResultMessage.QUANTITY_BLOCK_ATTRIBUTES_FULL,
        **QUANTITY_BLOCK_ATTRIBUTES
    }
    QUANTITY_ARRAY_BLOCK_ATTRIBUTES_FULL = {
        **AbstractResultMessage.QUANTITY_ARRAY_BLOCK_ATTRIBUTES_FULL,
        **QUANTITY_ARRAY_BLOCK_ATTRIBUTES
    }
    TIMESERIES_BLOCK_ATTRIBUTES_FULL = (
        AbstractResultMessage.TIMESERIES_BLOCK_ATTRIBUTES_FULL +
        TIMESERIES_BLOCK_ATTRIBUTES
    )

    def __eq__(self, other: Any) -> bool:
        """Check that two RequestMessages represent the same message."""
        return (
            super().__eq__(other) and
            isinstance(other, RequestMessage) and
            self.activation_time == other.activation_time and
            self.duration == other.duration and
            self.direction == other.direction and
            self.real_power_min == other.real_power_min and
            self.real_power_request == other.real_power_request and
            self.customer_ids == other.customer_ids and
            self.congestion_id == other.congestion_id and
            self.bid_resolution == other.bid_resolution
        )

    @property
    def activation_time(self) -> str:
        """
        The activation time in ISO 8601 format.
        Set as either a string or datetime.
        """
        return self.__activation_time

    @activation_time.setter
    def activation_time(self, activation_time: Union[str, datetime.datetime]):
        if self._check_activation_time(activation_time):
            iso_format_string = to_iso_format_datetime_string(activation_time)
            if isinstance(iso_format_string, str):
                self.__activation_time = iso_format_string
                return

        raise MessageValueError("'{:s}' is an invalid datetime".format(str(activation_time)))

    @classmethod
    def _check_activation_time(cls, activation_time: Union[str, datetime.datetime]) -> bool:
        return cls._check_datetime(activation_time)

    @property
    def duration(self) -> QuantityBlock:
        """
        The duration of the request.
        Set as a positive value. Units in minutes.
        """
        return self.__duration

    @duration.setter
    def duration(self, duration: Union[str, float, int, Dict[str, Any], QuantityBlock]):
        if isinstance(duration, int):
            duration = float(duration)
        if self._check_duration(duration):
            self._set_quantity_block_value(self.ATTRIBUTE_DURATION, duration)
            return

        raise MessageValueError("'{:s}' is an invalid value for {}.".format(str(duration),
                                                                            self.ATTRIBUTE_DURATION))

    @classmethod
    def _check_duration(cls, duration: Union[str, float, int, Dict[str, Any], QuantityBlock]) -> bool:
        return cls._check_quantity_block(duration,
                                         cls.QUANTITY_BLOCK_ATTRIBUTES_FULL[cls.ATTRIBUTE_DURATION],
                                         False,
                                         lambda value: value >= 0.0)

    @property
    def direction(self) -> str:
        """
        The direction of the request.
        Value either "upregulation" or "downregulation".
        """
        return self.__direction

    @direction.setter
    def direction(self, direction: str):
        if self._check_direction(direction):
            self.__direction = direction
            return

        raise MessageValueError("'{:s}' is an invalid value for direction".format(str(direction)))

    @classmethod
    def _check_direction(cls, direction: str) -> bool:
        if isinstance(direction, str) and direction in cls.ALLOWED_DIRECTION_VALUES:
            return True
        return False

    @property
    def real_power_min(self) -> QuantityBlock:
        """Minimum bid in kW"""
        return self.__real_power_min

    @real_power_min.setter
    def real_power_min(self, real_power_min: Union[str, float, int, Dict[str, Any], QuantityBlock]):
        if isinstance(real_power_min, int):
            real_power_min = float(real_power_min)
        if self._check_real_power_min(real_power_min):
            self._set_quantity_block_value(self.ATTRIBUTE_REALPOWERMIN, real_power_min)
            return

        raise MessageValueError("'{:s}' is an invalid value for {}.".format(str(real_power_min),
                                                                            self.ATTRIBUTE_REALPOWERMIN))

    @classmethod
    def _check_real_power_min(cls, real_power_min: Union[str, float, int, Dict[str, Any], QuantityBlock]) -> bool:
        return cls._check_quantity_block(real_power_min,
                                         cls.QUANTITY_BLOCK_ATTRIBUTES_FULL[cls.ATTRIBUTE_REALPOWERMIN],
                                         False, lambda value: value >= 0.0)

    @property
    def real_power_request(self) -> QuantityBlock:
        """Maximum bid in kW"""
        return self.__real_power_request

    @real_power_request.setter
    def real_power_request(self, real_power_request: Union[str, float, int, Dict[str, Any], QuantityBlock]):
        if isinstance(real_power_request, int):
            real_power_request = float(real_power_request)
        if self._check_real_power_request(real_power_request):
            self._set_quantity_block_value(self.ATTRIBUTE_REALPOWERREQUEST, real_power_request)
            return

        raise MessageValueError("'{:s}' is an invalid value for {}.".format(str(real_power_request),
                                                                            self.ATTRIBUTE_REALPOWERREQUEST))

    @classmethod
    def _check_real_power_request(cls, real_power_request: Union[str, float, int, Dict[str, Any], QuantityBlock]) -> bool:
        return cls._check_quantity_block(real_power_request,
                                         cls.QUANTITY_BLOCK_ATTRIBUTES_FULL[cls.ATTRIBUTE_REALPOWERREQUEST],
                                         False,
                                         lambda value: value >= 0.0)

    @property
    def customer_ids(self) -> List[str]:
        """List of customer ids request is targeted at"""
        return self.__customer_ids

    @customer_ids.setter
    def customer_ids(self, customer_ids: Union[str, List[str]]):
        if self._check_customer_ids(customer_ids):
            self.__customer_ids = list(customer_ids)
            return

        raise MessageValueError("'{}' is an invalid value for CustomerIds.".format(customer_ids))

    @classmethod
    def _check_customer_ids(cls, customer_ids: Union[str, List[str]]) -> bool:
        if customer_ids is None:
            return False
        if (not isinstance(customer_ids, (str, list)) or len(customer_ids) == 0):
            return False
        if not isinstance(customer_ids, str):
            for customer_id in customer_ids:
                if not isinstance(customer_id, str):
                    return False
        return True

    @property
    def congestion_id(self) -> str:
        """Identifier for the congestion area / specific congestion problem"""
        return self.__congestion_id

    @congestion_id.setter
    def congestion_id(self, congestion_id: str):
        if self._check_congestion_id(congestion_id):
            self.__congestion_id = congestion_id
            return

        raise MessageValueError("Invalid value, {}, for attribute: congestion_id".format(congestion_id))

    @classmethod
    def _check_congestion_id(cls, congestion_id: str) -> bool:
        return isinstance(congestion_id, str) and len(congestion_id) > 0

    @property
    def bid_resolution(self) -> Union[QuantityBlock, None]:
        """Resolution for the bids"""
        return self.__bid_resolution

    @bid_resolution.setter
    def bid_resolution(self, bid_resolution: Union[str, float, int, Dict[str, Any], QuantityBlock, None]):
        if isinstance(bid_resolution, int):
            bid_resolution = float(bid_resolution)
        if self._check_bid_resolution(bid_resolution):
            if bid_resolution is None:
                self.__bid_resolution = None
                return
            self._set_quantity_block_value(self.ATTRIBUTE_BIDRESOLUTION, bid_resolution)
            return

        raise MessageValueError("'{:s}' is an invalid value for {}.".format(str(bid_resolution),
                                                                            self.ATTRIBUTE_BIDRESOLUTION))

    @classmethod
    def _check_bid_resolution(cls, bid_resolution: Union[str, float, int, Dict[str, Any], QuantityBlock, None]) -> bool:
        return cls._check_quantity_block(bid_resolution,
                                         cls.QUANTITY_BLOCK_ATTRIBUTES_FULL[cls.ATTRIBUTE_BIDRESOLUTION],
                                         True,
                                         lambda value: value >= 0.0)

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[RequestMessage, None]:
        if cls.validate_json(json_message):
            return RequestMessage(**json_message)
        return None


RequestMessage.register_to_factory()
