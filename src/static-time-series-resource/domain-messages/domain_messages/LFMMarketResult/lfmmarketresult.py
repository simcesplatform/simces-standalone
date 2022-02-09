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
"""This module contains the message class for the simulation platform LFMMarketResult messages."""

from __future__ import annotations
from typing import Union, Dict, Any, List

from tools.exceptions.messages import MessageValueError
from tools.message.abstract import AbstractResultMessage
from tools.tools import FullLogger

import datetime
from tools.datetime_tools import to_iso_format_datetime_string
from tools.message.block import QuantityBlock, TimeSeriesBlock

LOGGER = FullLogger(__name__)

# Example:
# TimeSeriesBlock for RealPower:
#
# time_tmp = datetime.datetime.now()
# time_index_list = [to_iso_format_datetime_string(time_tmp),
#                    to_iso_format_datetime_string(time_tmp + datetime.timedelta(hours=1))]
# time_series_block_tmp = TimeSeriesBlock(time_index_list,
#                                         {"Regulation": ValueArrayBlock([2.0, 3.0],
#                                                                       "kW")})
#
# newMessage2 = LFMMarketResultMessage(**{
#     "Type": "LFMMarketResult",
#     "SimulationId": to_iso_format_datetime_string(datetime.datetime.now()),
#     "SourceProcessId": "source1",
#     "MessageId": "messageid1",
#     "EpochNumber": 1,
#     "TriggeringMessageIds": ["messageid1.1", "messageid1.2"],
#     "ActivationTime": to_iso_format_datetime_string(datetime.datetime.now()),
#     "Duration": 1.0,
#     "Direction": "upregulation",
#     "RealPower": time_series_block_tmp,
#     "Price": 2.0,
#     "CongestionId": "congestionId1",
#     "OfferId": "offerid1",
#     "ResultCount": 1,
#     "CustomerIds": ["Customer1", "Customer2"]
# })
#
# NOTE! - ResultCount is only value that requires a value
# Others can be left out or set to None (outside what AbstractResultMessage requires)
# Use this if ResultCount == 0
# (No checks on this)


