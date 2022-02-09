# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains code examples related to using the message classes."""

import asyncio
import logging

from examples.client import get_client
from tools.clients import RabbitmqClient
from tools.messages import MessageGenerator, StatusMessage
from tools.tools import FullLogger

# use the FullLogger for logging to show the output on the screen as well as to store it to a file
# the default file name for the log output is logfile.out
# the file name can be changed by using the environment variable SIMULATION_LOG_FILE
# in python code that can be done by:
#     import os
#     os.environ["SIMULATION_LOG_FILE"] = "my_logs.txt"
LOGGER = FullLogger(__name__, logger_level=logging.INFO)

EPOCH_TOPIC = "Epoch"
STATUS_TOPIC = "Status.Ready"
SIMSTATE_TOPIC = "SimState"
WAIT_BETWEEN_MESSAGES = 4.0


def send_message(client: RabbitmqClient, topic_name: str, message_bytes: bytes) -> None:
    """
    Sends a message to the message bus. This is done by creating a task to the event loop.
    The function will very likely exit before the sending of the message is actually finished.
    This function should only be called from an async function to ensure that there is a running event loop.
    """
    asyncio.create_task(client.send_message(topic_name, message_bytes))


async def start_sender() -> None:
    """
    Starts the test sender.
    The test sender sends an epoch message, 3 status ready messages and
    a simulation state message to the message bus.
    """
    # get a RabbitmqClient by using the parameters defined in client.py
    client = get_client()
    # create a message generator for the test sender
    generator = MessageGenerator(
        simulation_id="2000-01-01T12:00:00.000Z",
        source_process_id="TestProcess")

    message = generator.get_epoch_message(
        EpochNumber=1,
        TriggeringMessageIds=["message-id"],
        StartTime="2020-01-01T00:00:00.000Z",
        EndTime="2020-01-01T01:00:00.000Z")
    LOGGER.info("Sending an epoch message with start time {:s} to topic {:s}".format(message.start_time, EPOCH_TOPIC))
    await client.send_message(EPOCH_TOPIC, message.bytes())
    LOGGER.info("")

    # wait for a few seconds before sending the next message
    await asyncio.sleep(WAIT_BETWEEN_MESSAGES)

    message = generator.get_status_ready_message(
        EpochNumber=1,
        TriggeringMessageIds=["message-id-2"])
    LOGGER.info("Sending a status message for epoch {:d} to topic {:s}".format(message.epoch_number, STATUS_TOPIC))
    await client.send_message(STATUS_TOPIC, message.bytes())
    LOGGER.info("")

    await asyncio.sleep(WAIT_BETWEEN_MESSAGES)

    message = generator.get_status_ready_message(
        EpochNumber=2,
        TriggeringMessageIds=["message-id-3"])
    LOGGER.info("Sending a second status message")
    await client.send_message(STATUS_TOPIC, message.bytes())
    LOGGER.info("")

    await asyncio.sleep(WAIT_BETWEEN_MESSAGES)

    # use the general get_message method for creating the third status ready message
    message = generator.get_message(
        StatusMessage,
        EpochNumber=3,
        TriggeringMessageIds=["new-message-id", "new-message-id2"],
        Value="ready")
    LOGGER.info("Sending a third status message")
    # use the helper function to create a task for sending the message instead of the await keyword
    # this means that the execution of start_sender() will continue to the next source code line
    # while the sending of the message is done simultaneously.
    send_message(client, STATUS_TOPIC, message.bytes())
    LOGGER.info("")

    await asyncio.sleep(WAIT_BETWEEN_MESSAGES)

    message = generator.get_simulation_state_message(SimulationState="stopped")
    LOGGER.info("Sending a simulation state message {:s}".format(message.simulation_state))
    send_message(client, SIMSTATE_TOPIC, message.bytes())
    LOGGER.info("")

    await asyncio.sleep(WAIT_BETWEEN_MESSAGES)

    LOGGER.info("Closing the connection to the message bus.")
    await client.close()


if __name__ == '__main__':
    asyncio.run(start_sender())
