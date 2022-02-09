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
"""This module contains the message class for the simulation platform offer messages."""

from __future__ import annotations
from typing import Union, Dict, Any, List

from tools.exceptions.messages import MessageValueError
from tools.message.abstract import AbstractResultMessage
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)

# Example:
# newMessage3 = InitCISCustomerInfoMessage(**{
#         "Type": "Init.CIS.CustomerInfo",
#         "SimulationId": to_iso_format_datetime_string(datetime.datetime.now()),
#         "SourceProcessId": "source1",
#         "MessageId": "messageid1",
#         "EpochNumber": 1,
#         "TriggeringMessageIds": ["messageid1.1", "messageid1.2"],
#         "ResourceId": ["res1", "res2"],
#         "CustomerId": ["cus1", "cus2"],
#         "BusName": ["bus1", ""]
#     })
#
# NOTE: The length of the lists is not checked. All should be of same length.


class InitCISCustomerInfoMessage(AbstractResultMessage):
    """Class containing all the attributes for an Init.CIS.CustomerInfo message."""

    # message type for these messages
    CLASS_MESSAGE_TYPE = "Init.CIS.CustomerInfo"
    MESSAGE_TYPE_CHECK = True

    # Mapping from message JSON attributes to class attributes
    MESSAGE_ATTRIBUTES = {
        "ResourceId": "resource_id",
        "CustomerId": "customer_id",
        "BusName": "bus_name"
    }
    OPTIONAL_ATTRIBUTES = []

    # attributes whose value should be a QuantityBlock and the expected unit of measure.
    QUANTITY_BLOCK_ATTRIBUTES = {}

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
        """Check that two InitCISCustomerInfoMessages represent the same message."""
        return (
            super().__eq__(other) and
            isinstance(other, InitCISCustomerInfoMessage) and
            self.customer_id == other.customer_id and
            self.resource_id == other.resource_id and
            self.bus_name == other.bus_name
        )

    @property
    def resource_id(self) -> List[str]:
        return self.__resource_id

    @resource_id.setter
    def resource_id(self, resource_id_list: List[str]):
        if self._check_resource_id(resource_id_list):
            self.__resource_id = list(resource_id_list)
            return

        raise MessageValueError("'{:s}' is an invalid ResourceId".format(str(resource_id_list)))

    @classmethod
    def _check_resource_id(cls, resource_id_list: List[str]) -> bool:
        if not isinstance(resource_id_list, list):
            return False
        for resource in resource_id_list:
            if not isinstance(resource, str):
                return False
            if len(resource) < 1:
                return False
        return True

    @property
    def customer_id(self) -> List[str]:
        return self.__customer_id

    @customer_id.setter
    def customer_id(self, customer_id_list: List[str]):
        if self._check_customer_id(customer_id_list):
            self.__customer_id = list(customer_id_list)
            return

        raise MessageValueError("'{:s}' is an invalid CustomerId".format(str(customer_id_list)))

    @classmethod
    def _check_customer_id(cls, customer_id_list: List[str]) -> bool:
        if not isinstance(customer_id_list, list):
            return False
        if len(customer_id_list) < 1:
            return False
        for customer in customer_id_list:
            if not isinstance(customer, str):
                return False
            if len(customer) < 1:
                return False
        return True

    @property
    def bus_name(self) -> List[str]:
        return self.__bus_name

    @bus_name.setter
    def bus_name(self, bus_name_list: List[str]):
        if self._check_bus_name(bus_name_list):
            self.__bus_name = list(bus_name_list)
            return

        raise MessageValueError("'{:s}' is an invalid BusName".format(str(bus_name_list)))

    @classmethod
    def _check_bus_name(cls, bus_name_list: List[str]) -> bool:
        if not isinstance(bus_name_list, list):
            return False
        if len(bus_name_list) < 1:
            return False
        return True

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[InitCISCustomerInfoMessage, None]:
        if cls.validate_json(json_message):
            return InitCISCustomerInfoMessage(**json_message)
        return None


InitCISCustomerInfoMessage.register_to_factory()
