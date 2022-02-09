# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>
#            Otto Hylli <otto.hylli@tuni.fi>

"""This module contains a base simulation component that can communicate with the RabbitMQ message bus."""

import asyncio
import json
from typing import cast, Any, Dict, List, Optional, Union

from tools.clients import RabbitmqClient
from tools.exceptions.messages import MessageError
from tools.messages import (
    BaseMessage, AbstractMessage, EpochMessage, StatusMessage, SimulationStateMessage, MessageGenerator)
from tools.tools import FullLogger, EnvironmentVariable

LOGGER = FullLogger(__name__)

# The names of the environmental variables used by the component.
SIMULATION_ID = "SIMULATION_ID"
SIMULATION_COMPONENT_NAME = "SIMULATION_COMPONENT_NAME"
SIMULATION_EPOCH_MESSAGE_TOPIC = "SIMULATION_EPOCH_MESSAGE_TOPIC"
SIMULATION_STATUS_MESSAGE_TOPIC = "SIMULATION_STATUS_MESSAGE_TOPIC"
SIMULATION_STATE_MESSAGE_TOPIC = "SIMULATION_STATE_MESSAGE_TOPIC"
SIMULATION_ERROR_MESSAGE_TOPIC = "SIMULATION_ERROR_MESSAGE_TOPIC"
SIMULATION_START_MESSAGE_FILENAME = "SIMULATION_START_MESSAGE_FILENAME"

# To receive any other messages other than "Epoch" and "SimState" from the message bus
# use a comma separated list in SIMULATION_OTHER_TOPICS
# for example: "Result,Info" would make the simulation component listen to topics
# "Result" and "Info" in addition to the topics "Epoch" and "SimState
SIMULATION_OTHER_TOPICS = "SIMULATION_OTHER_TOPICS"


