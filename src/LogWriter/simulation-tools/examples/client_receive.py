# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""
This module contains code example about how to use the RabbitMQ message client
for receiving messages from the message bus.
"""

import asyncio
from typing import Any, Dict, Union

from examples.client import get_client
from tools.messages import BaseMessage, AbstractResultMessage
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)

SLEEP_TIME = 1.0
CLOSE_AFTER_MESSAGES = 10


class MessageReceiver:
    """Simple class for recording received messages."""
    def __init__(self):
        # keep count of the number of received messages
        self.count = 0
        # keep track of the epoch number from the latest message received
        self.latest_epoch = None

    async def callback(self, message_object: Union[BaseMessage, Dict[str, Any], str], topic_name: str):
        """
        Method that can be used to receive message from RabbitMQ message bus.
        The requirements for a callback method are that it must be awaitable (the async keyword) and
        callable with two parameters: the first containing the message contents and the second having the topic name.
        """
        self.count += 1
        if isinstance(message_object, BaseMessage):
            # All messages that are of supported type (i.e. a message class) and have been created with valid values
            # for the attributes should be child classes of BaseMessage.
            # The BaseMessage class supports 3 properties: message_type, simulation_id and timestamp
            message_type = message_object.message_type
            if isinstance(message_object, AbstractResultMessage):
                # All messages other than simulation state message or start message should be
                # abstract result messages and have the epoch_number property
                self.latest_epoch = message_object.epoch_number

        elif isinstance(message_object, dict):
            # Messages that do not have a corresponding message class or have been created with some invalid values
            # but are still valid JSON syntax are given as Python dictionary objects.
            # Handling of the received dictionaries should not be necessary
            # if all the expected message types have corresponding message classes.
            message_type = message_object.get("Type", "Unknown")
            if "EpochNumber" in message_object:
                self.latest_epoch = message_object["EpochNumber"]

        else:
            # Messages received from the message bus that are not valid JSON are given as strings.
            # Usually the invalid JSON strings can be ignored but they can sometimes be useful for debugging purposes.
            message_type = "Unknown"

        LOGGER.info("")
        LOGGER.info("Received '{:s}' message from topic '{:s}'".format(message_type, topic_name))
        LOGGER.info("Full message: {:s}".format(str(message_object)))
        LOGGER.info("")
        LOGGER.info("Total of {:d} messages received".format(self.count))
        LOGGER.info("Latest epoch number recorded is: {}".format(self.latest_epoch))


async def start_receiver():
    """
    Starts the message receiver.
    The test sender sends an epoch message, 3 status ready messages and
    a simulation state message to the message bus.
    """
    # get a RabbitmqClient by using the parameters defined in client.py
    client = get_client()
    # create an instance of the MessageReceiver
    message_receiver = MessageReceiver()

    # add a listener for all topics and
    # route the received messages to the callback method in the created MessageReceiver instance
    client.add_listener("#", message_receiver.callback)

    # do not allow the receiver program to exit before at least 10 messages have been received from the message bus
    while message_receiver.count < CLOSE_AFTER_MESSAGES:
        await asyncio.sleep(SLEEP_TIME)

    # close the RabbitMQ client before exiting to be nice for the RabbitMQ server
    LOGGER.info("Closing the connection to the message bus.")
    await client.close()


if __name__ == '__main__':
    asyncio.run(start_receiver())
