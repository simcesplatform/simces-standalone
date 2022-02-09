# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
Contains classes and methods for creating time series from messages of a simulation run.
The out side entry point for this module is the getTimeSeries method.
'''

from typing import List, Union, Dict, Any

import dateutil
from io import StringIO
import csv
from datetime import datetime

from LogReader.db import messages
from LogReader import utils

# the name of attribute containing the time series data in a time series block
seriesAttr = 'Series'
# attribute that contains the actual time series data 
seriesValueAttr = 'Values'
# name of the attribute containing the time index for the time series
timeIndexAttr = 'TimeIndex'
# quantity block attribute names
quantityValueAttr = 'Value'
quantityUnitAttr = 'UnitOfMeasure'

class TimeSeriesMessages():
    '''
    Represents the source data for time series creation.
    Has a list of messages and list of their attributes whose values should be included to the time series
    Can be used to iterate through the messages epoch by epoch. 
    '''
    
    def __init__(self, attrs: List[str], msgs: List[dict] ):
        '''
        Create a TimeSeriesMsgs object for the given messages and attributes.
        attrs: List of attributes. An attribute can refer to subattributes e.g. batteryState.chargePercentage.
        msgs: List of messages. Expected to be sorted by epoch in ascending order.
        '''
        # split each attribute to its parts.
        self._attrs = [ attr.split( '.' ) for attr in attrs ]
        self._msgs = msgs
        # index of the messages list pointing to first message for next epoch
        # in the beginning it is the first message 
        self._epochIndex = 0
        
    @property
    def attrs(self) -> List[str]:
        '''.Get the attributes.'''
        return self._attrs
    
    @property
    def msgs(self) -> List[dict]:
        '''
        Get the list of messages.
        '''
        return self._msgs
    
    def getNextEpochNumber(self) -> Union[int, None]:
        '''
        Get the number of the epoch this currently has messages for next.
        In other words this gives the number of the epoch the next call to getNextEpochMsgs
        will return messages for.
        If there are no longer messages left returns None.
        '''
        try:
            # get the epoch number of the message epoch index points to.
            return self.msgs[self._epochIndex][messages.epochNumAttr]
        
        except IndexError:
            return None
    
    def getNextEpochMsgs(self) -> Union[List[dict], None]:
        '''
        Get messages for current epoch i.e. the epoch whose number
        getNextEpochNumber returns.
        This is used to iterate through the messages epoch by epoch.
        I.e. after this is called return value of getNextEpochNumber changes.
        Returns None when there are no more messages.
        '''
        epoch = self.getNextEpochNumber()
        if epoch == None:
            # no more messages
            return None
        
        result = [] # put current epoch's messages here
        # find messages for this epoch
        for msg in self.msgs[self._epochIndex:]:
            if msg[messages.epochNumAttr] != epoch:
                break
                
            result.append( msg )
            # when done the epoch index will point at the start of the next epoch's messages
            self._epochIndex += 1
            
        return result
            
class TimeSeries(object):
    '''
    This class is used to create time series data from given messages.
    '''

    def __init__(self, timeSeriesMessages : List[TimeSeriesMessages], epochStartTimes: Dict[ int, datetime ] = None ):
        '''
        Specify the source data for the time series to be created.
        timeSeriesMessages: List of TimeSeriesMessage objects which determine the source data for the time series i.e. messages and the attributes.
        epochStartTimes: For each epoch there are messages for should contain key for the epoch number whose value is the epoch start time. Used when creating time series from attributes which do not use the time series block. 
        '''
        self._data = timeSeriesMessages
        self._epochStartTimes = epochStartTimes
        self._dataRemaining = True # have all messages been processed
        # the time series will be constructed here.
        self._result = { 'TimeIndex': [] }
        
    def createTimeSeries(self):
        '''
        Create the time series from the source data.
        '''
        # process messages one epoch at a time i.e. all messages that share the same epoch number
        # starting with the earliest epoch.  
        while self._findNextEpoch():
            # prepare the data for the current epoch.
            self._getEpochData()
            # create time series from the current epoch.
            self._processEpochData()
        
        # Remove temporary data used in time series creation from the actual result.    
        self._cleanResult()
            
    def _findNextEpoch(self) -> bool:
        '''
        Find the next epoch at least one of the TimeSeriesMessages objects has messages for.
        Set the self._nextEpoch to the number of that epoch.
        Return True if a epoch was found and False if not i.e there is no more messages.
        '''
        # get next epoch number from all TimeSeriesMessages objects to a list. 
        nextEpochs = [ tsMsgs.getNextEpochNumber() for tsMsgs in self._data if tsMsgs.getNextEpochNumber() != None ]
        if len( nextEpochs ) == 0:
            # none of the sources had a next epoch 
            self._nextEpoch = None
            return False
        
        # next epoch is the smallest epoch number.
        self._nextEpoch = min( nextEpochs )
        return True

    def _getEpochData(self):
        '''
        Prepares data for the next epoch to be actually processed by _processEpochData.
        '''
        # get all TimeSeriesMessages objects that have messages for the epoch we are currently processing.
        epochData = [ tsMsgs for tsMsgs in self._data if self._nextEpoch == tsMsgs.getNextEpochNumber() ]
        self._epochResult = [] # parts of the time series result that will be processed in this epoch.
        
        # find data for epoch from each TimeSeriesMessages object
        for tsMsgs in epochData:
            # find data from each message
            for msg in tsMsgs.getNextEpochMsgs():
                # get topic and source process from the message 
                topic = msg[messages.topicAttr]
                process = msg[messages.processAttr]
                # create or get the part of the result that contains data for this message 
                processData = self._result.setdefault( topic, {} ).setdefault( process, {} )
                # for each attribute in the TimeSeriesMessages see if this message has data for it.
                for attr in tsMsgs.attrs:
                    # parent of the data in the result
                    attrParent = processData
                    # source for the data in the message
                    source = msg
                    # is there data for the attribute
                    foundTimeSeries = False
                    # go through the attribute part by part
                    # attribute can refer to an attribute with a non time series block value, a complete time series block e.g. batteryState or one attribute inside it e.g. batteryState.chargePercentage.
                    for i in range( 0, len(attr)):
                        part = attr[i]
                        # go deeper in the message structure
                        source = source.get(part)
                        if source == None:
                            # message has no data for this attribute part
                            break
                        
                        # go deeper in result create or get the result part that will store this attribute's data
                        attrParent = attrParent.setdefault( part, {} )
                        
                        # is this message part a time series block
                        if self._isTimeSeries( source ):
                            foundTimeSeries = True
                            # done time series found
                            break
                        
                        # or is this a simple non time series block value or a QuantityBlock 
                        elif self._isSimpleValue( source ):
                            foundTimeSeries = True
                            # for processing this value we will create a "fake" time series block from it
                            source = self._createTimeSeriesBlockFromSimpleValue( source, part )
                            break
                        
                    if foundTimeSeries:
                        # we have data for the result
                        # add the current result part to this epoch's result if it is not already there
                        if not attrParent.get( 'inEpochResult' ):
                            attrParent['inEpochResult'] = True
                            self._epochResult.append( attrParent )
                            # temporarily add parts of th message to the result as data source
                            # index for keeping track of what item in the time index and values in the time series we are processing
                            attrParent['index'] = 0
                            # convert time index strings to datetime objects and add to the result.
                            attrParent['timeIndex'] = [ dateutil.parser.isoparse( date ) for date in source[timeIndexAttr] ]
                            if source.get( 'fake' ) == True:
                                # this was created from a simple value and when the result is cleaned has to be formatted  
                                attrParent['duplicate'] = True 
                        
                        # get the series part of the time series block    
                        series = source[seriesAttr]
                        if i == len( attr ) -1:
                            # we processed the whole attribute when we found the time series
                            # thus the attribute points to the whole time series block so everything under it should be included.
                            for key in series:
                                # get or create result part for this
                                # values will hold the actual time series result for this
                                resultSeries = attrParent.setdefault( key, { 'values': [] })
                                # add this epoch's source data temporarily to the result 
                                resultSeries['source'] = series[key][ seriesValueAttr ] 
                        
                        else:
                            # the attribute points to a specific data under the time series so only that will be included if it exists
                            attrData = series.get(attr[-1])
                            if attrData != None:
                                # get or create result part for this data
                                # values will hold the actual time series data
                                resultSeries = attrParent.setdefault( attr[-1], { 'values': [] })
                                # source will contain temporarily data for this epoch
                                resultSeries['source'] = attrData[ seriesValueAttr ]
        
        # delete the inEpochResult key from the epoch result
        # this was internal data for just this method.                         
        for data in self._epochResult:
            del data['inEpochResult']
    
    def _isTimeSeries(self, value: dict ) -> bool:
        '''
        Check if the given message part is a time series block.
        '''
        return isinstance( value, dict ) and seriesAttr in value and timeIndexAttr in value
    
    def _isSimpleValue(self, value) -> bool:
        '''
        Check if the message part is a simple string, number, boolean or QuantityBlock value.
        '''
        return (type( value ) in [ str, bool, int, float ] or 
            (isinstance( value, dict ) and quantityValueAttr in value and quantityUnitAttr in value) )
    
    def _createTimeSeriesBlockFromSimpleValue( self, value: Union[ int, float, str, bool, dict ], attrName: str ) -> dict:
        '''
        Creates a "fake" time series block from the given value stored under the given attribute name.
        '''
        timeSeries = {}
        # indicate that this is not a real time series block from a message
        timeSeries['fake'] = True
        # time index will have one value which is the start time for the current epoch being processed.
        # time series processing expects it to be a string
        timeSeries[ timeIndexAttr ] = [ utils.dateToIsoString( self._epochStartTimes[ self._nextEpoch ] ) ]
        # The Series part will contain one attribute with one value
        # measurement unit is not required here 
        timeSeries[ seriesAttr ] = {
            attrName: {
                # value is either a string, number, boolean or quantity block containing a value.
                seriesValueAttr: [ value if not isinstance( value, dict ) else value[ quantityValueAttr ] ]
            }
        }
        
        return timeSeries
                            
    def _handleMissingDataForEpoch(self):
        '''
        Ensures that the result is up to date before data for a epoch is processed.
        Ensures that all attributes in the result has as many values as there are items in time index.
        This is done by adding as many None values as there is missing data.
        '''
        for data in self._epochResult:
            for attr in data:
                # internal data which needs no processing
                if attr == 'index' or attr == 'timeIndex' or attr == 'duplicate':
                    continue
                
                values = data[attr]['values']
                self._addMissingValues( values )
                
    def _addMissingValues(self, values: list ):
        '''
        Makes values as long as time index by adding None values.
        '''                
        timeIndex = self._result['TimeIndex']
        numValues = len( timeIndex )
        missing = numValues -len( values )
        if missing > 0:
            values.extend( missing *[ None ] )
        
    def _processEpochData(self):
        '''
        Processes epoch data found by _getEpochData.
        The values from epoch data are added to the result and the time index is expanded to cover the current epoch.
        '''
        # ensure that values lists in epoch result are as long as the time index before starting.
        self._handleMissingDataForEpoch()
        timeIndex = self._result['TimeIndex']
        # process data until there is nothing left
        while True:
            # determine the earliest moment the epoch result has values for
            # in each result item index is used to keep a record of which time index item and for each attribute which value  should be processed next.
            # index will be marked None if there is no longer data available i.e. everything in that item has been processed.
            # from each result item get the current item from its time index i.e. the message time index 
            nextTimes = [ item['timeIndex'][ item['index'] ] for item in self._epochResult if item['index'] != None ]
            if len( nextTimes ) == 0:
                # no more time index items everything has been processed.
                break 
            
            # from the time items found get the earliest
            nextTime = min( nextTimes )
            # create time index entry for the new moment.
            timeIndex.append( { 'epoch': self._nextEpoch, 'timestamp': nextTime })
            # go through each epoch result item and see if it has data for the current moment.
            for item in self._epochResult:
                # what part of this item should be processed next.
                index = item['index']
                # item has data if everything has not yet been processed
                # and the next time index entry is the same as the moment we are currently processing.
                hasData = index != None and nextTime == item['timeIndex'][index]
                
                # process each attribute under the item that has values
                for key in item:
                    if key in [ 'index', 'timeIndex', 'duplicate' ]:
                        continue
                    
                    attrData = item[key]
                    # the new value to be added to the result
                    # assume None first i.e. there is no data for this moment.
                    value = None
                    if hasData:
                        # there is data i.e. the message data in the index position corresponds to the current moment.
                        value = attrData['source'][index]
                    
                    # add value to result        
                    attrData['values'].append( value )
                
                if hasData:
                    # the data at index position has been processed so increment index.    
                    index += 1
                    if index == len( item['timeIndex'] ):
                        # all data has been processed.
                        index = None
                    
                    item['index'] = index
                    
    def _cleanResult(self, result = None ) -> Any:
        '''
        After the time series result is complete, this method cleans any temporary data
        used by _processEpochData and formats the result properly. This method is used recursively.
        result (dict): Part of the result that should be cleaned. If None starts from the top level of self._result.
        Return value will be inserted to the current part of the result.
        '''
        if result == None:
            result = self._result
        
        if 'index' in result and 'timeIndex' in result:
            # contains temporary stuff used when creating the result that should now be removed.
            del result['index']
            del result['timeIndex']
            # is this from a fake time series block created from a simple value
            duplicate = result.get( 'duplicate' )
            if duplicate:
                del result['duplicate'] 
            # process each actual time series attribute under this
            for attr in result:
                # get the actual result values for the attribute
                values = result[attr]['values']
                # There may not have been data for this attribute in every epoch since it last got data so ensure it is as long as time index
                # by adding None values   
                self._addMissingValues(values)
                # move the values directly under the attribute
                # previously the attribute had the actual values and for each epoch source values for that epoch.
                result[attr] = values 
            
            # nothing more to process for this result part.
            if duplicate:
                # with simple values attribute name is duplicated because of the fake time series block creation
                # e.g. under RealPower there is a time series block with series for RealPower
                # this will remove the duplicated attribute name from the result.
                result = values    
            return result
        
        # nothing here to process go deeper in result structure excluding the time index.
        for key in result:
            if key != 'TimeIndex':
                # clean this result part
                result[key] = self._cleanResult( result[key] )
        
        return result
            
    def getResult(self) -> dict:
        '''
        After the time series has been created this is used to get the result.
        Result is a dictionary with the same data structure as specified in the API document for time series response json. Note timestamps in TimeIndex are datetime objects.
        '''
        return self._result

class TimeSeriesCsvConverter():
    '''
    Converts time series results created by TimeSeries into CSV.
    '''
    
    def __init__(self, timeSeries: dict, target = None ):
        '''
        Create Csv converter for the given time series result.
        timeSeries: A time series result created by TimeSeries and returned by its getResult method.
        target: A file like object which has a write method. The csv is saved here. If this is not given an internally created io.StringIO object is used which allows getting the time series as a string.
        '''
        self._timeSeries = timeSeries
        self._target = target
        if target == None:
            # the newline = '' is required by the csv module.
            self._target = StringIO( newline = '' )
            
    def createCsv(self):
        '''
        Create the csv from the result.
        It is stored to the given or internally created target.
        '''
        # create the csv headers i.e. column titles from the result.
        self._createHeaders()
        timeIndex = self._timeSeries['TimeIndex']
        # create a row from each time index item and related attribute values.
        for i in range( 0, len( timeIndex )):
            time = timeIndex[i]
            # build the row as an dictionary.
            # The time index item is used as is. except timestamp is converted from datetime to string. 
            row = dict( time )
            row['timestamp'] = utils.dateToIsoString( row['timestamp'] )
            # add the corresponding attribute values to row
            row.update( { column: values[i] for (column, values) in self._columns.items() })
            self._csv.writerow( row )
        
    def _createHeaders(self):
        '''
        Create the csv row headers and prepare the data for creating the rest of the csv. 
        '''
        # dictionary where the csv column names are the keys and the attribute value lists are the values.
        self._columns = {}
        # a column name will be formed from the topic, process name and attribute names.
        for topic in self._timeSeries:
            if topic == 'TimeIndex':
                # ignore the time index part of the result, rest are topics
                continue
            
            topicData = self._timeSeries[ topic ] 
            for process in topicData:
                processData = topicData[ process ]
                # process attributes for each process
                self._getProcessAttrs( processData, topic +':' +process )
        
        # column names are epoch, timestamp and the attribute value column names.
        columnNames = [ 'epoch', 'timestamp' ] +list( self._columns.keys() )
        # create a csv dictwirter that writes to the target and uses the given column names.        
        self._csv = csv.DictWriter( self._target, columnNames, delimiter = ';' )
        # write the first row i.e. the headers
        self._csv.writeheader()
        
    def _getProcessAttrs(self, data: dict, columnName: str ):
        '''
        Recursively get attribute data starting from the process data.
        data: Part of the time series result starting from the process level.
        columnName: Beginning of the column name that everything in this result part will share.
        '''
        for attr in data:
            value = data[attr]
            # include the attribute name to the column name
            newColumnName = columnName +'.' +attr
            if type( value ) == list:
                # found actual attribute values
                self._columns[newColumnName] = value
                
            else:
                # go deeper in the result.
                self._getProcessAttrs( value, newColumnName)
        
    def getTarget(self):
        '''
        Gets the file like target to which the time series csv has been written after createCsv has been called.
        From the default io.StringIO the csv can be got as an string with its getvalue method.
        ''' 
        return self._target
    

class TimeSeriesMessageFilter():
    '''
    When getting a time series this is used to specify message query criteria for getting messages
    from which the time series will be created.
    '''
    
    def __init__(self, attrs: List[str], process = None, topic = None ):
        '''
        attrs: List of message attributes from which time series should be created.
        process: List of process ids for querying messages.
        topic (str): Topic for querying messages.
        ''' 
        self._attrs = attrs
        self._process = process
        self._topic = topic
        
    @property
    def attrs(self) -> List[str]:
        '''
        Get the attributes list.
        '''
        return self._attrs
    
    @property
    def process(self) -> List[str]:
        '''
        Get the process ids list.
        '''
        return self._process
    
    @property
    def topic(self) -> str:
        '''
        Get the topic.
        '''
        return self._topic
    
def getTimeSeries( messageStore, simId: str, messageFilters: List[TimeSeriesMessageFilter], epoch: int = None, startEpoch: int = None, endEpoch: int = None, fromSimDate: datetime = None, toSimDate: datetime = None, csv: bool = False ) -> Union[dict, str, None]:
    '''
    Gets a time series based on given parameters.
    messageStore: Source for getting messages which should have a getMessages method.
    simId: Id of simulation from whose messages time series will be created.
    timeSeriesMessageFilters: For each TimeSeriesMessageFilter the corresponding messages and their attributes will be included to the time series.
    csv: Should the time series be converted to csv.
    The other parameters are common parameters used by getMessages and will be used with each TimeSeriesMessageFilter.
    Returns: a string if csv is requested. Otherwise a dictionary is returned whose structure corresponds to the time series response JSON from the API specification. If there is no simulation with given id None is returned. 
    '''
    # for each TimeSeriesMessageFilter a TimeSeriesMessages object will be created that has the corresponding messages.
    timeSeriesMsgsLst = []
    # we have to have the start time of each epoch that we have messages for
    # for that we will get all epoch messages starting from the first epoch and ending at the last epoch we have messages for  
    minEpoch = None
    maxEpoch = 0 
    for msgFilter in messageFilters:
        # get messages sorted by epoch number which is the sort order time series creation requires.
        msgs = messageStore.getMessages( simId, epoch = epoch, startEpoch = startEpoch, endEpoch = endEpoch, fromSimDate = fromSimDate, toSimDate = toSimDate, process = msgFilter.process, topic = msgFilter.topic, sortAttr = messages.epochNumAttr )
        if msgs == None:
            # the simulation was not found.
            return None
        
        # ensure that each message has a epoch number which is required by time series creation.
        msgs = [ message for message in msgs if messages.epochNumAttr in message ]
        timeSeriesMsgsLst.append( TimeSeriesMessages( msgFilter.attrs, msgs ))
        
        # if we have messages check for first and last epoch
        if len( msgs ) > 0:
            maxEpoch = max( maxEpoch, msgs[-1][ messages.epochNumAttr ])
            if minEpoch == None:
                # first value for this
                minEpoch = msgs[0][messages.epochNumAttr]
            
            else:
                minEpoch = min( minEpoch, msgs[0][messages.epochNumAttr] )
    
    epochStartTimes = {} # empty if there are no messages
    # minEpoch is none is there were no messages
    if minEpoch != None:
        epochMsgs = messageStore.getMessages( simId, startEpoch = minEpoch, endEpoch = maxEpoch, topic = messages.epochTopic )
        # get start time for each epoch: key epoch number value its start time
        epochStartTimes = { msg[ messages.epochNumAttr ]: msg[ messages.epochStartAttr ] for msg in epochMsgs }    
    
    # time series object for creating the time series 
    timeSeries = TimeSeries( timeSeriesMsgsLst, epochStartTimes )
    timeSeries.createTimeSeries()
    result = timeSeries.getResult()
    # if csv is required convert to csv otherwise just return the result as is.
    if csv:
        csvConverter = TimeSeriesCsvConverter( result )
        csvConverter.createCsv()
        result = csvConverter.getTarget().getvalue()
        
    return result