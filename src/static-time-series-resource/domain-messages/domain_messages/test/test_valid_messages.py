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
"""Tests that take the domain message examples from the documentation pages and create message objects."""

import unittest

from tools.messages import MessageGenerator, QuantityBlock, TimeSeriesBlock
from tools.message.block import ValueArrayBlock
from tools.tools import FullLogger

from domain_messages.ControlState import ControlStatePowerSetpointMessage
from domain_messages.dispatch import DispatchBlock, ResourceForecastStateDispatchMessage
from domain_messages.InitCISCustomerInfo import InitCISCustomerInfoMessage
from domain_messages.LFMMarketResult import LFMMarketResultMessage
from domain_messages.Offer import OfferMessage
from domain_messages.price_forecaster import PriceForecastStateMessage
from domain_messages.Request import RequestMessage
from domain_messages.resource import ResourceStateMessage
from domain_messages.resource_forecast import ResourceForecastPowerMessage

LOGGER = FullLogger(__name__)

SIMULATION_ID = "2020-01-01T00:00:00.000Z"
SOURCE_PROCESS_ID = "test-component"
EPOCH_NUMBER = 10
TRIGGERING_MESSAGE_IDS = ["component1-10", "component2-10"]


class TestValidMessages(unittest.TestCase):
    """Unit tests for testing some creating message objects using valid parameters."""
    generator = MessageGenerator(SIMULATION_ID, SOURCE_PROCESS_ID)

    def test_valid_init_cis_customer_info_message(self):
        """Test creation of InitCISCustomerInfoMessage with valid parameters."""
        resource_id = ["load1", "load2", "load3"]
        customer_id = ["GridA-1", "GridA-1", "GridA-1"]
        bus_name = ["2", "1", ""]

        message = self.generator.get_message(
            InitCISCustomerInfoMessage,
            EpochNumber=EPOCH_NUMBER,
            TriggeringMessageIds=TRIGGERING_MESSAGE_IDS,
            ResourceId=resource_id,
            CustomerId=customer_id,
            BusName=bus_name
        )

        # only test the message type and the attributes that are not included in AbstractResultMessage
        self.assertIsInstance(message, InitCISCustomerInfoMessage)
        if isinstance(message, InitCISCustomerInfoMessage):
            self.assertEqual(message.message_type, "Init.CIS.CustomerInfo")
            self.assertEqual(message.resource_id, resource_id)
            self.assertEqual(message.customer_id, customer_id)
            self.assertEqual(message.bus_name, bus_name)

    def test_valid_lfm_marker_result_message(self):
        """Test creation of LFMMarketResultMessage with valid parameters."""
        activation_time = "2020-06-03T04:00:00.000Z"
        duration = QuantityBlock(Value=60, UnitOfMeasure="Minute")
        direction = "upregulation"
        real_power = TimeSeriesBlock(
            TimeIndex=[
                "2020-06-03T04:00:00.000Z",
                "2020-06-03T04:15:00.000Z",
                "2020-06-03T04:30:00.000Z",
                "2020-06-03T04:45:00.000Z"
            ],
            Series={
                "Regulation": ValueArrayBlock(
                    UnitOfMeasure="kW",
                    Values=[200, 300, 150, 210]
                )
            }
        )
        price = QuantityBlock(Value=50, UnitOfMeasure="EUR")
        customer_ids = ["CustomerIdA", "CustomerIdB"]
        congestion_id = "XYZ"
        offer_id = "Elenia-2020-06-03T04:15:07.456Z"
        result_count = 3

        message = self.generator.get_message(
            LFMMarketResultMessage,
            EpochNumber=EPOCH_NUMBER,
            TriggeringMessageIds=TRIGGERING_MESSAGE_IDS,
            ActivationTime=activation_time,
            Duration=duration,
            Direction=direction,
            RealPower=real_power,
            Price=price,
            CongestionId=congestion_id,
            OfferId=offer_id,
            ResultCount=result_count,
            CustomerIds=customer_ids
        )

        # only test the message type and the attributes that are not included in AbstractResultMessage
        self.assertIsInstance(message, LFMMarketResultMessage)
        if isinstance(message, LFMMarketResultMessage):
            self.assertEqual(message.message_type, "LFMMarketResult")
            self.assertEqual(message.activation_time, activation_time)
            self.assertEqual(message.duration, duration)
            self.assertEqual(message.direction, direction)
            self.assertEqual(message.real_power, real_power)
            self.assertEqual(message.price, price)
            self.assertEqual(message.congestion_id, congestion_id)
            self.assertEqual(message.offer_id, offer_id)
            self.assertEqual(message.result_count, result_count)
            self.assertEqual(message.customerids, customer_ids)

    def test_valid_offer_message(self):
        """Test creation of OfferMessage with valid parameters."""
        activation_time = "2020-06-03T04:00:00.000Z"
        duration = QuantityBlock(Value=60, UnitOfMeasure="Minute")
        direction = "upregulation"
        real_power = TimeSeriesBlock(
            TimeIndex=[
                "2020-06-03T04:00:00.000Z",
                "2020-06-03T04:15:00.000Z",
                "2020-06-03T04:30:00.000Z",
                "2020-06-03T04:45:00.000Z"
            ],
            Series={
                "Regulation": ValueArrayBlock(
                    UnitOfMeasure="kW",
                    Values=[200, 300, 150, 210]
                )
            }
        )
        price = QuantityBlock(Value=50, UnitOfMeasure="EUR")
        customer_ids = ["CustomerIdA", "CustomerIdB"]
        congestion_id = "XYZ"
        offer_id = "Elenia-2020-06-03T04:15:07.456Z"
        offer_count = 1

        message = self.generator.get_message(
            OfferMessage,
            EpochNumber=EPOCH_NUMBER,
            TriggeringMessageIds=TRIGGERING_MESSAGE_IDS,
            ActivationTime=activation_time,
            Duration=duration,
            Direction=direction,
            RealPower=real_power,
            Price=price,
            CongestionId=congestion_id,
            CustomerIds=customer_ids,
            OfferId=offer_id,
            OfferCount=offer_count
        )

        # only test the message type and the attributes that are not included in AbstractResultMessage
        self.assertIsInstance(message, OfferMessage)
        if isinstance(message, OfferMessage):
            self.assertEqual(message.message_type, "Offer")
            self.assertEqual(message.activation_time, activation_time)
            self.assertEqual(message.duration, duration)
            self.assertEqual(message.direction, direction)
            self.assertEqual(message.real_power, real_power)
            self.assertEqual(message.price, price)
            self.assertEqual(message.congestion_id, congestion_id)
            self.assertEqual(message.customerids, customer_ids)
            self.assertEqual(message.offer_id, offer_id)
            self.assertEqual(message.offer_count, offer_count)

    def test_valid_request_message(self):
        """Test creation of RequestMessage with valid parameters."""
        activation_time = "2020-06-03T04:00:00.000Z"
        duration = QuantityBlock(Value=30, UnitOfMeasure="Minute")
        direction = "upregulation"
        real_power_min = QuantityBlock(Value=100.0, UnitOfMeasure="kW")
        real_power_request = QuantityBlock(Value=700.0, UnitOfMeasure="kW")
        customer_ids = ["Elenia10", "Elenia170"]
        congestion_id = "XYZ"

        message = self.generator.get_message(
            RequestMessage,
            EpochNumber=EPOCH_NUMBER,
            TriggeringMessageIds=TRIGGERING_MESSAGE_IDS,
            ActivationTime=activation_time,
            Duration=duration,
            Direction=direction,
            RealPowerMin=real_power_min,
            RealPowerRequest=real_power_request,
            CustomerIds=customer_ids,
            CongestionId=congestion_id
        )

        # only test the message type and the attributes that are not included in AbstractResultMessage
        self.assertIsInstance(message, RequestMessage)
        if isinstance(message, RequestMessage):
            self.assertEqual(message.message_type, "Request")
            self.assertEqual(message.activation_time, activation_time)
            self.assertEqual(message.duration, duration)
            self.assertEqual(message.direction, direction)
            self.assertEqual(message.real_power_min, real_power_min)
            self.assertEqual(message.real_power_request, real_power_request)
            self.assertEqual(message.customer_ids, customer_ids)
            self.assertEqual(message.congestion_id, congestion_id)
            self.assertIsNone(message.bid_resolution)

    def test_control_state_power_setpoint_message(self):
        """Test creation of ControlStatePowerSetpointMessage with valid parameters."""
        real_power = QuantityBlock(Value=100.0, UnitOfMeasure="kW")
        reactive_power = QuantityBlock(Value=0.0, UnitOfMeasure="kV.A{r}")

        message = self.generator.get_message(
            ControlStatePowerSetpointMessage,
            EpochNumber=EPOCH_NUMBER,
            TriggeringMessageIds=TRIGGERING_MESSAGE_IDS,
            RealPower=real_power,
            ReactivePower=reactive_power
        )

        # only test the message type and the attributes that are not included in AbstractResultMessage
        self.assertIsInstance(message, ControlStatePowerSetpointMessage)
        if isinstance(message, ControlStatePowerSetpointMessage):
            self.assertEqual(message.message_type, "ControlState.PowerSetpoint")
            self.assertEqual(message.real_power, real_power)
            self.assertEqual(message.reactive_power, reactive_power)

    def test_resource_forecast_state_dispatch_message(self):
        """Test creation of ResourceForecastStateDispatchMessage with valid parameters."""
        dispatch = DispatchBlock(
            ResourceA=TimeSeriesBlock(
                TimeIndex=["2020-06-25T00:00:00Z", "2020-06-25T01:00:00Z"],
                Series={
                    "RealPower": ValueArrayBlock(
                        UnitOfMeasure="kW",
                        Values=[0.2, 0.27]
                    )
                }
            ),
            ResourceB=TimeSeriesBlock(
                TimeIndex=["2020-06-25T00:00:00Z", "2020-06-25T01:00:00Z"],
                Series={
                    "RealPower": ValueArrayBlock(
                        UnitOfMeasure="kW",
                        Values=[0.27, 0.2]
                    )
                }
            )
        )

        message = self.generator.get_message(
            ResourceForecastStateDispatchMessage,
            EpochNumber=EPOCH_NUMBER,
            TriggeringMessageIds=TRIGGERING_MESSAGE_IDS,
            Dispatch=dispatch
        )

        # only test the message type and the attributes that are not included in AbstractResultMessage
        self.assertIsInstance(message, ResourceForecastStateDispatchMessage)
        if isinstance(message, ResourceForecastStateDispatchMessage):
            self.assertEqual(message.message_type, "ResourceForecastState.Dispatch")
            self.assertEqual(message.dispatch, dispatch)

    def test_price_forecast_state_message(self):
        """Test creation of PriceForecastStateMessage with valid parameters."""
        market_id = "assign-market-here"
        resource_id = "assign-resource-here"
        prices = TimeSeriesBlock(
            TimeIndex=[
                "2020-02-17T10:00:00Z",
                "2020-02-17T11:00:00Z",
                "2020-02-17T12:00:00Z"
            ],
            Series={
                "Price": ValueArrayBlock(
                    UnitOfMeasure="{EUR}/(kW.h)",
                    Values=[0.041, 0.042, 0.043]
                )
            }
        )

        message = self.generator.get_message(
            PriceForecastStateMessage,
            EpochNumber=EPOCH_NUMBER,
            TriggeringMessageIds=TRIGGERING_MESSAGE_IDS,
            MarketId=market_id,
            ResourceId=resource_id,
            Prices=prices
        )

        # only test the message type and the attributes that are not included in AbstractResultMessage
        self.assertIsInstance(message, PriceForecastStateMessage)
        if isinstance(message, PriceForecastStateMessage):
            self.assertEqual(message.message_type, "PriceForecastState")
            self.assertEqual(message.marketid, market_id)
            self.assertEqual(message.resourceid, resource_id)
            self.assertEqual(message.prices, prices)
            self.assertIsNone(message.pricingtype)

    def test_resource_state_message(self):
        """Test creation of ResourceStateMessage with valid parameters."""
        customerid = "customer1"
        real_power = QuantityBlock(Value=100.0, UnitOfMeasure="kW")
        reactive_power = QuantityBlock(Value=0.0, UnitOfMeasure="kV.A{r}")
        node = 2
        state_of_charge = QuantityBlock(Value=68.1, UnitOfMeasure="%")

        message = self.generator.get_message(
            ResourceStateMessage,
            EpochNumber=EPOCH_NUMBER,
            TriggeringMessageIds=TRIGGERING_MESSAGE_IDS,
            CustomerId=customerid,
            RealPower=real_power,
            ReactivePower=reactive_power,
            Node=node,
            StateOfCharge=state_of_charge
        )

        # only test the message type and the attributes that are not included in AbstractResultMessage
        self.assertIsInstance(message, ResourceStateMessage)
        if isinstance(message, ResourceStateMessage):
            self.assertEqual(message.message_type, "ResourceState")
            self.assertEqual(message.customerid, customerid)
            self.assertEqual(message.real_power, real_power)
            self.assertEqual(message.reactive_power, reactive_power)
            self.assertEqual(message.node, node)
            self.assertEqual(message.state_of_charge, state_of_charge)

    def test_resource_forecast_power_message(self):
        """Test creation of ResourceForecastPowerMessage with valid parameters."""
        resource_id = "load1"
        forecast = TimeSeriesBlock(
            TimeIndex=[
                "2020-06-25T00:00:00Z",
                "2020-06-25T01:00:00Z",
                "2020-06-25T02:00:00Z",
                "2020-06-25T03:00:00Z"
            ],
            Series={
                "RealPower": ValueArrayBlock(
                    UnitOfMeasure="kW",
                    Values=[-0.2, -0.27, -0.15, -0.21]
                )
            }
        )

        message = self.generator.get_message(
            ResourceForecastPowerMessage,
            EpochNumber=EPOCH_NUMBER,
            TriggeringMessageIds=TRIGGERING_MESSAGE_IDS,
            ResourceId=resource_id,
            Forecast=forecast
        )

        # only test the message type and the attributes that are not included in AbstractResultMessage
        self.assertIsInstance(message, ResourceForecastPowerMessage)
        if isinstance(message, ResourceForecastPowerMessage):
            self.assertEqual(message.message_type, "ResourceForecastState.Power")
            self.assertEqual(message.resource_id, resource_id)
            self.assertEqual(message.forecast, forecast)


if __name__ == "__main__":
    unittest.main()
