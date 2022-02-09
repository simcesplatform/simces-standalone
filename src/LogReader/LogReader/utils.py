# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
Various utility functions.
'''

import datetime

import falcon
import dateutil.parser

def dateToIsoString( date ):
    '''
    Convert datetime to a ISO datetime string.
    '''
    # .isoformat marks utc as +00:00 but we want to use Z
    return date.isoformat().replace( '+00:00', 'Z' ) 

def jsonSerializeDate(obj):
    '''
    Used as a parameter for json.dumps to serialize datetime objects to JSON
    '''
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return dateToIsoString( obj )

def processDateParams( params, fromDateParam, toDateParam ):
    '''
    Validate and convert given date values from params dictionary to datetime objects.
    If there is an invalid value raises falcon.HTTPBadRequest.
    fromDateParam and toDateParam are the names of parameters containing start and end dates.
    Returns a tuple containing fromDate and toDate. Values are None if params did not contain any value for given parameter.
    '''
    fromDate = params.get( fromDateParam )
    if fromDate:
        try:
            fromDate = dateutil.parser.isoparse( fromDate  )
            
        except ValueError:
            raise falcon.HTTPBadRequest( title = "Invalid datetime value", description = f"Invalid datetime value for {fromDateParam}: {fromDate}" )
    
    toDate = params.get( toDateParam )
    if toDate:
        try:
            toDate = dateutil.parser.isoparse( toDate )
            
        except ValueError:
            raise falcon.HTTPBadRequest( title = "Invalid datetime value", description = f"Invalid datetime value for {toDateParam}: {toDate}" )
        
    return fromDate, toDate 
        
def paramToInt( paramName, params ):
    '''
    Convert value from given dictionary to int if present.
    paramName (str): Dictionary key whose value should be an integer. 
    params: A dictionary that should contain the integer. 
    Returns the parameter value as an integer or None if the request does not have a value for the parameter.
    Raises falcon.HTTPBadRequest if the value is not a valid integer.
    '''
    param = params.get( paramName )
    if param:
        try:
            param = int( param )
            
        except ValueError:
            raise falcon.HTTPBadRequest( title = "Invalid integer value", description = f"Invalid integer value for {paramName}: {param}." )
        
    return param

def validateMessageParams( params ):
    '''
    Validate and convert parameters related to getting messages .
    params (dict): Parameters for getting messages from for example query parameters from a falcon HTTP request. 
    Returns Dictionary containing the validated and converted parameters.
    Raises falcon.HTTPBadRequest if there are invalid values for sim dates, epoch numbers or onlyWarnings.
    '''
    validated = dict( params )
    # process and validate possible fromSimDate and toSimDate date parameters  
    validated['fromSimDate'], validated['toSimDate'] = processDateParams( params, 'fromSimDate', 'toSimDate' )
    # Get possible epoch filtering parameters and check that they are integers.
    validated['epoch'] = paramToInt( 'epoch', params )
    validated['startEpoch'] = paramToInt( 'startEpoch', params )
    validated['endEpoch'] = paramToInt( 'endEpoch', params )
    
    # get possible process ids and separate comma separated values into a list if the value is not already a list.
    validated['process'] = params.get( 'process' )
    if validated['process'] and type( validated['process'] ) != list:
        validated['process'] = validated['process'].split( ',' )
    
    # get onlyWarnings parameter and convert to bool if not already converted
    onlyWarnings = params.get( 'onlyWarnings', False )
    if onlyWarnings and type( onlyWarnings ) != bool:
        conversion = { 'true': True, 'false': False }
        try:
            onlyWarnings = conversion[onlyWarnings]
            
        except KeyError:
            raise falcon.HTTPBadRequest( title = 'Invalid value for onlyWarnings.', description = f'Value should be true or false but it was {onlyWarnings}.' )
    
    validated['onlyWarnings'] = onlyWarnings    
    # get topic parameter
    validated['topic'] = params.get( 'topic' )
    return validated