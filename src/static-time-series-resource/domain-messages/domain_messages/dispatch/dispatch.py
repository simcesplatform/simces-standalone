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
"""This module contains the message class for the simulation platform dispatch messages."""

from __future__ import annotations
import json
from typing import Any, Callable, Dict, List, Tuple, Type, Union

from tools.message.abstract import AbstractResultMessage
from tools.exceptions.messages import MessageValueError
from tools.message.block import TimeSeriesBlock
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class DispatchBlock:
    """ Class for containing component dispatches for a message, dispatch field content of ResourceForecastStateDispatchMessage. 
    
    Get dispatch TimeSeries block for resource_name with block[resource_name] or block.get(resource_name) (None for non-existing resource)
    where block is a DispatchBlock. Other helper methods assist in slicing one dispatch message into multiple.
    """

    DISPATCH_SERIES_UNITS = {"RealPower": "kW"}

    def __init__(self, **kwargs):
        """Creates a new Dispatch block. 
        Throws an exception if parameters contain invalid values.
        
        Parameters
        ----------
        kwargs:
            component names as keys and appropriate TimeSeries blocks or dicts
            (see series key and unit of measure pairs in DISPATCH_SERIES_UNITS) as values
        """

        self.__dispatch = {}
        self._set_attribute_values(kwargs)

    def _set_attribute_values(self, kwargs: Dict[str, Union[TimeSeriesBlock, Dict[str,Any]]]):
        for k, v in kwargs.items():
            self.add_component_dispatch(k, v)

    def __getitem__(self, key):
        return self.__dispatch[key]

    def __setitem__(self, key, value):
        self.add_component_dispatch(component_name=key, component_dispatch=value)

    def clear(self):
        self.__dispatch.clear()

    def get(self, key, default=None):
        self.__dispatch.get(key, default)

    def items(self):
        return self.__dispatch.items()

    def keys(self):
        return self.__dispatch.keys()

    @classmethod
    def _check_item(cls, key: str, val: Union[TimeSeriesBlock, Dict[str,Any]]) -> bool:
        """ Checks that the name, dispatch pair is valid."""
        if not isinstance(key, str) and isinstance(val, (TimeSeriesBlock, dict)):
            return False

        if not cls._check_time_series_block(val):
            return False
        
        return True

    @classmethod
    def _check_time_series_block(cls, block: Union[TimeSeriesBlock, Dict[str, Any]]) -> bool:
        """ Check that value for time series block is valid. """
        if isinstance(block, dict):
            block = TimeSeriesBlock(**block)
        
        try:
            for var_name, unit_of_meas in cls.DISPATCH_SERIES_UNITS.items():
                if block.series[var_name].unit_of_measure != unit_of_meas:
                    return False
        except KeyError:
            return False
        
        return True

    def add_component_dispatch(self, component_name: str, 
                    component_dispatch: Union[TimeSeriesBlock, Dict[str, Any]]):
        """ Adds a new component dispatch to block.
        Throws an exception if parameters contain invalid values."""

        if not self._check_item(component_name, component_dispatch):
            raise MessageValueError("'{:s}' dispatch item is invalid.".format(component_name))

        if isinstance(component_dispatch, dict):
            component_dispatch = TimeSeriesBlock(**component_dispatch)

        self.__dispatch[component_name] = component_dispatch

    def get_component_dispatch_block(self, component_name: str) -> DispatchBlock:
        """Returns the a specific component dispatch as a DispatchBlock."""
        return DispatchBlock(**self.get_component_dispatch_json(component_name))

    def get_component_dispatch_json(self, component_name: str) -> Dict[str, Any]:
        """Returns the a specific component dispatch block as a JSON object."""
        return {component_name: self[component_name].json()}

    def remove_component_dispatch(self, component_name: str):
        """ Removes a component dispatch from the block. """
        del self.__dispatch[component_name]

    def json(self) -> Dict[str, Any]:
        """Returns the dispatch block as a JSON object."""
        return {name: time_series_block.json() for name, time_series_block in self.items()}

    def __eq__(self, other) -> bool:
        '''
        Check that two dispatch blocks represent the same quantity.

        '''
        if not isinstance(other, DispatchBlock):
            return False

        return self.__dispatch == other.__dispatch

    def __str__(self) -> str:
        '''
        Convert to a string.
        '''
        return json.dumps(self.json())

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def validate_json(cls, json_dispatch_block: Dict[str, Any]) -> bool:
        '''
        Check if the given dictionary could be converted to a DispatchBlock.
        '''
        try:
            DispatchBlock(**json_dispatch_block)
            return True

        except MessageValueError as err:
            LOGGER.warning("{:s} error '{:s}' encountered when validating dispatch block".format(str(type(err)), str(err)))
            return False

    @classmethod
    def from_json(cls, json_dispatch_block: Dict[str, Any]):
        '''
        Convert the given dictionary to a DispatchBlock.
        If the conversion does not succeed returns None.
        '''
        if cls.validate_json(json_dispatch_block):
            return DispatchBlock(**json_dispatch_block)

        return None


class ResourceForecastStateDispatchMessage(AbstractResultMessage):
    """Class containing all the attributes for a dispatch message."""

    CLASS_MESSAGE_TYPE = "ResourceForecastState.Dispatch"
    MESSAGE_TYPE_CHECK = True

    MESSAGE_ATTRIBUTES = {
        "Dispatch": "dispatch",
    }

    MESSAGE_ATTRIBUTES_FULL = {
        **AbstractResultMessage.MESSAGE_ATTRIBUTES_FULL,
        **MESSAGE_ATTRIBUTES
    }

    @property
    def dispatch(self) -> Dict[str, Union[DispatchBlock, Dict[str, Any]]]:
        return self.__dispatch

    @dispatch.setter
    def dispatch(self, dispatch: Dict[str, Union[DispatchBlock, Dict[str, Any]]]):
        if not self._check_dispatch(dispatch):
            raise MessageValueError("'{:s}' is an invalid item for dispatch.".format("<placeholder>"))

        if isinstance(dispatch, dict):
            dispatch = DispatchBlock(**dispatch)
        self.__dispatch = dispatch

    def __eq__(self, other: Any):
        return (
            super().__eq__(other) and
            isinstance(other, ResourceForecastStateDispatchMessage) and
            self.dispatch == other.dispatch
        )

    @classmethod
    def _check_dispatch(cls, dispatch: Union[DispatchBlock, Dict[str, Any]]) -> bool:
        return isinstance(dispatch, (DispatchBlock, dict))

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) :
        """Returns a class object created based on the given JSON attributes.
           If the given JSON does not contain valid values, returns None."""
        if cls.validate_json(json_message):
            return ResourceForecastStateDispatchMessage(**json_message)
        return None

ResourceForecastStateDispatchMessage.register_to_factory()