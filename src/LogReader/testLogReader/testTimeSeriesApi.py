# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
Tests for the time series api.
'''
import unittest
import os 
# disable access logging for tests
os.environ['LOGREADER_ACCESS_LOGGING'] = 'false'

from testLogReader import dataManager, testingUtils

# url path for creating time series from test messages.
path = f'/simulations/{dataManager.testMsgSimId}/timeseries'

# specify test scenarios for the time series api
# for each scenario time series is fetched with query parameters from the scenario 
# and checked against expected results read from file. 
scenarios = [
    # scenario name is used to identify scenario result files.
    { 'name': 'battery state for battery 1',
     # define HTTP request query parameters used to get the time series.
     'query': { 'attrs': 'batteryState',
               'process': 'battery1', 
               'topic': 'energy.storage.state' },
     # define expected HTTP status code
     'status': 200 },
    { 'name': 'real power for solar plant 1',
     'query': { 'attrs': 'RealPower',
               'process': 'solarPlant1', 
               'topic': 'energy.production.solar' },
     'status': 200 },
    { 'name': 'real and reactive power for solar plant 1',
     'query': { 'attrs': 'RealPower,ReactivePower',
               'process': 'solarPlant1', 
               'topic': 'energy.production.solar' },
     'status': 200 },
    { 'name': 'missing attrs parameter',
     'query': { 
               'process': 'battery1', 
               'topic': 'energy.storage.state' },
     'status': 400 },
    { 'name': 'battery charge for battery 1',
     'query': { 'attrs': 'batteryState.chargePercentage',
               'process': 'battery1', 
               'topic': 'energy.storage.state' },
     'status': 200 },
    { 'name': 'battery state for battery 1 and 2',
     'query': { 'attrs': 'batteryState',
               'process': 'battery1,battery2', 
               'topic': 'energy.storage.state' },
     'status': 200 },
    { 'name': 'battery state for battery 1 with start epoch',
     'query': { 'attrs': 'batteryState',
               'startEpoch': '2',
               'process': 'battery1', 
               'topic': 'energy.storage.state' },
     'status': 200 },
    { 'name': 'battery state for battery 1 with end epoch',
     'query': { 'attrs': 'batteryState',
               'endEpoch': '1',
               'process': 'battery1', 
               'topic': 'energy.storage.state' },
     'status': 200 },
    { 'name': 'battery state for battery 1 with epoch',
     'query': { 'attrs': 'batteryState',
               'epoch': '2',
               'process': 'battery1', 
               'topic': 'energy.storage.state' },
     'status': 200 },
    { 'name': 'battery state for battery 1 with from simdate',
     'query': { 'attrs': 'batteryState',
               'fromSimDate': '2020-06-03T14:00:00Z',
               'process': 'battery1', 
               'topic': 'energy.storage.state' },
     'status': 200 },
    { 'name': 'battery state for battery 1 with to simdate',
     'query': { 'attrs': 'batteryState',
               'toSimDate': '2020-06-03T14:00:00Z',
               'process': 'battery1', 
               'topic': 'energy.storage.state' },
     'status': 200 },
    { 'name': 'no messages',
     'query': { 'attrs': 'batteryState',
               'epoch': '3',
               'process': 'battery1', 
               'topic': 'energy.storage.state' },
     'status': 200 }
    ]

class TestTimeSeriesApi( testingUtils.ApiTest ):
    '''
    Tests for time series API.
    '''
    
    @classmethod
    def setUpClass(cls):
        '''
        Adds the test message data to the db
        '''
        cls._testData = dataManager.insertTestMsgData()
        
    @classmethod
    def tearDownClass(cls):
        '''
        Removes the test message data from the db.
        '''
        dataManager.deleteTestMsgData()
        
    def testApiWithScenarios(self):
        '''
        Test getting time series from the API with different test scenarios which have different query parameters and expected results.
        Each scenario is tested for both json and csv formats
        Actual results for each scenario are saved to a file and compared to expected results read from file.
        '''
        for scenario in scenarios:
            for dataFormat in [ 'json', 'csv' ]:
                with self.subTest( scenario = scenario['name' ], format = dataFormat ):
                    self._checkScenario( scenario, dataFormat )
                    
    def _checkScenario(self, scenario: dict, dataFormat: str ):
        '''
        Check given scenario with the given data format json or csv.
        Actual results are saved to a file and compared to expected results read from file.
        '''
        # copy original scenario query parameters since they would otherwise be modified
        params = dict( scenario['query'] )
        params['format'] = dataFormat
        result = self.simulate_get( path, params = params )
        self.assertEqual( result.status_code, scenario['status'], 'Did not get the expected HTTP status code.' )
        if result.status_code != 200 or scenario['status'] != 200:
            # no need to check response body
            return
        
        # save the actual results we got to a file
        testName = 'testTimeSeriesApi'
        actualResultName = testingUtils.getTestDataResultFileName( testName, scenario['name'], True, dataFormat )
        if dataFormat == 'json':
            resultData = result.json
            
        elif dataFormat == 'csv':
            resultData = result.text
            
        dataManager.writeFile( actualResultName, resultData )
        
        # read expected results from file
        resultName = testingUtils.getTestDataResultFileName( testName, scenario['name'], False, dataFormat )
        expected = dataManager.readFile( resultName )
        # compare actual result and expected
        if dataFormat == 'json':
            self.assertEqual( resultData, expected )
            
        elif dataFormat == 'csv':
            testingUtils.checkCsv( self, resultData, expected )
            
    def testSimulationNotFound(self):
        '''
        Test that we get correct HTTP status when trying to get time series for simulation which does not exist.
        '''
        result = self.simulate_get( '/simulations/foo/timeseries', params = { 'attrs': 'batteryState', 'topic': 'energy.storage.state' })
        self.assertEqual( result.status_code, 404, 'Got unexpected status code.' )
        
if __name__ == "__main__":
    unittest.main()