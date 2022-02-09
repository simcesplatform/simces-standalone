# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
Tests for simulation api endpoints.
Uses falcons testing tools which simulate HTTP requests. 
'''
import unittest
import os 

# disable access logging for tests
os.environ['LOGREADER_ACCESS_LOGGING'] = 'false'

from testLogReader import dataManager, testingUtils
from LogReader.db.simulations import simIdAttr

class TestSimApi( testingUtils.ApiTest ):
    '''
    The simulation API tests.
    '''
    
    @classmethod
    def setUpClass(cls):
        '''
        Insert simulation test data before the tests are executed.
        '''
        # store test data for use in tests
        cls._testData = dataManager.insertTestSimData()
        
    @classmethod
    def tearDownClass(cls):
        '''
        Remove test data after tests are complete.
        '''
        dataManager.deleteTestSimData()
    
    def testGetAll(self):
        '''
        Test get all simulations.
        '''
        result = self.simulate_get( '/simulations' )
        testingUtils.checkSimulations(self, result.json, self._testData )
        
    def testGetSimulationsAfterDate(self):
        '''
        Test get simulations after given date.
        '''
        params = { 'fromDate': '2020-06-03T10:01:52.345Z' }
        result = self.simulate_get( '/simulations', params = params )
        self.assertEqual( result.status_code, 200 )
        # we should haven gotten the latter two simulations.
        testingUtils.checkSimulations(self, result.json, self._testData[1:] )
        
    def testGetSimulationsBeforeDate(self):
        '''
        Test get simulations started before given date.
        '''
        params = { 'toDate': '2020-06-03T10:01:52.345Z' }
        result = self.simulate_get( '/simulations', params = params )
        self.assertEqual( result.status_code, 200 )
        # we should get the first simulation
        testingUtils.checkSimulations(self, result.json, self._testData[:1] )
        
    def testGetSimulationsBetweenDates(self):
        '''
        Test get simulations executed between given dates.
        '''
        params = { 'fromDate': '2020-06-03T09:01:52.345Z',
                  'toDate': '2020-06-03T11:01:52.345Z'
               }
        result = self.simulate_get( '/simulations', params = params )
        self.assertEqual( result.status_code, 200 )
        # we should get only the second simulation.
        testingUtils.checkSimulations(self, result.json, self._testData[1:2] )
        
    def testGetSimulationsWithBadDate(self):
        '''
        Check that we get a HTTP bad request response with an invalid date.
        '''
        params = { 'toDate': '2020-06-0310:01:52.345Z' }
        result = self.simulate_get( '/simulations', params = params )
        self.assertEqual( result.status_code, 400 )
    
    def testGetSimulationById(self):
        '''
        Test get simulation by SimulationId.
        '''
        simId = self._testData[1][simIdAttr]
        result = self.simulate_get( f'/simulations/{simId}' )
        self.assertEqual( result.status_code, 200 )
        self.assertIsNotNone( result.json )
        self.assertIn( simIdAttr, result.json )
        self.assertEqual( result.json[ simIdAttr ], simId )
        
    def testGetSimulationByIdNotFound(self):
        '''
        Test proper response when simulation not found.
        '''
        result = self.simulate_get( '/simulations/foo' )
        self.assertEqual( result.status_code, 404 )

if __name__ == "__main__":
    # execute tests if main file.
    unittest.main()