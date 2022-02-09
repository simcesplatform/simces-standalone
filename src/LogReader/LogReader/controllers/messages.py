# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
Processor for get messages requests.
'''

import logging

import falcon

from LogReader import utils

log = logging.getLogger( __name__ )

class MsgController(object):
    '''
    Process requests about messages.
    '''

    def __init__(self, messageStore ):
        '''
        Initialize message request processor.
        messageStore: Module with method for getting messages.
        '''
        self._messageStore = messageStore
    
    def on_get_messages(self, req, resp, simId ):
        '''
        Get messages for simulation:
        simId: Simulation id from the URL path.
        '''
        log.debug( f'Get messages for simulation with id {simId} with parameters {req.params}.' )
        params = utils.validateMessageParams( req.params )
        result = self._messageStore.getMessages( simId, **params )
        # result None means that there is no simulation with the id (no corresponding mongodb collection for the messages)
        if result == None:
            raise falcon.HTTPNotFound( title = 'Simulation not found.', description = f'Simulation with id {simId} not found.' )
        
        resp.media = result
        
    def on_get_invalid_messages(self, req, resp, simId):
        '''
        Get invalid messages for simulation:
        simId: Simulation id from the URL path.
        '''
        log.debug( f'Get invalid messages for simulation with id {simId} with parameters {req.params}.' )
        result = self._messageStore.getInvalidMessages( simId, topic = req.params.get( 'topic' ) )
        # result None means that there is no simulation with the id
        if result is None:
            raise falcon.HTTPNotFound( title = 'Simulation not found.', description = f'Simulation with id {simId} not found.' )
        
        resp.media = result