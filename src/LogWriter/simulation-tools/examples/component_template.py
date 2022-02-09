# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""
Module containing a template for a simulation platform component.
"""

import asyncio
from typing import Any, cast, Optional, Union

from tools.components import AbstractSimulationComponent
from tools.exceptions.messages import MessageError
from tools.messages import BaseMessage
from tools.tools import FullLogger, load_environmental_variables

# import all the required messages from installed libraries
# from <library_name>.<folder_name_1> import <message_class_name_1>
# from <library_name>.<folder_name_2> import <message_class_name_2>

# initialize logging object for the module
LOGGER = FullLogger(__name__)

# set the names of the used environment variables to Python variables
COMPONENT_PARAMETER_1 = "COMPONENT_PARAMETER_1"
COMPONENT_PARAMETER_2 = "COMPONENT_PARAMETER_2"
COMPONENT_PARAMETER_3 = "COMPONENT_PARAMETER_3"

SOME_TOPIC_1 = "SOME_TOPIC_1"
SOME_TOPIC_2 = "SOME_TOPIC_2"

# time interval in seconds on how often to check whether the component is still running
TIMEOUT = 1.0


class NewSimulationComponent(AbstractSimulationComponent):
    """
    Description for the NewSimulationComponent.
    """

    # The constructor for the component class.
    # This example shows three parameters given to the component at the constructor
    # These should be adjusted to fit the actual component in development.
    def __init__(
            self,
            parameter1: int,
            parameter2: str,
            parameter3: Optional[str] = None):
        """
        Description for the constructor including descriptions for the parameters.

        - parameter1 (int): description for the required integer parameter
        - parameter2 (str): description for the required string parameter
        - parameter3 (str): description for the optional string parameter
        """

        # Initialize the AbstractSimulationComponent using the values from the environmental variables.
        # This will initialize various variables including the message client for message bus access.
        super().__init__()

        # Set the object variables for the extra parameters.
        self._parameter1 = parameter1
        self._parameter2 = parameter2
        self._parameter3 = parameter3

        # Add checks for the parameters if necessary
        # and set initialization error if there is a problem with the parameters.
        # if <some_check_for_the_parameters>:
        #     # add appropriate error message
        #     self.initialization_error = "There was a problem with the parameters"
        #     LOGGER.error(self.initialization_error)

        # Load environmental variables for those parameters that were not given to the constructor.
        # In this template the used topics are set in this way with given default values as an example.
        environment = load_environmental_variables(
            (SOME_TOPIC_1, str, "SomeTopic.One"),
            (SOME_TOPIC_2, str, "SomeTopic.Two")
        )
        self._topic_one = cast(str, environment[SOME_TOPIC_1])
        self._topic_two = cast(str, environment[SOME_TOPIC_2])

        # The easiest way to ensure that the component will listen to all necessary topics
        # is to set the self._other_topics variable with the list of the topics to listen to.
        # Note, that the "SimState" and "Epoch" topic listeners are added automatically by the parent class.
        self._other_topics = [
            self._topic_one,
            self._topic_two
        ]

        # The base class contains several variables that can be used in the child class.
        # The variable list below is not an exhaustive list but contains the most useful variables.

        # Variables that should only be READ in the child class:
        # - self.simulation_id               the simulation id
        # - self.component_name              the component name
        # - self.start_message               the Start message as a dictionary (None if the message is not available)
        # - self._simulation_state           either "running" or "stopped"
        # - self._latest_epoch               epoch number for the current epoch
        # - self._completed_epoch            epoch number for the latest epoch that has been completed
        # - self._latest_epoch_message       the latest epoch message as EpochMessage object

        # Variable for the triggering message ids where all relevant message ids should be appended.
        # The list is automatically cleared at the start of each epoch.
        # - self._triggering_message_ids

        # MessageGenerator object that can be used to generate the message objects:
        # - self._message_generator

        # RabbitmqClient object for communicating with the message bus:
        # - self._rabbitmq_client

    def clear_epoch_variables(self) -> None:
        """
        Clears all the variables that are used to store information about the received input within the
        current epoch. This method is called automatically after receiving an epoch message for a new epoch.

        NOTE: this method should be overwritten in any child class that uses epoch specific variables
        """
        # replace "pass" with the initialization of the variables for the new epoch
        pass  # pylint: disable=unnecessary-pass

    async def process_epoch(self) -> bool:
        """
        Process the epoch and do all the required calculations.
        Assumes that all the required information for processing the epoch is available.

        Returns False, if processing the current epoch was not yet possible.
        Otherwise, returns True, which indicates that the epoch processing was fully completed.
        This also indicated that the component is ready to send a Status Ready message to the Simulation Manager.

        NOTE: this method should be overwritten in any child class.
        """

        # Any calculations done within the current epoch would be included here.
        # Also sending of any result messages (other than Status message) would be included here.
        return True     # only if the component is done for the current epoch
        # return False  # if the component still has things to do within the current epoch

    async def all_messages_received_for_epoch(self) -> bool:
        """
        Returns True, if all the messages required to start calculations for the current epoch have been received.
        Checks only that all the required information is available.
        Does not check any other conditions like the simulation state.

        NOTE: this method should be overwritten in any child class that needs more
        information than just the Epoch message.
        """

        return True     # if all input messages have been received
        # return False  # otherwise

    async def general_message_handler(self, message_object: Union[BaseMessage, Any],
                                      message_routing_key: str) -> None:
        """
        Handles the incoming messages. message_routing_key is the topic for the message.
        Assumes that the messages are not of type SimulationStateMessage or EpochMessage.

        NOTE: this method should be overwritten in any child class that
        listens to messages other than SimState or Epoch messages.
        """

        # general structure on how to handle messages here:
        # - check the message type
        #       if isinstance(message_object, MessageClassName):
        # - check that the message is valid, for example that is for the current epoch
        #     - if the message is not valid, either output warning message or send an error message
        #       to the message bus depending on the seriousness of the error
        #           LOGGER.warning("warning output here")
        #           await self.send_error_message("error description here")
        # - store any information from the message to some variable (self._variable_name)
        #     - this might be the information that all_messages_received_for_epoch() would check
        # - update the triggering message id list
        #       self._triggering_message_ids.append(message_object.message_id)
        # - if it is now possible that the component has received all input messages
        #   for the current epoch call start_epoch()
        #       await self.start_epoch()

    # an example of method for sending an output message
    async def _send_result_message(self):
        """
        Sends a result message based on the current variable values.
        """
        try:
            # The code is commented because no MyResultMessage class is imported.
            # Replace the class name, the message attributes and the topic name as appropriate.

            # result_message = self._message_generator.get_message(
            #     MyResultMessage,
            #     EpochNumber=self._latest_epoch,
            #     TriggeringMessageIds=self._triggering_message_ids,
            #     MyAttribute1=self._my_variable_1,
            #     MyAttribute2=self._my_variable_2
            # )
            # await self._rabbitmq_client.send_message(
            #     topic_name=self._result_topic,
            #     message_bytes=result_message.bytes()
            # )
            pass  # remove this when the code above is properly included

        except (ValueError, TypeError, MessageError) as message_error:
            # When there is an exception while creating the message, it is in most cases a serious error.
            LOGGER.error("{}: {}".format(type(message_error).__name__, message_error))
            await self.send_error_message("Internal error when creating result message.")


def create_component() -> NewSimulationComponent:
    """
    Creates and returns a NewSimulationComponent based on the environment variables.
    """

    # Read the parameters for the component from the environment variables.
    # In this example the parameters are made to correspond to the example
    # parameters used in the NewSimulationComponent constructor
    # They should be changed to fit the actual component.
    environment_variables = load_environmental_variables(
        (COMPONENT_PARAMETER_1, int, 10),      # required integer with the default value of 10
        (COMPONENT_PARAMETER_2, str, "test"),  # required string with the default value of "test"
        (COMPONENT_PARAMETER_3, str)           # optional string with the default value of None
    )

    # The cast function here is only used to help Python linters like pyright to recognize the proper type.
    # They are not necessary and can be omitted.
    parameter1 = cast(int, environment_variables[COMPONENT_PARAMETER_1])
    parameter2 = cast(str, environment_variables[COMPONENT_PARAMETER_2])
    parameter3 = environment_variables[COMPONENT_PARAMETER_3]
    if parameter3 is not None:
        parameter3 = cast(str, parameter3)

    # Create and return a new NewSimulationComponent object using the values from the environment variables
    return NewSimulationComponent(
        parameter1=parameter1,
        parameter2=parameter2,
        parameter3=parameter3
    )


async def start_component():
    """
    Creates and starts a NewSimulationComponent component.
    """
    resource = create_component()

    # The component will only start listening to the message bus once the start() method has been called.
    await resource.start()

    # Wait in the loop until the component has stopped itself.
    while not resource.is_stopped:
        await asyncio.sleep(TIMEOUT)


if __name__ == "__main__":
    asyncio.run(start_component())
