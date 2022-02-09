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
"""This module contains the message class for the simulation platform resource state messages."""

from __future__ import annotations
from typing import Any, Dict, Union

from tools.exceptions.messages import MessageValueError
from tools.message.abstract import AbstractResultMessage, AbstractMessage
from tools.message.block import QuantityBlock
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class ResourceStateMessage(AbstractResultMessage):
    """Class containing all the attributes for a ResourceState message."""

    # message type for these messages
    CLASS_MESSAGE_TYPE = "ResourceState"
    MESSAGE_TYPE_CHECK = True

    # Mapping from message JSON attributes to class attributes
    MESSAGE_ATTRIBUTES = {
        "CustomerId": "customerid",
        "RealPower": "real_power",
        "ReactivePower": "reactive_power",
        "Node": "node",
        "StateOfCharge": "state_of_charge"
    }
    OPTIONAL_ATTRIBUTES = ["Node", "StateOfCharge"]

    # attributes whose value should be a QuantityBlock and the expected unit of measure.
    QUANTITY_BLOCK_ATTRIBUTES = {
        "RealPower": "kW",
        "ReactivePower": "kV.A{r}",
        "StateOfCharge": "%"
    }

    MESSAGE_ATTRIBUTES_FULL = {
        **AbstractResultMessage.MESSAGE_ATTRIBUTES_FULL,
        **MESSAGE_ATTRIBUTES
    }
    OPTIONAL_ATTRIBUTES_FULL = AbstractResultMessage.OPTIONAL_ATTRIBUTES_FULL + OPTIONAL_ATTRIBUTES
    QUANTITY_BLOCK_ATTRIBUTES_FULL = {
        **AbstractMessage.QUANTITY_BLOCK_ATTRIBUTES_FULL,
        **QUANTITY_BLOCK_ATTRIBUTES
    }

    # allowed values for the node attribute
    ACCEPTED_NODE_VALUES = [1, 2, 3]

    @property
    def customerid(self) -> str:
        """The attribute for the name of customerid to which the resource is connected."""
        return self.__customerid

    @property
    def real_power(self) -> QuantityBlock:
        """The attribute for real power of the resource."""
        return self.__real_power

    @property
    def reactive_power(self) -> QuantityBlock:
        """The attribute for reactive power of the resource."""
        return self.__reactive_power

    @property
    def node(self) -> Union[int, None]:
        """Node that 1-phase resource is connected to.
           If this is not specified then it is assumed that the resource is 3-phase resource."""
        return self.__node

    @property
    def state_of_charge(self) -> Union[QuantityBlock, None]:
        """Present amount of energy stored, % of rated kWh. Unit of measure: "%"."""
        return self.__state_of_charge

    @customerid.setter
    def customerid(self, customerid: str):
        """Set value for customerid."""
        if self._check_customerid(customerid):
            self.__customerid = customerid
            return

        raise MessageValueError(f"'{customerid}' is an invalid value for customerid since it is not a string.")

    @real_power.setter
    def real_power(self, real_power: Union[str, float, QuantityBlock, Dict[str, Any]]):
        """Set value for real power.
        A string value is converted to a float. A float value is converted into a QuantityBlock with the default unit.
        A dict is converted to a QuantityBlock.
        Raises MessageValueError if value is missing or invalid: a QuantityBlock has the wrong unit, dict cannot be converted  or
        a string cannot be converted to float"""
        if self._check_real_power(real_power):
            self._set_quantity_block_value('RealPower', real_power)
            return

        raise MessageValueError("'{:s}' is an invalid value for real power.".format(str(real_power)))

    @reactive_power.setter
    def reactive_power(self, reactive_power: Union[str, float, QuantityBlock, Dict[str, Any]]):
        """Set value for reactive power.
        A string value is converted to a float. A float value is converted into a QuantityBlock with the default unit.
        A dict is converted into a QuantityBlock.
        Raises MessageValueError if value is missing or invalid: a QuantityBlock has the wrong unit, dict cannot be converted  or
        a string cannot be converted to float"""
        if self._check_reactive_power(reactive_power):
            self._set_quantity_block_value('ReactivePower', reactive_power)
            return

        raise MessageValueError("'{:s}' is an invalid value for reactive power.".format(str(reactive_power)))

    @state_of_charge.setter
    def state_of_charge(self, state_of_charge: Union[float, str, dict, QuantityBlock, None]):
        """Set value for state of charge.
        A string value is converted to a float. A float value is converted into a QuantityBlock with the default unit.
        A dict is converted into a QuantityBlock.
        Raises MessageValueError if value is missing or invalid: a QuantityBlock has the wrong unit, dict cannot be converted  or
        a string cannot be converted to float"""
        if self._check_state_of_charge(state_of_charge):
            self._set_quantity_block_value("StateOfCharge", state_of_charge)
            return

        raise MessageValueError("'{:s}' is an invalid value for state of charge.".format(str(state_of_charge)))

    @node.setter
    def node(self, node: Union[int, None]):
        """Set value for node."""
        if self._check_node(node):
            if node is not None:
                self.__node = int(node)

            else:
                self.__node = node

            return

        raise MessageValueError(f"'{node}' is an invalid value for node: not an integer 1, 2 or 3.")

    def __eq__(self, other: Any) -> bool:
        """Check that two ResourceStateMessages represent the same message."""
        return (
            super().__eq__(other) and
            isinstance(other, ResourceStateMessage) and
            self.customerid == other.customerid and
            self.real_power == other.real_power and
            self.reactive_power == other.reactive_power and
            self.node == other.node and
            self.state_of_charge == other.state_of_charge
        )

    @classmethod
    def _check_customerid(cls, customerid: str) -> bool:
        """Check that value for customerid is valid i.e. a string."""
        return isinstance(customerid, str)

    @classmethod
    def _check_real_power(cls, real_power: Union[str, float, QuantityBlock]) -> bool:
        """Check that value for real power is valid."""
        return cls._check_quantity_block(real_power, cls.QUANTITY_BLOCK_ATTRIBUTES_FULL['RealPower'])

    @classmethod
    def _check_reactive_power(cls, reactive_power: Union[str, float, QuantityBlock]) -> bool:
        """Check that value for reactive power is valid."""
        return cls._check_quantity_block(reactive_power, cls.QUANTITY_BLOCK_ATTRIBUTES_FULL['ReactivePower'])

    @classmethod
    def _check_state_of_charge(cls, state_of_charge: Union[str, float, QuantityBlock, None]) -> bool:
        """Check that value for state of charge is valid which includes checking that it is between 0 and 100."""
        return cls._check_quantity_block(
            state_of_charge,
            cls.QUANTITY_BLOCK_ATTRIBUTES_FULL['StateOfCharge'],
            True,
            lambda value: value >= 0.0 and value <= 100.0
        )

    @classmethod
    def _check_node(cls, node: Union[int, None]) -> bool:
        """Check that node is None or something that can be converted to integer and its value is 1, 2 or 3."""
        if node is None:
            return True

        try:
            node = int(node)
            return node in cls.ACCEPTED_NODE_VALUES

        except ValueError:
            return False

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[ResourceStateMessage, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON is not validated returns None."""
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None


ResourceStateMessage.register_to_factory()
