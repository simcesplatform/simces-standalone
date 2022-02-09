# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Kalle Ruuth <kalle.ruuth@tuni.fi>
'''
Tests for the StaticTimeSeriesResource component.
'''

from typing import List, Tuple, Union, cast
import os 
import pathlib

from tools.messages import AbstractMessage
from domain_messages.resource import ResourceStateMessage 

from tools.tests.components import MessageGenerator, TestAbstractSimulationComponent

from static_time_series_resource.component import create_component, RESOURCE_TYPE, RESOURCE_STATE_CSV_FILE 
from domain_tools.resource.resource_state_source import ResourceState 

class ResourceStateMessageGenerator( MessageGenerator ):
    """Message generator for the tests. extended to produce the expected ResourceState messages."""
    
    # resource states that are the basis of the expected messages 
    states = [ None, # nothing for epoch 0
          ResourceState( real_power = -10.0, reactive_power = -1.0, customerid = 'GridA-1', node = None ),
          ResourceState( real_power = -11.5, reactive_power = -2.0, customerid = 'GridA-1', node = 1 ),
          ResourceState( real_power = -9.1, reactive_power = 0.0, customerid = 'GridA-1', node = 2 )
      ]

    def get_resource_state_message(self, epoch_number: int, triggering_message_ids: List[str]) -> Union[ResourceStateMessage, None]:
        """Get the expected ResourceStateMessage for the given epoch."""
        if epoch_number == 0 or epoch_number >= len( self.states ):
            return None
        
        # get the resource state for this epoch
        state = self.states[ epoch_number ]
        self.latest_message_id = next(self.id_generator)
        resource_state_message = ResourceStateMessage(**{
            "Type": "ResourceState",
            "SimulationId": self.simulation_id,
            "SourceProcessId": self.process_id,
            "MessageId": self.latest_message_id,
            "EpochNumber": epoch_number,
            "TriggeringMessageIds": triggering_message_ids,
            "RealPower": state.real_power,
            "ReactivePower": state.reactive_power,
            "CustomerId": state.customerid,
            "Node": state.node
        })
        
        return resource_state_message

class TestStaticTimeSeriesResourceCompoment( TestAbstractSimulationComponent ):
    """Unit tests for StaticTimeSeriesResource.""" 
    
    # the method which initializes the component with the used csv file source
    component_creator = create_component
    message_generator_type = ResourceStateMessageGenerator
    normal_simulation_epochs = 3
    
    # specify resource type and the csv file to be used via environment variables
    os.environ[ RESOURCE_TYPE ] = 'Load'
    os.environ[ RESOURCE_STATE_CSV_FILE ] = str( pathlib.Path(__file__).parent.absolute() / 'load1.csv' )
    
    def get_expected_messages(self, component_message_generator: ResourceStateMessageGenerator, epoch_number: int, triggering_message_ids: List[str]) -> List[Tuple[AbstractMessage, str]]:
        """Get the messages and topics the component is expected to publish in given epoch."""
        if epoch_number == 0:
            return [
                (component_message_generator.get_status_message(epoch_number, triggering_message_ids), "Status.Ready")
                ]
            
        return [
            (component_message_generator.get_resource_state_message(epoch_number, triggering_message_ids), "ResourceState.Load." +self.component_name ),
            (component_message_generator.get_status_message(epoch_number, triggering_message_ids), "Status.Ready")
        ]
        
    def compare_resource_state_message(self, first_message: ResourceStateMessage, second_message: ResourceStateMessage ):
        """Check that the two ResourceState messages have the same content."""
        self.compare_abstract_result_message(first_message, second_message)
        self.assertEqual( first_message.reactive_power, second_message.reactive_power )
        self.assertEqual( first_message.real_power, second_message.real_power )
        self.assertEqual( first_message.customerid, second_message.customerid )
        self.assertEqual( first_message.node, second_message.node )
        
    def compare_message(self, first_message: AbstractMessage, second_message: AbstractMessage) -> bool:
        """Override the super class implementation to add the comparison of ResourceState messages.""" 
        if super().compare_message(first_message, second_message):
            return True

        if isinstance(second_message, ResourceStateMessage ):
            self.compare_resource_state_message(cast(ResourceStateMessage, first_message), second_message)
            return True

        return False
