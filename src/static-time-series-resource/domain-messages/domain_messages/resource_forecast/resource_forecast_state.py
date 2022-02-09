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
"""This module contains the message class for the simulation platform resource forecast power messages."""

from __future__ import annotations
from typing import Any, Dict, Union

from tools.exceptions.messages import MessageValueError
from tools.message.abstract import AbstractResultMessage
from tools.message.block import TimeSeriesBlock
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class ResourceForecastPowerMessage(AbstractResultMessage):
    """Class containing all the attributes for a ResourceForecastPower message."""

    # message type for these messages
    CLASS_MESSAGE_TYPE = "ResourceForecastState.Power"
    MESSAGE_TYPE_CHECK = True
    
    FORECAST_ATTRIBUTE = "Forecast"
    FORECAST_SERIES_NAMES = ["RealPower"]
    FORECAST_SERIES_UNIT = "kW"

    # Mapping from message JSON attributes to class attributes
    MESSAGE_ATTRIBUTES = {
        "Forecast": "forecast",
        "ResourceId": "resource_id"
    }
    OPTIONAL_ATTRIBUTES = []

    # attributes whose value should be a QuantityBlock and the expected unit of measure.
    QUANTITY_BLOCK_ATTRIBUTES = {}
    
    # attributes whose value should be a Array Block.
    QUANTITY_ARRAY_BLOCK_ATTRIBUTES = {}
    
    # attributes whose value should be a Timeseries Block.
    TIMESERIES_BLOCK_ATTRIBUTES = ["Forecast",]

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
    def resource_id(self) -> str:
        """The attribute for the name of resource that is forecasted."""
        return self.__resource_id

    @property
    def forecast(self) -> TimeSeriesBlock:
        """The attribute for forecast of the resource."""
        return self.__forecast

    @resource_id.setter
    def resource_id(self, resource_id: str):
        """Set value for resource name that is forecasted."""
        if self._check_resource_id(resource_id):
            self.__resource_id = resource_id
        else:
            raise MessageValueError("Invalid value, {}, for attribute: resource_id".format(resource_id))

    @forecast.setter
    def forecast(self, forecast: Union[TimeSeriesBlock, Dict[str, Any]]):
        """Set value for forecast. Series should have at least 2 time indexes and values. 
        A string value is converted to a float. A float value is converted into a QuantityBlock with the default unit.
        A dict is converted to a QuantityBlock.
        Raises MessageValueError if value is missing or invalid: a QuantityBlock has the wrong unit, dict cannot be converted  or
        a string cannot be converted to float"""

        if self._check_forecast(forecast):
            self._set_timeseries_block_value(self.FORECAST_ATTRIBUTE, forecast)
            return
        else:
            raise MessageValueError("Invalid value, {}, for attribute: forecast".format(forecast))

    def __eq__(self, other: Any) -> bool:
        """Check that two ResourceForecastPowerMessages represent the same message."""
        return (
            super().__eq__(other) and
            isinstance(other, ResourceForecastPowerMessage) and
            self.resource_id == other.resource_id and
            self.forecast == other.forecast
        )

    @classmethod
    def _check_resource_id(cls, resource_id: str) -> bool:
        """Check that value for resource_id is valid i.e. a string."""
        return isinstance(resource_id, str)

    @classmethod
    def _check_forecast(cls, forecast: Union[TimeSeriesBlock, Dict[str, Any]]) -> bool:
        """Check that value for forecast is valid."""
        return cls._check_timeseries_block(
            value=forecast, block_check=cls._check_forecast_block)
        
    @classmethod
    def _check_forecast_block(cls, forecast_block: TimeSeriesBlock) -> bool:
        block_series = forecast_block.series
        if len(block_series) != 1 or len(forecast_block.time_index) < 2:
            return False
        for forecast_series_name in cls.FORECAST_SERIES_NAMES:
            if forecast_series_name not in block_series:
                return False
            current_series = block_series[forecast_series_name]
            if current_series.unit_of_measure != cls.FORECAST_SERIES_UNIT or len(current_series.values) < 2:
                return False
        return True

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[ResourceForecastPowerMessage, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON is not validated returns None."""
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None

ResourceForecastPowerMessage.register_to_factory()
