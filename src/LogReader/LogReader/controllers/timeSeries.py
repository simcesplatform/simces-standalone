# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
Includes the class for handling time series API requests. 
'''
import logging

import falcon

from LogReader import utils
from LogReader.services import timeSeries 

log = logging.getLogger( __name__ )

class TimeSeriesController():
    '''
    Request handler class for requests to time series API.
    '''

    def __init__(self, messageStore ):
        '''
        Create the request handler.
        messageStore: Module for getting messages from db. Should have a getMessages method.
        '''
        self._messageStore = messageStore
        
    def on_get(self, req, resp, simId ):
        '''
        Handle the get request for time series.
        '''
        log.debug( f'Get time series for simulation with id {simId} with parameters {req.params}.' )
        # get and validate the request parameters that are common with getting messages.
        params = utils.validateMessageParams( req.params )
        # check is there a format parameter and does it have valid value.
        dataFormat = req.get_param( 'format' )
        if dataFormat != None:
            del params['format'] # no longer required here and causes an error otherwise later
            if dataFormat not in [ 'json', 'csv' ]:
                raise falcon.HTTPBadRequest( title = 'Invalid time series result format.', description = f'Format should be json or csv instead of {format}.' )
            
        else:
            dataFormat = 'json' # no format given json is the default
        
        # get comma separated list of attributes and convert to list
        # This parameter is required.      
        attrs = req.get_param( 'attrs', required = True ).split( ',' )
        # this api can create time series just for one set of messages specified below
        msgFilter = timeSeries.TimeSeriesMessageFilter( attrs, topic = params.get( 'topic' ), process = params.get( 'process' ))
        # contents of params will be used as keyword parameters for getTimeSeries method
        # so anything not expected by that method has to be removed. 
        del params['attrs']
        del params['process']
        del params['topic']
        del params['onlyWarnings']
        
        result = timeSeries.getTimeSeries( self._messageStore, simId, [ msgFilter ], csv = dataFormat == 'csv', **params )
        if result == None:
            raise falcon.HTTPNotFound( title = 'Simulation not found.', description = f'Simulation with id {simId} not found.' )
        
        if dataFormat == 'json':
            # just let falcon convert the result dict to json
            resp.media = result
            
        elif dataFormat == 'csv':
            resp.content_type = 'text/csv'
            resp.body = result