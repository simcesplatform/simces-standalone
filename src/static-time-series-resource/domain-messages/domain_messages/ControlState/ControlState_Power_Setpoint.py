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
from __future__ import annotations
from typing import Any, Dict, Optional, Union
from tools.message.block import QuantityBlock
from tools.exceptions.messages import MessageError, MessageValueError
from tools.messages import AbstractResultMessage


class ControlStatePowerSetpointMessage(AbstractResultMessage):
    """Message class for setting all the attributes for ControlStatePowerSetpoint message """
    CLASS_MESSAGE_TYPE = "ControlState.PowerSetpoint"
    MESSAGE_TYPE_CHECK = True
    # Json attribute to class attribute mapping
    MESSAGE_ATTRIBUTES = {
        "RealPower": "real_power",
        "ReactivePower": "reactive_power"
    }
    # list all attributes that are optional here (use the JSON attribute names)
    OPTIONAL_ATTRIBUTES = []

    # The quantity block attributes is listed here
    QUANTITY_BLOCK_ATTRIBUTES = {
        "RealPower": "kW",
        "ReactivePower": "kV.A{r}"
    }

    # Message class containing quantity array block is listed here
    QUANTITY_ARRAY_BLOCK_ATTRIBUTES = {}

    # Message class containing Time series block is listed here
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

    @property
    def real_power(self) -> QuantityBlock:
        """The attribute for real power of the resource."""
        return self.__real_power

    @property
    def reactive_power(self) -> QuantityBlock:
        """The attribute for reactive power of the resource."""
        return self.__reactive_power

    # for each attributes added by this message type provide a property setter function to set the value of
    # the attribute the name of the properties must correspond to the names given in MESSAGE_ATTRIBUTES

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

    def __eq__(self, other: Any) -> bool:
        """Check that two ControlStatePowerSetpointMessage represent the same message."""
        return (
            super().__eq__(other) and
            isinstance(other, ControlStatePowerSetpointMessage) and
            self.real_power == other.real_power and
            self.reactive_power == other.reactive_power
        )

    # Provide a class method for each attribute added by this message type to check if the value is acceptable
    # These should return True only when the given parameter corresponds to an acceptable value for the attribute
    @classmethod
    def _check_real_power(cls, real_power: Union[str, float, QuantityBlock]) -> bool:
        """Check that value for real power is valid."""
        return cls._check_quantity_block(real_power, cls.QUANTITY_BLOCK_ATTRIBUTES_FULL['RealPower'])

    @classmethod
    def _check_reactive_power(cls, reactive_power: Union[str, float, QuantityBlock]) -> bool:
        """Check that value for reactive power is valid."""
        return cls._check_quantity_block(reactive_power, cls.QUANTITY_BLOCK_ATTRIBUTES_FULL['ReactivePower'])

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Optional[ControlStatePowerSetpointMessage]:
        """TODO: description for the from_json method"""
        try:
            message_object = cls(**json_message)
            return message_object
        except (TypeError, ValueError, MessageError):
            return None


ControlStatePowerSetpointMessage.register_to_factory()