class LFMMarketResultMessage(AbstractResultMessage):
    """Class containing all the attributes for an LFMMarketResult message."""

    # message type for these messages
    CLASS_MESSAGE_TYPE = "LFMMarketResult"
    MESSAGE_TYPE_CHECK = True

    # Mapping from message JSON attributes to class attributes
    MESSAGE_ATTRIBUTES = {
        "ActivationTime": "activation_time",
        "Duration": "duration",
        "Direction": "direction",
        "RealPower": "real_power",
        "Price": "price",
        "CongestionId": "congestion_id",
        "OfferId": "offer_id",
        "ResultCount": "result_count",
        "CustomerIds": "customerids"
    }
    OPTIONAL_ATTRIBUTES = []

    # Values accepted for direction
    ALLOWED_DIRECTION_VALUES = ["upregulation", "downregulation"]
    # Units accepted for price
    ALLOWED_PRICE_UNIT = "EUR"
    # RealPower units:
    REAL_POWER_UNIT = "kW"

    # Attribute names
    ATTRIBUTE_REALPOWER = "RealPower"
    ATTRIBUTE_PRICE = "Price"
    ATTRIBUTE_DURATION = "Duration"

    # attributes whose value should be a QuantityBlock and the expected unit of measure.
    QUANTITY_BLOCK_ATTRIBUTES = {
        ATTRIBUTE_DURATION: "Minute",
        ATTRIBUTE_PRICE: "EUR"
    }

    # attributes whose value should be a Array Block.
    QUANTITY_ARRAY_BLOCK_ATTRIBUTES = {}

    # attributes whose value should be a Timeseries Block.
    TIMESERIES_BLOCK_ATTRIBUTES = [ATTRIBUTE_REALPOWER]

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
        """Check that two LFMMarketResultMessages represent the same message."""
        return (
            super().__eq__(other) and
            isinstance(other, LFMMarketResultMessage) and
            self.activation_time == other.activation_time and
            self.duration == other.duration and
            self.direction == other.direction and
            self.real_power == other.real_power and
            self.price == other.price and
            self.congestion_id == other.congestion_id and
            self.offer_id == other.offer_id and
            self.result_count == other.result_count and
            self.customerids == other.customerids
        )

    @property
    def activation_time(self) -> Union[str, None]:
        """The activation time in ISO 8601 format"""
        return self.__activation_time

    @activation_time.setter
    def activation_time(self, activation_time: Union[None, str, datetime.datetime]):
        if activation_time is None:
            self.__activation_time = activation_time
            return
        if self._check_activation_time(activation_time):
            iso_format_string = to_iso_format_datetime_string(activation_time)
            if isinstance(iso_format_string, str):
                self.__activation_time = iso_format_string
                return

        raise MessageValueError("'{:s}' is an invalid ActivationTime".format(str(activation_time)))

    @classmethod
    def _check_activation_time(cls, activation_time: Union[None, str, datetime.datetime]) -> bool:
        return activation_time is None or cls._check_datetime(activation_time)

    @property
    def duration(self) -> Union[QuantityBlock, None]:
        """The duration of the request"""
        return self.__duration

    @duration.setter
    def duration(self, duration: Union[str, float, int, Dict[str, Any], QuantityBlock, None]):
        if isinstance(duration, int):
            duration = float(duration)
        if self._check_duration(duration):
            self._set_quantity_block_value(self.ATTRIBUTE_DURATION, duration)
            return

        raise MessageValueError("'{:s}' is an invalid value for {}.".format(
            str(duration), self.ATTRIBUTE_DURATION))

    @classmethod
    def _check_duration(cls, duration: Union[str, float, int, Dict[str, Any], QuantityBlock, None]) -> bool:
        return cls._check_quantity_block(
            value=duration,
            unit=cls.QUANTITY_BLOCK_ATTRIBUTES_FULL[cls.ATTRIBUTE_DURATION],
            can_be_none=True,
            float_value_check=lambda value: value >= 0.0
        )

    @property
    def direction(self) -> Union[str, None]:
        """The direction of the request"""
        return self.__direction

    @direction.setter
    def direction(self, direction: Union[str, None]):
        if self._check_direction(direction):
            self.__direction = direction
            return

        raise MessageValueError("'{:s}' is an invalid value for Direction".format(str(direction)))

    @classmethod
    def _check_direction(cls, direction: Union[str, None]) -> bool:
        if direction is None or (isinstance(direction, str) and direction in cls.ALLOWED_DIRECTION_VALUES):
            return True
        return False

    @property
    def real_power(self) -> Union[TimeSeriesBlock, None]:
        """Offered regulation as a TimeSeriesBlock"""
        return self.__real_power

    @real_power.setter
    def real_power(self, real_power: Union[TimeSeriesBlock, Dict[str, Any], None]):
        if self._check_real_power(real_power):
            self._set_timeseries_block_value(self.ATTRIBUTE_REALPOWER, real_power)
            return

        raise MessageValueError("'{:s}' is an invalid value for {}".format(str(real_power),
                                                                           self.ATTRIBUTE_REALPOWER))

    @classmethod
    def _check_real_power(cls, real_power: Union[TimeSeriesBlock, Dict[str, Any], None]) -> bool:
        return cls._check_timeseries_block(value=real_power,
                                           can_be_none=True,
                                           block_check=cls._check_real_power_block)

    @classmethod
    def _check_real_power_block(cls, real_power_block: TimeSeriesBlock) -> bool:
        block_series = real_power_block.series
        if len(block_series) < 1 or len(real_power_block.time_index) < 1:
            return False
        for value_array in block_series.values():
            if value_array.unit_of_measure != cls.REAL_POWER_UNIT:
                return False
        return True

    @property
    def price(self) -> Union[QuantityBlock, None]:
        """
        Price of the offered regulation.
        Units EUR
        """
        return self.__price

    @price.setter
    def price(self, price: Union[str, float, int, QuantityBlock, None]):
        """
        Sets the price for the offer. Sets the input price to a QuantityBlock.
        If the price is given as a QuantityBlock, uses its unit of measure.
        """
        if isinstance(price, int):
            price = float(price)
        if self._check_price(price):
            self._set_quantity_block_value(message_attribute=self.ATTRIBUTE_PRICE,
                                           quantity_value=price)
            if isinstance(price, QuantityBlock) and isinstance(self.__price, QuantityBlock):
                self.__price.unit_of_measure = price.unit_of_measure
            return

        raise MessageValueError("'{:s}' is an invalid value for {}".format(str(price),
                                                                           self.ATTRIBUTE_PRICE))

    @classmethod
    def _check_price(cls, price) -> bool:
        if isinstance(price, QuantityBlock):
            if price.unit_of_measure is not cls.ALLOWED_PRICE_UNIT:
                return False
            return cls._check_quantity_block(value=price.value,
                                             unit=price.unit_of_measure,
                                             can_be_none=True,
                                             float_value_check=lambda value: value >= 0.0)
        return cls._check_quantity_block(value=price,
                                         unit=cls.ALLOWED_PRICE_UNIT,
                                         can_be_none=True,
                                         float_value_check=lambda value: value >= 0.0)

    @property
    def congestion_id(self) -> Union[str, None]:
        """Identifier for the congestion area / specific congestion problem"""
        return self.__congestion_id

    @congestion_id.setter
    def congestion_id(self, congestion_id: Union[str, None]):
        if self._check_congestion_id(congestion_id):
            self.__congestion_id = congestion_id
            return

        raise MessageValueError("'{:s}' is an invalid value for CongestionId".format(str(congestion_id)))

    @classmethod
    def _check_congestion_id(cls, congestion_id: Union[str, None]) -> bool:
        return congestion_id is None or (isinstance(congestion_id, str) and len(congestion_id) > 0)

    @property
    def offer_id(self) -> Union[str, None]:
        """Identifier for this specific offer"""
        return self.__offer_id

    @offer_id.setter
    def offer_id(self, offer_id: Union[str, None]):
        if self._check_offer_id(offer_id):
            self.__offer_id = offer_id
            return

        raise MessageValueError("'{:s}' is an invalid value for OfferId".format(str(offer_id)))

    @classmethod
    def _check_offer_id(cls, offer_id: Union[str, None]) -> bool:
        return offer_id is None or (isinstance(offer_id, str) and len(offer_id) > 0)

    @property
    def result_count(self) -> int:
        """
        Total number of accepted offers in place the provider is going to send to the running epoch related to this
        congestion id.
        """
        return self.__result_count

    @result_count.setter
    def result_count(self, result_count: Union[str, float, int]):
        if self._check_result_count(result_count):
            self.__result_count = int(result_count)
            return

        raise MessageValueError("'{:s}' is an invalid value for ResultCount".format(str(result_count)))

    @classmethod
    def _check_result_count(cls, result_count: Union[str, float, int]) -> bool:
        if result_count is None or not isinstance(result_count, (str, float, int)):
            return False
        if isinstance(result_count, str):
            try:
                result_count = float(result_count)
            except ValueError:
                return False
        return result_count >= 0 and (isinstance(result_count, int) or result_count.is_integer())

    @property
    def customerids(self) -> Union[List[str], None]:
        return self.__customerids

    @customerids.setter
    def customerids(self, customerids: Union[List[str], None]):
        if self._check_customerids(customerids):
            self.__customerids = customerids
            return

        raise MessageValueError("'{:s}' is an invalid value for CustomerIds".format(str(customerids)))

    @classmethod
    def _check_customerids(cls, customerids: Union[List[str], None]) -> bool:
        if customerids is None:
            return True
        if isinstance(customerids, list):
            if len(customerids) > 0:
                for customer in customerids:
                    if not isinstance(customer, str):
                        return False
                return True
        return False

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[LFMMarketResultMessage, None]:
        if cls.validate_json(json_message):
            return LFMMarketResultMessage(**json_message)
        return None


LFMMarketResultMessage.register_to_factory()