class AbstractSimulationComponent:
    """Class for holding the state of a abstract simulation component.
       The actual simulation components should be derived from this."""
    SIMULATION_STATE_VALUE_RUNNING = SimulationStateMessage.SIMULATION_STATES[0]   # "running"
    SIMULATION_STATE_VALUE_STOPPED = SimulationStateMessage.SIMULATION_STATES[-1]  # "stopped"

    READY_STATUS = StatusMessage.STATUS_VALUES[0]  # "ready"
    ERROR_STATUS = StatusMessage.STATUS_VALUES[-1]  # "error"

    def __init__(self,
                 simulation_id: Optional[str] = None,
                 component_name: Optional[str] = None,
                 epoch_message_topic: Optional[str] = None,
                 simulation_state_message_topic: Optional[str] = None,
                 status_message_topic: Optional[str] = None,
                 error_message_topic: Optional[str] = None,
                 other_topics: Optional[List[str]] = None,
                 rabbitmq_host: Optional[str] = None,
                 rabbitmq_port: Optional[int] = None,
                 rabbitmq_login: Optional[str] = None,
                 rabbitmq_password: Optional[str] = None,
                 rabbitmq_ssl: Optional[bool] = None,
                 rabbitmq_ssl_version: Optional[str] = None,
                 rabbitmq_exchange: Optional[str] = None,
                 rabbitmq_exchange_autodelete: Optional[bool] = None,
                 rabbitmq_exchange_durable: Optional[bool] = None,
                 **kwargs: Any):
        """Loads the simulation is and the component name as wells as the required topic names from environmental
        variables and sets up the connection to the RabbitMQ message bus for which the connection parameters are
        fetched from environmental variables. Opens a topic listener for the simulation state and epoch messages
        as well as other specified topics after creating the connection to the message bus.

        If any attribute is missing or its value is None, an environmental value is used for the attribute value.
        Most attributes also have a default value that is used when even the environmental value is missing.

        The available attributes:
        - simulation_id (str)
            - the simulation_id for the simulation, i.e. SimulationId that is used in the messages
            - environmental variable: "SIMULATION_ID"
            - default value: "2020-01-01T00:00:00.000Z"
        - component_name (str)
            - the component name, i.e. the SourceProcessId, that the component uses in the messages
            - environmental variable: "SIMULATION_COMPONENT_NAME"
            - default value: "component"
        - epoch_message_topic (str)
            - the topic name for the Epoch messages
            - environmental variable: "SIMULATION_EPOCH_MESSAGE_TOPIC"
            - default value: "Epoch"
        - simulation_state_message_topic (str)
            - the topic name for the Simulation state messages
            - environmental variable: "SIMULATION_STATE_MESSAGE_TOPIC"
            - default value: "SimState"
        - status_message_topic (str)
            - the topic name for the Status ready messages
            - environmental variable: "SIMULATION_STATUS_MESSAGE_TOPIC"
            - default value: "Status.Ready"
        - error_message_topic (str)
            - the topic name for the Status error messages
            - environmental variable: "SIMULATION_ERROR_MESSAGE_TOPIC"
            - default value: "Status.Error"
        - other_topics (List[str])
            - a list of topic names that the component needs to listen to in addition to the epoch and simulation state
            - environmental variable: "SIMULATION_OTHER_TOPICS"
                - in the environmental variable the list is given as a comma seprated string, e.g. "Result,Info"
            - default value: []
        - rabbitmq_host (str)
            - the host name for the RabbitMQ server
            - environmental variable: "RABBITMQ_HOST"
            - default value: "localhost"
        - rabbitmq_port (int)
            - the port number for the RabbitMQ server
            - environmental variable: "RABBITMQ_PORT"
            - default value: 5672
        - rabbitmq_login (str)
            - the username for access to the RabbitMQ server
            - environmental variable: "RABBITMQ_LOGIN"
            - default value: ""
        - rabbitmq_password (str)
            - the password for access to the RabbitMQ server
            - environmental variable: "RABBITMQ_PASSWORD"
            - default value: ""
        - rabbitmq_ssl (bool)
            - whether to use SSL connection to the RabbitMQ server
            - environmental variable: "RABBITMQ_SSL"
            - default value: False
        - rabbitmq_ssl_version (str)
            - the SSL version parameter for the SSL connection (ignored if rabbitmq_ssl is False)
            - environmental variable: "RABBITMQ_SSL_VERSION"
            - default value: "PROTOCOL_TLS"
        - rabbitmq_exchange (str)
            - the name for the exchange used by the RabbitMQ client
            - environmental variable: "RABBITMQ_EXCHANGE"
            - default value: ""
        - rabbitmq_exchange_autodelete (bool)
            - whether to automatically delete the exchange after use
            - environmental variable: "RABBITMQ_EXCHANGE_AUTODELETE"
            - default value: False
        - rabbitmq_exchange_durable (bool)
            - whether to setup the exchange to survive message bus restarts
            - environmental variable: "RABBITMQ_EXCHANGE_DURABLE"
            - default value: False
        - **kwargs
            - all other arguments are ignored
        """
        # pylint: disable=unused-argument

        # Start the connection to the RabbitMQ client using the given connection parameters and
        # the environmental values for those parameters that were not given.
        self._rabbitmq_parameters = AbstractSimulationComponent.__get_rabbitmq_parameters(
            host=rabbitmq_host,
            port=rabbitmq_port,
            login=rabbitmq_login,
            password=rabbitmq_password,
            ssl=rabbitmq_ssl,
            ssl_version=rabbitmq_ssl_version,
            exchange=rabbitmq_exchange,
            exchange_autodelete=rabbitmq_exchange_autodelete,
            exchange_durable=rabbitmq_exchange_durable
        )
        self._rabbitmq_client = RabbitmqClient(**self._rabbitmq_parameters)

        # set the component variables for which the values can also be received from the environmental variables
        self.__set_component_variables(
            simulation_id=simulation_id,
            component_name=component_name,
            epoch_message_topic=epoch_message_topic,
            simulation_state_message_topic=simulation_state_message_topic,
            status_message_topic=status_message_topic,
            error_message_topic=error_message_topic,
            other_topics=other_topics
        )

        self.__start_message = self.__load_start_message()

        self._is_stopped = True
        self.initialization_error = None
        # component goes to error state after it has sent an error message
        # in an error state the component only reacts to simulation state message "stopped" by stopping and
        # to epoch message and simulation state message "running" by sending an error message.
        # Note: for errors during initialization, the self.initialization_error variable should be used
        self._in_error_state = False
        self._error_description = ""

        self._simulation_state = AbstractSimulationComponent.SIMULATION_STATE_VALUE_STOPPED
        self._latest_epoch = 0
        self._completed_epoch = 0
        self._triggering_message_ids = [""]
        self._latest_status_message_id = None
        self._latest_epoch_message = None

        self._message_generator = MessageGenerator(self._simulation_id, self._component_name)
        # include the message id generator separately to be compatible with older code created before
        # the message generator class was implemented
        self._message_id_generator = self._message_generator.message_id_generator

        # lock that is set while the component is handling a message
        self._lock = asyncio.Lock()

    @property
    def simulation_id(self) -> str:
        """The simulation ID for the simulation."""
        return self._simulation_id

    @property
    def component_name(self) -> str:
        """The component name in the simulation."""
        return self._component_name

    @property
    def is_stopped(self) -> bool:
        """Returns True, if the component is stopped."""
        return self._is_stopped

    @property
    def is_client_closed(self) -> bool:
        """Returns True if the RabbitMQ client has been stopped."""
        return self._rabbitmq_client is None or self._rabbitmq_client.is_closed

    @property
    def initialization_error(self) -> Union[str, None]:
        """If the component has encountered an error during initialization contains an errorr message.
        If there was no error will be None."""
        return self._initialization_error

    @initialization_error.setter
    def initialization_error(self, initialization_error: Union[str, None]):
        """Set the initialization error message."""
        self._initialization_error = initialization_error

    @property
    def start_message(self) -> Optional[Dict[str, Any]]:
        """The JSON formatted Start message as Python dictionary.
           The Start message is set to None if the Start message is not available."""
        return self.__start_message

    async def start(self) -> None:
        """Starts the component."""
        if self.initialization_error is not None or self._in_error_state:
            if self.initialization_error is not None:
                LOGGER.error("Component has an initialization error: {}".format(self.initialization_error))
            else:
                LOGGER.error("Component because it is in an error state: {}".format(self._error_description))
            LOGGER.warning("The component will be started to allow the others to know about the error.")

        if self.is_client_closed:
            self._rabbitmq_client = RabbitmqClient(**self._rabbitmq_parameters)

        LOGGER.info("Starting the component: '{}'".format(self.component_name))
        topics_to_listen = self._other_topics + [
            self._simulation_state_topic,
            self._epoch_topic
        ]
        self._rabbitmq_client.add_listener(topics_to_listen, self.general_message_handler_base)
        self._is_stopped = False

    async def stop(self) -> None:
        """Stops the component."""
        LOGGER.info("Stopping the component: '{}'".format(self.component_name))
        self._simulation_state = AbstractSimulationComponent.SIMULATION_STATE_VALUE_STOPPED
        await self._rabbitmq_client.close()
        self._is_stopped = True

    def get_simulation_state(self) -> str:
        """Returns the simulation state attribute."""
        return self._simulation_state

    async def set_simulation_state(self, new_simulation_state: str) -> None:
        """Sets the simulation state. If the new simulation state is "running" and the current epoch is 0,
           sends a status message to the message bus. If initialization_error is None sends a ready status message.
           If it contains an error message sends an error status.
           If the new simulation state is "stopped", stops the dummy component."""
        if new_simulation_state in SimulationStateMessage.SIMULATION_STATES:
            self._simulation_state = new_simulation_state

            if new_simulation_state == AbstractSimulationComponent.SIMULATION_STATE_VALUE_RUNNING:
                if self._latest_epoch == 0:
                    if self.initialization_error is None:
                        if not self._in_error_state:
                            # normal situation
                            await self.send_status_message()
                        else:
                            # component is in an error state
                            await self.send_error_message(self._error_description)
                    else:
                        # the component could not be initialized properly
                        await self.send_error_message(self.initialization_error)

            elif new_simulation_state == AbstractSimulationComponent.SIMULATION_STATE_VALUE_STOPPED:
                await self.stop()

    def clear_epoch_variables(self) -> None:
        """Clears all the variables that are used to store information about the received input within the
           current epoch. This method is called automatically after receiving an epoch message for a new epoch.

           NOTE: this method should be overwritten in any child class that uses epoch specific variables
        """

    async def start_epoch(self) -> bool:
        """Starts a new epoch for the component.
           Returns True if the epoch calculations were completed for the current epoch.
        """
        if self._simulation_state == AbstractSimulationComponent.SIMULATION_STATE_VALUE_STOPPED:
            LOGGER.warning("Simulation is stopped, cannot start epoch calculations")
            return False

        if self._latest_epoch_message is None:
            LOGGER.warning("No epoch message received, cannot start epoch calculations.")
            return False

        if self._simulation_state != AbstractSimulationComponent.SIMULATION_STATE_VALUE_RUNNING:
            LOGGER.warning("Simulation in an unknown state: '{}', cannot start epoch calculations.".format(
                self._simulation_state))
            return False

        self._latest_epoch = self._latest_epoch_message.epoch_number

        if self._in_error_state:
            # Component is in an error state and instead of starting a new epoch will just send an error message.
            LOGGER.error("Component is in an error state: {}".format(self._error_description))
            await self.send_error_message(self._error_description)
            return True

        if self._completed_epoch == self._latest_epoch:
            LOGGER.warning("The epoch {} has already been processed.".format(self._completed_epoch))
            LOGGER.debug("Resending status message for epoch {}".format(self._latest_epoch))
            await self.send_status_message()
            return True

        if await self.ready_for_new_epoch():
            if await self.process_epoch():
                # The current epoch was successfully processed.
                self._completed_epoch = self._latest_epoch
                await self.send_status_message()
                LOGGER.info("Finished processing epoch {}".format(self._completed_epoch))
                return True

        # Some information required for the epoch is still missing.
        return False

    async def process_epoch(self) -> bool:
        """Process the epoch and do all the required calculations.
           Assumes that all the required information for processing the epoch is available.

           Returns False, if processing the current epoch was not yet possible.
           Otherwise, returns True, which indicates that the epoch processing was fully completed.
           This also indicated that the component is ready to send a Status Ready message to the Simulation Manager.

           NOTE: this method should be overwritten in any child class.
        """
        # Any calculations done within the current epoch would be included here.
        # Also sending of any result messages (other than Status message) would be included here.
        return True

    async def ready_for_new_epoch(self) -> bool:
        """Returns True, if all the messages required to start the processing for the current epoch are available.
        """
        if (self._simulation_state == AbstractSimulationComponent.SIMULATION_STATE_VALUE_RUNNING and
                not self.is_stopped and
                self._completed_epoch < self._latest_epoch):
            return await self.all_messages_received_for_epoch()

        # Some precondition for the epoch processing were not fulfilled.
        return False

    async def all_messages_received_for_epoch(self) -> bool:
        """Returns True, if all the messages required to start calculations for the current epoch have been received.
           Checks only that all the required information is available.
           Does not check any other conditions like the simulation state.

           NOTE: this method should be overwritten in any child class that needs more information
                 than just the Epoch message.
        """
        # The AbstractSimulationComponent needs no other information other than Epoch message for processing.
        return True

    async def general_message_handler_base(self, message_object: Union[BaseMessage, Any],
                                           message_routing_key: str) -> None:
        """Forwards the message handling to the appropriate function depending on the message type."""
        # only allow handling one message at a time
        async with self._lock:
            if isinstance(message_object, SimulationStateMessage):
                await self.simulation_state_message_handler(message_object, message_routing_key)

            elif isinstance(message_object, EpochMessage):
                await self.epoch_message_handler(message_object, message_routing_key)

            elif self._in_error_state:
                # component is in an error state and will not react to any other messages
                return

            else:
                # Handling of any other message types would be added to a separate function.
                await self.general_message_handler(message_object, message_routing_key)

    async def general_message_handler(self, message_object: Union[BaseMessage, Any],
                                      message_routing_key: str) -> None:
        """Forwards the message handling to the appropriate function depending on the message type.
           Assumes that the messages are not of type SimulationStateMessage or EpochMessage.

           NOTE: this method should be overwritten in any child class that listens to other messages.
        """
        if isinstance(message_object, AbstractMessage):
            LOGGER.debug("Received {} message from topic {}".format(
                message_object.message_type, message_routing_key))
        else:
            LOGGER.debug("Received unknown message: {}".format(str(message_object)))

    async def simulation_state_message_handler(self, message_object: SimulationStateMessage,
                                               message_routing_key: str) -> None:
        """Handles the received simulation state messages."""
        if message_object.simulation_id != self.simulation_id:
            LOGGER.info(
                "Received state message for a different simulation: '{}' instead of '{}'".format(
                    message_object.simulation_id, self.simulation_id))
        elif message_object.message_type != SimulationStateMessage.CLASS_MESSAGE_TYPE:
            LOGGER.info(
                "Received a state message with wrong message type: '{}' instead of '{}'".format(
                    message_object.message_type, SimulationStateMessage.CLASS_MESSAGE_TYPE))
        else:
            LOGGER.debug("Received a state message from {} on topic {}".format(
                message_object.source_process_id, message_routing_key))
            self._triggering_message_ids = [message_object.message_id]
            await self.set_simulation_state(message_object.simulation_state)

    async def epoch_message_handler(self, message_object: EpochMessage, message_routing_key: str) -> None:
        """Handles the received epoch messages."""
        if message_object.simulation_id != self.simulation_id:
            LOGGER.info(
                "Received epoch message for a different simulation: '{}' instead of '{}'".format(
                    message_object.simulation_id, self.simulation_id))
        elif message_object.message_type != EpochMessage.CLASS_MESSAGE_TYPE:
            LOGGER.info(
                "Received a epoch message with wrong message type: '{}' instead of '{}'".format(
                    message_object.message_type, EpochMessage.CLASS_MESSAGE_TYPE))
        elif (message_object.epoch_number == self._latest_epoch and
              self._latest_status_message_id in message_object.triggering_message_ids):
            LOGGER.info("Status message has already been registered for epoch {}".format(self._latest_epoch))
        else:
            LOGGER.debug("Received an epoch from {} on topic {}".format(
                message_object.source_process_id, message_routing_key))
            self._triggering_message_ids = [message_object.message_id]
            self._latest_epoch_message = message_object

            # clear and initialize any variables used to store input within the epoch
            self.clear_epoch_variables()

            # If all the epoch calculations were completed, send a new status message.
            if not await self.start_epoch():
                LOGGER.debug("Waiting for other required messages before processing epoch {}".format(
                    self._latest_epoch))

    async def send_status_message(self) -> None:
        """Sends a new status message to the message bus."""
        if self._in_error_state:
            # component is in an error state => send an error message instead
            await self.send_error_message(self._error_description)
            return

        status_message = self._get_status_message()
        if status_message is None:
            await self.send_error_message("Internal error when creating status message.")
        else:
            await self._rabbitmq_client.send_message(self._status_topic, status_message.bytes())
            self._completed_epoch = self._latest_epoch
            self._latest_status_message_id = status_message.message_id

    async def send_error_message(self, description: str) -> None:
        """Sends an error message to the message bus."""
        self._error_description = description
        self._in_error_state = True

        error_message = self._get_error_message(description)
        if error_message is None:
            # So serious error that even the error message could not be created => stop the component.
            LOGGER.error("Could not create an error message")
            await self.stop()
        else:
            await self._rabbitmq_client.send_message(self._error_topic, error_message.bytes())

    def _get_status_message(self) -> Union[StatusMessage, None]:
        """Creates a new status message and returns the created message object.
           Returns None, if there was a problem creating the message."""
        try:
            return self._message_generator.get_status_ready_message(
                EpochNumber=self._latest_epoch,
                TriggeringMessageIds=self._triggering_message_ids)

        except (ValueError, TypeError, MessageError) as message_error:
            LOGGER.error("Problem with creating a status message: {}".format(message_error))
            return None

    def _get_error_message(self, description: str) -> Union[StatusMessage, None]:
        """Creates a new error message and returns the created message object.
           Returns None, if there was a problem creating the message."""
        try:
            return self._message_generator.get_status_error_message(
                EpochNumber=self._latest_epoch,
                TriggeringMessageIds=self._triggering_message_ids,
                Description=description)

        except (ValueError, TypeError, MessageError) as message_error:
            LOGGER.error("Problem with creating an error message: {}".format(message_error))
            return None

    def __set_component_variables(self,
                                  simulation_id: Optional[str] = None,
                                  component_name: Optional[str] = None,
                                  epoch_message_topic: Optional[str] = None,
                                  simulation_state_message_topic: Optional[str] = None,
                                  status_message_topic: Optional[str] = None,
                                  error_message_topic: Optional[str] = None,
                                  other_topics: Optional[List[str]] = None):
        """Sets the topic name related variables for the object. Called automatically from the constructor."""
        if simulation_id is None:
            simulation_id = cast(str, EnvironmentVariable(SIMULATION_ID, str, "2020-01-01T00:00:00.000Z").value)
        if component_name is None:
            component_name = cast(str, EnvironmentVariable(SIMULATION_COMPONENT_NAME, str, "component").value)

        if simulation_state_message_topic is None:
            simulation_state_message_topic = cast(
                str, EnvironmentVariable(SIMULATION_STATE_MESSAGE_TOPIC, str, "SimState").value)
        if epoch_message_topic is None:
            epoch_message_topic = cast(str, EnvironmentVariable(SIMULATION_EPOCH_MESSAGE_TOPIC, str, "Epoch").value)
        if status_message_topic is None:
            status_message_topic = cast(
                str, EnvironmentVariable(SIMULATION_STATUS_MESSAGE_TOPIC, str, "Status.Ready").value)
        if error_message_topic is None:
            error_message_topic = cast(
                str, EnvironmentVariable(SIMULATION_ERROR_MESSAGE_TOPIC, str, "Status.Error").value)
        if other_topics is None:
            other_topics_from_env = cast(str, EnvironmentVariable(SIMULATION_OTHER_TOPICS, str, "").value)
            if other_topics_from_env:
                other_topics = ",".split(other_topics_from_env)
            else:
                other_topics = []

        # NOTE: No checking for the validity of the parameters is done here. If for example the simulation_id is
        #       invalid, the component should enter in an error state when trying to create a message.
        self._simulation_id = simulation_id
        self._component_name = component_name

        self._simulation_state_topic = simulation_state_message_topic
        self._epoch_topic = epoch_message_topic
        self._status_topic = status_message_topic
        self._error_topic = error_message_topic
        self._other_topics = other_topics

    @staticmethod
    def __get_rabbitmq_parameters(**kwargs: Union[str, int, bool, None]) -> Dict[str, Union[str, int, bool]]:
        """Returns a dictionary of parameters that can be used with the RabbitmqClient constructor.
        Only those parameters that are not None will be included in the dictionary."""
        return {
            parameter_name: parameter_value
            for parameter_name, parameter_value in kwargs.items()
            if parameter_value is not None
        }

    @staticmethod
    def __load_start_message() -> Optional[Dict[str, Any]]:
        """Tries to load the Start message from a file.
           The filename is gotten from the environmental variable SIMULATION_START_MESSAGE_FILENAME.
           If the message loading is successful, returns the message as a dictionary.
           Otherwise, returns None."""
        try:
            start_message_filename = EnvironmentVariable(SIMULATION_START_MESSAGE_FILENAME, str).value
            if isinstance(start_message_filename, str):
                with open(start_message_filename, mode="r", encoding="UTF-8") as start_message_file:
                    start_message = json.load(start_message_file)
                    if isinstance(start_message, dict):
                        return start_message

            LOGGER.warning("Could not load the Start message from file '{}'.".format(start_message_filename))
            return None

        except (OSError, TypeError, OverflowError, ValueError) as error:
            LOGGER.warning("Exception '{}' when trying to load the Start message from file: {}".format(
                type(error).__name__, error))
            return None
