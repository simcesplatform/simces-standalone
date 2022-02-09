# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
Tests for the simulations db module.
'''
import unittest
from datetime import timedelta  
from LogReader.db.simulations import getSimulations, getSimulationById, simIdAttr, endTimeAttr, startTimeAttr
from testLogReader import dataManager
from testLogReader.testingUtils import checkSimulations

class SimTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        '''
        Insert test data before the test methods are executed.
        '''
        # save test data for use in the tests.
        cls._testData = dataManager.insertTestSimData()
    
    @classmethod
    def tearDownClass(cls):
        '''
        Removes test data after tests have been executed.
        '''
        dataManager.deleteTestSimData()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testGetAllSimulations(self):
        '''
        Test that all simulations can be fetched correctly.
        '''
        results = getSimulations()
        # check that results match what was expected.
        checkSimulations( self, results, self._testData )
    
    def testGetSimulationsAfterDate(self):
        '''
        Test getting by start date.
        '''
        # start time is the start time of second test simulation.
        start = self._testData[1][startTimeAttr]
        result = getSimulations( start )
        # results should not include the first simulation
        checkSimulations( self, result, self._testData[1:] )
        
    def testGetSimulationsBeforeDate(self):
        '''
        Get by end date.
        '''
        # end is the start time of second simulation.
        end = self._testData[1][startTimeAttr]
        result = getSimulations( end = end )
        # should only include first simulation
        checkSimulations( self, result, self._testData[:1] ) 
        
    def testGetSimulationsBetweenDates(self):
        '''
        Get by start and end.
        '''
        # we want the second simulation so query hour before last simulation start and hour after first simulation start   
        hour = timedelta( hours = 1 )
        start = self._testData[0][startTimeAttr] +hour
        end = self._testData[2][startTimeAttr] -hour
        result = getSimulations( start, end )
        checkSimulations( self, result, self._testData[1:2] ) 
        
    def testGetSimulationById(self):
        '''
        Test get simulation by id from db.
        '''
        simId = self._testData[2][simIdAttr]
        result = getSimulationById( simId )
        self.assertIn( simIdAttr, result )
        self.assertEqual( result[simIdAttr], simId )
        
    def testGetSimulationNotFound(self):
        '''
        Check that we get None if there is no simulation with given id.
        '''
        result = getSimulationById( 'foo'  )
        self.assertIsNone( result )
 
if __name__ == "__main__":
    # if main file execute tests
    unittest.main()