# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains general utils for working with simulation platform message classes."""

import datetime
from typing import Iterator, List, Optional, Type, Union

from tools.exceptions.messages import MessageError
from tools.message.abstract import AbstractMessage
from tools.message.epoch import EpochMessage
from tools.message.simulation_state import SimulationStateMessage
from tools.message.status import StatusMessage
from tools.message.utils import get_next_message_id
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


def abstract_message_generator(message_id_generator: Iterator[str], simulation_id: str, source_process_id: str) \
        -> Iterator[AbstractMessage]:
    """Generator for getting new instances of AbstractMessage with updated MessageId and Timestamp fields."""
    # TODO: add unit tests for this function
    while True:
        try:
            new_message_id = next(message_id_generator)
        except StopIteration:
            return

        yield AbstractMessage(
            Type=AbstractMessage.CLASS_MESSAGE_TYPE,
            SimulationId=simulation_id,
            SourceProcessId=source_process_id,
            MessageId=new_message_id
        )


class MessageGenerator:
    """Message generator class to help with the creation of simulation message objects."""
    def __init__(self, simulation_id: str, source_process_id: str, start_message_id: int = 1):
        # TODO: add checks for the parameters
        self._message_id_generator = get_next_message_id(source_process_id, start_message_id)
        self._abstract_message_generator = abstract_message_generator(
            self._message_id_generator, simulation_id, source_process_id)

    @property
    def message_id_generator(self) -> Iterator[str]:
        """Iterator that is used by the message generator to generate message ids."""
        return self._message_id_generator

    def get_abstract_message(self) -> AbstractMessage:
        """Returns a new AbstractMessage instance."""
        return next(self._abstract_message_generator)

    def get_message(self, message_class: Type[AbstractMessage], **kwargs) -> AbstractMessage:
        """Returns a new message instance of type message_class according to the given parameters.
           Throws an MessageError or ValueError exception if there is a problem with the given parameters.
        """
        # TODO: add unit tests for this function
        if message_class is EpochMessage:
            return self.get_epoch_message(**kwargs)
        if message_class is StatusMessage:
            return self.get_status_message(**kwargs)
        if message_class is SimulationStateMessage:
            return self.get_simulation_state_message(**kwargs)

        if not issubclass(message_class, AbstractMessage):
            raise MessageError("{:s} is not a subclass of {:s}".format(
                getattr(message_class, "__name__"), AbstractMessage.__name__))

        # No predefined function for the given message class type.
        # => Argument checking is done by the message class but no error messages related to extra arguments
        #    are given as in the other cases.
        abstract_message = self.get_abstract_message()
        return message_class(
            Type=message_class.CLASS_MESSAGE_TYPE,
            SimulationId=abstract_message.simulation_id,
            SourceProcessId=abstract_message.source_process_id,
            MessageId=abstract_message.message_id,
            Timestamp=abstract_message.timestamp,
            **kwargs
        )

    def get_epoch_message(self, EpochNumber: int, TriggeringMessageIds: List[str],
                          StartTime: Union[str, datetime.datetime], EndTime: Union[str, datetime.datetime],
                          LastUpdatedInEpoch: Optional[int] = None, Warnings: Optional[List[str]] = None,
                          IterationStatus: Optional[str] = None) \
            -> EpochMessage:
        """Returns a new EpochMessage corresponding to the given parameters.
           Throws an exception if the message creation was unsuccessful."""
        # pylint: disable=invalid-name
        abstract_message = self.get_abstract_message()
        return EpochMessage(
            Type=EpochMessage.CLASS_MESSAGE_TYPE,
            SimulationId=abstract_message.simulation_id,
            SourceProcessId=abstract_message.source_process_id,
            MessageId=abstract_message.message_id,
            Timestamp=abstract_message.timestamp,
            EpochNumber=EpochNumber,
            TriggeringMessageIds=TriggeringMessageIds,
            LastUpdatedInEpoch=LastUpdatedInEpoch,
            Warnings=Warnings,
            IterationStatus=IterationStatus,
            StartTime=StartTime,
            EndTime=EndTime
        )

    def get_status_message(self, Value: str, **kwargs) -> StatusMessage:
        """Returns a new StatusMessage corresponding to the given parameters.
           Throws an exception if the message creation was unsuccessful."""
        # pylint: disable=invalid-name
        if Value == StatusMessage.STATUS_VALUES[0]:   # should be "ready"
            return self.get_status_ready_message(**kwargs)
        if Value == StatusMessage.STATUS_VALUES[-1]:  # should be "error"
            return self.get_status_error_message(**kwargs)

        # unknown status value, try to create the message regardless
        abstract_message = self.get_abstract_message()
        return StatusMessage(
            Type=StatusMessage.CLASS_MESSAGE_TYPE,
            SimulationId=abstract_message.simulation_id,
            SourceProcessId=abstract_message.source_process_id,
            MessageId=abstract_message.message_id,
            Timestamp=abstract_message.timestamp,
            Value=Value,
            **kwargs
        )

    def get_status_ready_message(self, EpochNumber: int, TriggeringMessageIds: List[str],
                                 LastUpdatedInEpoch: Optional[int] = None, Warnings: Optional[List[str]] = None,
                                 IterationStatus: Optional[str] = None) -> StatusMessage:
        """Returns a new StatusMessage corresponding to the given parameters.
           Throws an exception if the message creation was unsuccessful."""
        # pylint: disable=invalid-name
        abstract_message = self.get_abstract_message()
        return StatusMessage(
            Type=StatusMessage.CLASS_MESSAGE_TYPE,
            SimulationId=abstract_message.simulation_id,
            SourceProcessId=abstract_message.source_process_id,
            MessageId=abstract_message.message_id,
            Timestamp=abstract_message.timestamp,
            EpochNumber=EpochNumber,
            TriggeringMessageIds=TriggeringMessageIds,
            LastUpdatedInEpoch=LastUpdatedInEpoch,
            Warnings=Warnings,
            IterationStatus=IterationStatus,
            Value=StatusMessage.STATUS_VALUES[0]  # should be "ready"
        )

    def get_status_error_message(self, EpochNumber: int, TriggeringMessageIds: List[str],
                                 Description: Optional[str] = None,
                                 LastUpdatedInEpoch: Optional[int] = None, Warnings: Optional[List[str]] = None,
                                 IterationStatus: Optional[str] = None) -> StatusMessage:
        """Returns a new StatusMessage corresponding to the given parameters.
           Throws an exception if the message creation was unsuccessful."""
        # pylint: disable=invalid-name
        abstract_message = self.get_abstract_message()
        return StatusMessage(
            Type=StatusMessage.CLASS_MESSAGE_TYPE,
            SimulationId=abstract_message.simulation_id,
            SourceProcessId=abstract_message.source_process_id,
            MessageId=abstract_message.message_id,
            Timestamp=abstract_message.timestamp,
            EpochNumber=EpochNumber,
            TriggeringMessageIds=TriggeringMessageIds,
            LastUpdatedInEpoch=LastUpdatedInEpoch,
            Warnings=Warnings,
            IterationStatus=IterationStatus,
            Value=StatusMessage.STATUS_VALUES[-1],  # should be "error"
            Description=Description
        )

    def get_simulation_state_message(self, SimulationState: str, Name: Optional[str] = None,
                                     Description: Optional[str] = None) -> SimulationStateMessage:
        """Returns a new StatusMessage corresponding to the given parameters.
           Throws an exception if the message creation was unsuccessful."""
        # pylint: disable=invalid-name
        abstract_message = self.get_abstract_message()
        return SimulationStateMessage(
            Type=SimulationStateMessage.CLASS_MESSAGE_TYPE,
            SimulationId=abstract_message.simulation_id,
            SourceProcessId=abstract_message.source_process_id,
            MessageId=abstract_message.message_id,
            Timestamp=abstract_message.timestamp,
            SimulationState=SimulationState,
            Name=Name,
            Description=Description
        )
