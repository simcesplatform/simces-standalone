# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
Processors for requests related to simulations.
'''

import logging

import falcon

import LogReader.utils


log = logging.getLogger( __name__ )

class SimController:
    '''
    Process requests about simulations.
    '''
    
    def __init__( self, simulationStore ):
        '''
        Initialize simulation request processor.
        simulationStore: module used to get simulations from database.
        '''
        self._simulationStore = simulationStore
        
    def on_get_simulations( self, req, resp ):
        '''
        Process request for getting list of simulations.
        '''
        log.debug( f'Got request for  simulations with parameters: {req.params}.' )
        # process and validate possible fromDate and toDate date parameters
        fromDate, toDate = LogReader.utils.processDateParams( req.params, 'fromDate', 'toDate' ) 
        
        results = self._simulationStore.getSimulations( fromDate, toDate )
        resp.media = results
        
    def on_get_simulation(self, req, resp, simId ):
        '''
        Response handler for get simulation by id.
        simId (str): URI template parameter for simulation id.
        '''
        log.debug( f'Get simulation with id {simId}.' )
        result = self._simulationStore.getSimulationById( simId )
        if result == None:
            raise falcon.HTTPNotFound( title = 'Simulation not found.', description = f'Simulation with id {simId} not found.' )
        
        resp.media = result