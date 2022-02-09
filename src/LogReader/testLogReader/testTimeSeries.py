# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
Tests for the time series service module.
'''
import unittest
import functools
import copy
import csv
from typing import List, Dict, Tuple, Any

from LogReader.db import messages
from LogReader.services import timeSeries
from testLogReader import dataManager, testingUtils

# define test related data

# messages from batteries that have the same time series update interval 
batteryMsgIds = [ 'battery1-1', 'battery2-1', 'battery1-2', 'battery2-2' ]
# solarplant messages which are not missing data.
solarPlantOkMsgIds = [ 'solarPlant1-1', 'solarPlant1-2' ]
# includes the solarplant message which does not have power information
solarPlantMsgIds = solarPlantOkMsgIds +[ 'solarPlant1-3' ]
# messages from battery that has a different time series interval
battery3MsgIds = [ 'battery3-1', 'battery3-2' ]
# battery messages which have different time series interval from each other
battery_1_3MsgIds = [ 'battery1-1', 'battery3-1', 'battery1-2', 'battery3-2' ]
# battery messages where one message is missing from a epoch
batteryMsgIdsMissing = [ 'battery1-1', 'battery1-2', 'battery2-2' ]
batteryMsgIdsMissing2 = [ 'battery1-1', 'battery2-1', 'battery2-2' ]
# names of various message attributes
chargePercentageAttr = 'batteryState.chargePercentage'
capacityAttr = 'batteryState.capacity'
batteryStateAttr = 'batteryState'
realPowerAttr = 'RealPower'
reactivePowerAttr = 'ReactivePower'

# each test method is executed multiple times with different scenarios whose parameters vary
# these scenarios are defined here. 
testScenarios = [
    # name is used in identifying actual and expected test result files 
    { 'name': 'battery state from battery 1 and 2',
     # define the basis of time series creation i.e. the messages and their attributes
     'timeSeriesParams': [ 
         {'msgIds': batteryMsgIds,
         'attrs': [ batteryStateAttr ]}
     ],
     # for each test method define information about expected results.
     # list epochs there are messages for
     'testGetMessagesForNextEpoch': [[ 1, 2 ]],
     # for others define the result type csv or json
     # todo: this should not really be needed since for each method this is the same
     # "noResult": True can be added to indicate that actual results should not be checked against expected results
     # can be used for example when adding a new scenario and there is not yet expected results.
     # if the method name is missing this scenario will not be tested with that method
     'testGetEpochData': { 'fileType': 'json' },
     'testCreateTimeSeries': { 'fileType': 'json' },
     'testCreateCsvHeaders': { 'fileType': 'csv' },
     'testCreateCsv': { 'fileType': 'csv' } },
    { 'name': 'real power from solar plant 1',
     'timeSeriesParams': [ 
         {'msgIds': solarPlantOkMsgIds,
         'attrs': [ realPowerAttr ]}
     ],
     'testGetMessagesForNextEpoch': [[ 1, 2 ]],
     'testGetEpochData': { 'fileType': 'json' },
     'testCreateTimeSeries': { 'fileType': 'json'  },
     'testCreateCsvHeaders': { 'fileType': 'csv' },
     'testCreateCsv': { 'fileType': 'csv' } },
    { 'name': 'real and reactive power from solar plant 1',
     'timeSeriesParams': [ 
         {'msgIds': solarPlantOkMsgIds,
         'attrs': [ realPowerAttr, reactivePowerAttr ]}
     ],
     'testGetMessagesForNextEpoch': [[ 1, 2 ]],
     'testGetEpochData': { 'fileType': 'json' },
     'testCreateTimeSeries': { 'fileType': 'json' },
     'testCreateCsvHeaders': { 'fileType': 'csv' },
     'testCreateCsv': { 'fileType': 'csv' }},
    { 'name': 'charge percentage from battery 1 and 2',
     'timeSeriesParams': [ 
         {'msgIds': batteryMsgIds,
         'attrs': [ chargePercentageAttr ],}
     ],
     'testGetMessagesForNextEpoch': [[ 1, 2 ]],
     'testGetEpochData': { 'fileType': 'json' },
    'testCreateTimeSeries': { 'fileType': 'json' },
     'testCreateCsvHeaders': { 'fileType': 'csv' },
     'testCreateCsv': { 'fileType': 'csv' } },
    # battery3 is missing values for the capacity attribute 
    { 'name': 'missing attributes from battery 3',
     'timeSeriesParams': [ 
         {'msgIds': battery3MsgIds,
         'attrs': [ chargePercentageAttr, capacityAttr ],}
     ],
     'testGetMessagesForNextEpoch': [[ 1, 2 ]],
     'testGetEpochData': { 'fileType': 'json' },
    'testCreateTimeSeries': { 'fileType': 'json' },
     'testCreateCsvHeaders': { 'fileType': 'csv' },
     'testCreateCsv': { 'fileType': 'csv' } },
    # no data from one battery for one epoch
    { 'name': 'battery state from battery 1 and 2 with missing data',
     'timeSeriesParams': [ 
         {'msgIds': batteryMsgIdsMissing,
         'attrs': [ batteryStateAttr ]}
     ],
     'testGetMessagesForNextEpoch': [[ 1, 2 ]],
     'testGetEpochData': { 'fileType': 'json' },
     'testCreateTimeSeries': { 'fileType': 'json' },
     'testCreateCsvHeaders': { 'fileType': 'csv' },
     'testCreateCsv': { 'fileType': 'csv', } },
    { 'name': 'battery state from battery 1 and 2 with missing data 2',
     'timeSeriesParams': [ 
         {'msgIds': batteryMsgIdsMissing2,
         'attrs': [ batteryStateAttr ]}
     ],
     'testGetMessagesForNextEpoch': [[ 1, 2 ]],
     'testGetEpochData': { 'fileType': 'json' },
     'testCreateTimeSeries': { 'fileType': 'json' },
     'testCreateCsvHeaders': { 'fileType': 'csv' },
     'testCreateCsv': { 'fileType': 'csv', } },
    # update interval in time series is different
    { 'name': 'different time indexes',
     'timeSeriesParams': [ 
         {'msgIds': battery_1_3MsgIds,
         'attrs': [ chargePercentageAttr ],}
     ],
     'testGetMessagesForNextEpoch': [[ 1, 2 ]],
     'testGetEpochData': { 'fileType': 'json' },
    'testCreateTimeSeries': { 'fileType': 'json' },
     'testCreateCsvHeaders': { 'fileType': 'csv' },
     'testCreateCsv': { 'fileType': 'csv' } }
]

def testWithAllScenarios( testName: str ):
    '''
    Returns a decorator which is used to execute test methods for each scenario.
    testName is used in test result file names. 
    '''
    def decorator(test ):
        '''
        Decorator used to execute given test method for all scenarios.
        '''
        @functools.wraps(test)
        def wrapper(testInstance):
            '''
            The actual functionality of the decorator.
            TestInstance is the object the test method is called for.
            '''
            # save test name to instance so it can be used later when working with result files
            testInstance._testName = testName
            # test method stores its actual results here so they can be saved to a file later
            testInstance._results = {}
            for scenario in testScenarios:
                # tells if the actual test checks are executed or the results just saved to file without checking.
                testInstance._skipAsserts = False
                # get the TimeSeries object for the scenario's messages and attributes, and the expected results.
                timeSeries, expected = testInstance.getTestData( scenario )
                if expected == None:
                    # this test will not be executed for this scenario.
                    continue
                
                # used later when storing actual results .    
                testInstance._scenarioName = scenario['name']
                with testInstance.subTest( scenario = scenario['name'] ):
                    # execute test with given TimeSeries creator object and expected results.
                    test( testInstance, timeSeries, expected )
                        
        return wrapper
    return decorator

class TestTimeSeries(unittest.TestCase):
    '''
    Tests for the classes in timeSeries module.
    '''
    
    @classmethod
    def setUpClass(cls):
        '''
        Get the test messages from file.
        ''' 
        cls._testData = dataManager.readFile( 'messages1.json' )

    def tearDown(self):
        '''
        Stores the actual test results for each scenario into a file.
        ''' 
        for scenarioName in self._results:
            fileName = testingUtils.getTestDataResultFileName( self._testName, scenarioName, True, self._fileType )
            dataManager.writeFile( fileName, self._results[scenarioName] )

    @classmethod
    def _getMessagesForIds(cls, msgIds: List[str] ) -> List[dict]:
        '''
        Gets messages with given ids from the test data.
        '''
        return [ msg for msg in cls._testData if msg[messages.idAttr] in msgIds ]

    @testWithAllScenarios( 'testGetMessagesForNextEpoch' )
    def testGetMessagesForNextEpoch(self, timeSeries: timeSeries.TimeSeries, expected: List[List[int]] ):
        '''
        Test that TimeSeriesMessage objects can iterate properly through their messages epoch by epoch.
        ''' 
        # for each TimeSeriesMessages object the TimeSeries has expected has a list of epoch numbers the TimeSeriesMessages' should have messages for 
        for i in range( 0, len(expected)):
            # get the TimeSeriesMessages
            tsMsgs = timeSeries._data[i]
            for epoch in expected[i]:
                # messages we expect to get for this epoch.
                expectedMsgs = [ msg for msg in tsMsgs.msgs if msg[messages.epochNumAttr] == epoch ]
                # number of epoch we should get messages for 
                nextEpoch = tsMsgs.getNextEpochNumber()
                self.assertEqual( nextEpoch, epoch ) 
                epochMsgs = tsMsgs.getNextEpochMsgs()
                testingUtils.checkMessages( self, epochMsgs, expectedMsgs )
                
            # there should not be more epochs and messages.    
            self.assertIsNone( tsMsgs.getNextEpochNumber() )    
            self.assertIsNone( tsMsgs.getNextEpochMsgs() )

    @testWithAllScenarios( 'testGetEpochData' )
    def testGetEpochData(self, timeSeries: timeSeries.TimeSeries, expected: Dict[str, List[dict]]):
        '''
        Test that TimeSeries can get the correct information for creating the result for each epoch.
        '''
        # for each epoch we call _getEpochData and check the state of the result and that correct parts of it will be processed in each epoch.   
        results = { 'result': [], 'epochResult': [] }
        # for storing the test results to the actual results file after the test has been executed for each scenario.
        self._results[self._scenarioName] = results
        index = 0 # for indexing expected results.
        while timeSeries._findNextEpoch(): 
            timeSeries._getEpochData()
            # store this epochs state to result for saving to file
            results['result'].append( copy.deepcopy(timeSeries._result) )
            results['epochResult'].append( copy.deepcopy(timeSeries._epochResult) )
            if not self._skipAsserts:
                # check what we got matches expected for this epoch.
                self.assertEqual( timeSeries._result, expected['result'][index] )
                self.assertEqual( timeSeries._epochResult, expected['epochResult'][index] )
            index += 1
    
    @testWithAllScenarios( 'testCreateTimeSeries' )        
    def testCreateTimeSeries(self, timeSeries: timeSeries.TimeSeries, expected: dict ):
        '''
        Test that TimeSeries can create a time series correctly.
        '''
        timeSeries.createTimeSeries()
        # store for saving the actual result to a file.
        self._results[self._scenarioName] = timeSeries._result
        if not self._skipAsserts:
            self.assertEqual( timeSeries._result, expected )
    
    @testWithAllScenarios( 'testCreateCsvHeaders' )        
    def testCreateCsvHeaders(self, timeSeriesObj: timeSeries.TimeSeries, expected: csv.DictReader ):
        '''
        Test that TimeSeriesCsvConverter creates the correct headers for a time series csv result.
        '''
        timeSeriesObj.createTimeSeries()
        csv = timeSeries.TimeSeriesCsvConverter( timeSeriesObj.getResult() )
        csv._createHeaders()
        result = csv.getTarget().getvalue()
        self._results[self._scenarioName] = result
        if not self._skipAsserts:
            testingUtils.checkCsv( self, result, expected )
        
    @testWithAllScenarios( 'testCreateCsv' )        
    def testCreateCsv(self, timeSeriesObj: timeSeries.TimeSeries, expected: csv.DictReader ):
        '''
        Test that TimeSeriesCsvCreator can create correct csv from the result of TimeSeries.
        '''
        timeSeriesObj.createTimeSeries()
        csv = timeSeries.TimeSeriesCsvConverter( timeSeriesObj.getResult() )
        csv.createCsv()
        result = csv.getTarget().getvalue()
        self._results[self._scenarioName] = result
        if not self._skipAsserts:
            testingUtils.checkCsv( self, result, expected )
    
    def getTestData(self, scenario: Dict[str, Any]) -> Tuple[timeSeries.TimeSeries, Any]:
        '''
        Get test data for given scenario for use in test method whose name is in self._testName.
        Returns a TimeSeries created with appropriate parameters from scenario and expected results of scenario.
        Expected results can be None in which case the test is not executed.
        '''
        # create required TimeSeriesMessages objects from scenario parameters.
        tsMsgsLst = [ timeSeries.TimeSeriesMessages( params['attrs'],  self._getMessagesForIds( params['msgIds'] ) ) for params in scenario['timeSeriesParams'] ]
        # TimeSeries requires start time for each epoch so find out which epochs we have messages for
        # and find their start times
        epochs = set()
        for tsMsgs in tsMsgsLst:
            epochs.update( [ msg[messages.epochNumAttr] for msg in tsMsgs.msgs ] )
            
        epochStartTimes = { msg[ messages.epochNumAttr ]: msg[ messages.epochStartAttr ] for msg in self._testData if msg[ messages.topicAttr ] == 'Epoch' and msg[ messages.epochNumAttr ] in epochs }
        
        # get expected results for scenario        
        # expected can be used as is or the actual expected results are read from file.
        expected = scenario.get(self._testName)
        if expected is not None and type( expected ) == dict and 'fileType' in expected:
            fileType = expected['fileType']
            self._fileType = fileType
            if not expected.get( 'noResult' ):
                fileName = testingUtils.getTestDataResultFileName( self._testName, scenario['name'], False, fileType )
                expected = dataManager.readFile( fileName )
                
            else:
                # there are no expected results tests are executed without asserts
                # which means that actual results are just saved to files.
                self._skipAsserts = True
                
        return timeSeries.TimeSeries( tsMsgsLst, epochStartTimes ), expected
    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testGetMessagesForNextEpoch']
    unittest.main()