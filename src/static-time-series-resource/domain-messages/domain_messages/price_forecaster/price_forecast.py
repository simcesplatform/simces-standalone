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
"""This module contains the message class for the simulation platform price forecast messages."""

from __future__ import annotations
from typing import Any, Dict, List, Union

from tools.exceptions.messages import MessageValueError
from tools.message.abstract import AbstractResultMessage, AbstractMessage
from tools.message.block import QuantityBlock, QuantityArrayBlock, TimeSeriesBlock
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class PriceForecastStateMessage(AbstractResultMessage):
    """Class containing all the attributes for a PriceForecastState message."""

    # message type for these messages
    CLASS_MESSAGE_TYPE = "PriceForecastState"
    MESSAGE_TYPE_CHECK = True

    ALLOWED_Price_UNITS = ["{EUR}/(kW.h)", "{EUR}/(MW.h)"]

    # Mapping from message JSON attributes to class attributes
    MESSAGE_ATTRIBUTES = {
        "MarketId": "marketid",
        "Prices": "prices",
        "ResourceId": "resourceid",
        "PricingType": "pricingtype"
    }
    OPTIONAL_ATTRIBUTES = ["ResourceId", "PricingType"]

    # attributes whose value should be a Quantity Block.
    QUANTITY_BLOCK_ATTRIBUTES = {}

    # attributes whose value should be a Array Block.
    QUANTITY_ARRAY_BLOCK_ATTRIBUTES = {}

    # attributes whose value should be a Timeseries Block.
    TIMESERIES_BLOCK_ATTRIBUTES = [
        "Prices"
    ]


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


    @property
    def marketid(self) -> str:
        """The attribute for the id of the market."""
        return self.__marketid

    @property
    def prices(self) -> TimeSeriesBlock:
        """The attribute for prices."""
        return self.__prices

    @property
    def resourceid(self) -> Union[str, None]:
        """The attribute for the id of the resource."""
        return self.__resourceid

    @property
    def pricingtype(self) -> Union[str, None]:
        """The attribute for the type of price."""
        return self.__pricingtype


    @marketid.setter
    def marketid(self, marketid: str):
        """Set value for market id."""
        if self._check_marketid(marketid):
            self.__marketid = marketid
            return

    @prices.setter
    def prices(self, prices: Union[TimeSeriesBlock, Dict[str, Any]]):
        """Set value for prices.
        A string value is converted to a float. A float value is converted into a QuantityBlock with the default unit.
        A dict is converted to a QuantityBlock.
        Raises MessageValueError if value is missing or invalid: a QuantityBlock has the wrong unit, dict cannot be converted  or
        a string cannot be converted to float"""
        if self._check_prices(prices):
            self._set_timeseries_block_value('Prices', prices)
            return

        raise MessageValueError("'{:s}' is an invalid value for prices.".format(str(prices)))

    @resourceid.setter
    def resourceid(self, resourceid: Union[str, None]):
        """Set value for resource id."""
        if self._check_resourceid(resourceid):
            if resourceid is not None:
                self.__resourceid = str(resourceid)
            else:
                self.__resourceid = resourceid
            return

    @pricingtype.setter
    def pricingtype(self, pricingtype: Union[str, None]):
        """Set value for pricing type."""
        if self._check_pricingtype(pricingtype):
            if pricingtype is not None:
                self.__pricingtype = str(pricingtype)
            else:
                self.__pricingtype = pricingtype
            return


    def __eq__(self, other: Any) -> bool:
        """Check that two PriceForecastStateMessages represent the same message."""
        return (
            super().__eq__(other) and
            isinstance(other, PriceForecastStateMessage) and
            self.marketid == other.marketid and
            self.prices == other.prices and
            self.resourceid == other.resourceid and
            self.pricingtype == other.pricingtype
        )

    @classmethod
    def _check_marketid(cls, marketid: str) -> bool:
        """Check that value for marketid is valid i.e. a string."""
        return isinstance(marketid, str)

    @classmethod
    def _check_prices(cls, prices: Union[TimeSeriesBlock, Dist[str, Any]]) -> bool:
        """Check that value for prices is valid."""
        return cls._check_timeseries_block(prices, cls._check_prices_block)

    @classmethod
    def _check_resourceid(cls, resourceid: Union[str, None]) -> bool:
        """Check that value for resourceid is valid i.e. a string."""
        if resourceid is None:
            return True
        else:
            return isinstance(resourceid, str)
    
    @classmethod
    def _check_pricingtype(cls, pricingtype: Union[str, None]) -> bool:
        """Check that value for pricingtype is valid i.e. a string."""
        if pricingtype is None:
            return True
        else:
            return isinstance(pricingtype, str)

    @classmethod
    def _check_prices_block(cls, prices_block: TimeSeriesBlock) -> bool:
        block_series = prices_block.series
        if len(block_series) != 2 or len(prices_block.time_index) < 3:
            return False

        for prices_series_name in cls.PRICES_SERIES_NAMES:
            if prices_series_name not in block_series:
                return False
            current_series = block_series[prices_series_name]
            if current_series.unit_of_measure != cls.PRICES_SERIES_UNIT or len(current_series.values) < 3:
                return False

        return True


    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[PriceForecastStateMessage, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON is not validated returns None."""
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None


PriceForecastStateMessage.register_to_factory()
