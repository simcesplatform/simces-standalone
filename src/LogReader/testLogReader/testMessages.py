# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
Tests for getting messages from the database.
'''

import unittest
from builtins import classmethod

import dateutil

from testLogReader import dataManager, testingUtils
from LogReader.db import messages

class TestMessages(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # insert test data before tests are executed
        cls._testData = dataManager.insertTestMsgData()
        cls._testInvalidData = dataManager.insertTestInvalidMsgData()
    
    @classmethod
    def tearDownClass(cls):
        # after tests are executed delete test messages
        dataManager.deleteTestMsgData()
        dataManager.deleteTestInvalidMsgData()

    def setUp(self):
        pass


    def tearDown(self):
        pass

    def testGetAllMessages(self):
        '''
        Test that we can get all messages.
        '''
        result = messages.getMessages( dataManager.testMsgSimId )
        testingUtils.checkMessages( self, result, self._testData )
        
    def testGetMessagesSimulationNotFound(self):
        '''
        Test that we get None with id of a simulation that does not exist.
        '''
        result = messages.getMessages( 'foo' )
        self.assertIsNone( result )
        
    def testGetMessagesByEpoch(self):
        '''
        Test get messages by epoch number.
        '''
        epoch = 1
        result = messages.getMessages( dataManager.testMsgSimId, epoch = epoch )
        expected = [ msg for msg in self._testData if msg.get( messages.epochNumAttr ) == epoch ]
        testingUtils.checkMessages( self, result, expected )
        
    def testGetMessagesByStartEpoch(self):
        '''
        test get messages starting from given epoch.
        '''
        startEpoch = 2
        result = messages.getMessages( dataManager.testMsgSimId, startEpoch = startEpoch )
        expected = [ msg for msg in self._testData if messages.epochNumAttr in msg and msg[messages.epochNumAttr] >= startEpoch ]
        testingUtils.checkMessages( self, result, expected )
        
    def testGetMessagesByEndEpoch(self):
        '''
        test get messages ending at given epoch.
        '''
        endEpoch = 2
        result = messages.getMessages( dataManager.testMsgSimId, endEpoch = endEpoch )
        expected = [ msg for msg in self._testData if messages.epochNumAttr in msg and msg[messages.epochNumAttr] <= endEpoch ]
        testingUtils.checkMessages( self, result, expected )
        
    def testGetMessagesBetweenEpochs(self):
        '''
        test get messages between given epochs
        '''
        startEpoch = 2
        endEpoch = 3
        result = messages.getMessages( dataManager.testMsgSimId, startEpoch = startEpoch, endEpoch = endEpoch )
        expected = [ msg for msg in self._testData if messages.epochNumAttr in msg and msg[messages.epochNumAttr] >= startEpoch and msg[messages.epochNumAttr] <= endEpoch ]
        testingUtils.checkMessages( self, result, expected )
    
    def testGetMessagesByProcess(self):
        '''
        Test get messages by source process id.
        '''
        process = [ 'solarPlant1' ]
        result = messages.getMessages( dataManager.testMsgSimId, process = process )
        expected = [ msg for msg in self._testData if msg[ messages.processAttr ] in process ]
        testingUtils.checkMessages( self, result, expected )
        
    def testGetMessagesByProcesses(self):
        '''
        Test get messages by multiple source process ids.
        '''
        process = [ 'solarPlant1', 'weatherDivinity' ]
        result = messages.getMessages( dataManager.testMsgSimId, process = process )
        expected = [ msg for msg in self._testData if msg[ messages.processAttr ] in process ]
        testingUtils.checkMessages( self, result, expected )
        
    def testGetOnlyWarningMessages(self):
        '''
        Test get only messages that contain warnings.
        '''
        result = messages.getMessages( dataManager.testMsgSimId, onlyWarnings = True )
        expected = [ msg for msg in self._testData if messages.warningsAttr in msg ]
        testingUtils.checkMessages( self, result, expected )        
        
    def testGetEpochsForSimDates(self):
        '''
        Test the _getEpochForsimDates helper method used when getting messages by simulation dates.
        '''
        fromSimDate = dateutil.parser.isoparse( "2020-06-03T14:00:00Z" ) # start of epoch 2
        toSimDate = dateutil.parser.isoparse( "2020-06-03T16:00:00Z" ) # end of epoch 3
        result = messages._getEpochsForSimDates( dataManager.testMsgSimId, fromSimDate = fromSimDate )
        self.assertEqual( result, ( 2, None ))
        result = messages._getEpochsForSimDates( dataManager.testMsgSimId, toSimDate = toSimDate )
        self.assertEqual( result, ( None, 3 ))
        result = messages._getEpochsForSimDates( dataManager.testMsgSimId, fromSimDate = fromSimDate, toSimDate = toSimDate )
        self.assertEqual( result, ( 2, 3 ))
        fromSimDate = dateutil.parser.isoparse( "2020-06-03T17:00:00Z" ) #  end of last epoch, no epochs
        toSimDate = dateutil.parser.isoparse( "2020-06-03T13:00:00Z" ) # Start of first epoch, should not get any epochs 
        result = messages._getEpochsForSimDates( dataManager.testMsgSimId, fromSimDate = fromSimDate )
        self.assertEqual( result, ( None, None ))
        result = messages._getEpochsForSimDates( dataManager.testMsgSimId, toSimDate = toSimDate )
        self.assertEqual( result, ( None, None ))
        
    def testGetMessagesByFromSimDate( self ):
        '''
        Get messages on and after epoch which includes the given simulation date.
        '''
        fromSimDate = dateutil.parser.isoparse( "2020-06-03T14:00:00Z" )
        result = messages.getMessages( dataManager.testMsgSimId, fromSimDate = fromSimDate )
        # we expect messages starting from epoch 2
        startEpoch = 2
        expected = [ msg for msg in self._testData if messages.epochNumAttr in msg and msg[messages.epochNumAttr] >= startEpoch ]
        testingUtils.checkMessages( self, result, expected )
        
    def testGetMessagesByToSimDate( self ):
        '''
        Get messages on and before epoch which includes the given simulation date.
        '''
        toSimDate = dateutil.parser.isoparse( "2020-06-03T15:00:00Z" )
        result = messages.getMessages( dataManager.testMsgSimId, toSimDate = toSimDate )
        # we expect messages ending with   epoch 2
        endEpoch = 2
        expected = [ msg for msg in self._testData if messages.epochNumAttr in msg and msg[messages.epochNumAttr] <= endEpoch ]
        testingUtils.checkMessages( self, result, expected )
        
    def testGetMessagesBetweenSimDate( self ):
        '''
        Get messages between epochs  that contain the given simulation dates.
        '''
        fromSimDate = dateutil.parser.isoparse( "2020-06-03T14:00:00Z" )
        toSimDate = dateutil.parser.isoparse( "2020-06-03T16:00:00Z" )
        result = messages.getMessages( dataManager.testMsgSimId, fromSimDate = fromSimDate, toSimDate = toSimDate )
        # we expect messages starting from epoch 2 and ending with epoch 3
        startEpoch = 2
        endEpoch = 3
        expected = [ msg for msg in self._testData if messages.epochNumAttr in msg and msg[messages.epochNumAttr] >= startEpoch and msg[messages.epochNumAttr] <= endEpoch ]
        testingUtils.checkMessages( self, result, expected )
        
    def testGetMessagesByTopic(self):
        '''
        Test get messages by various topic patterns which use wild card characters.
        '''
        # key topic pattern, value list of topics it should match from the test messages.
        topics = {
            'Epoch': [ 'Epoch' ],
            'weather.*': [ 'weather.current', 'weather.forecast' ],
            '*.current': [ 'weather.current' ],
            'energy.*.solar': [ 'energy.production.solar' ],
            '*.production.*': [ 'energy.production.solar' ],
            'energy.*': [],
            'energy.#': [ 'energy.production.solar', 'energy.storage.state' ],
            '#.solar': [ 'energy.production.solar' ]
        }
        
        for topic in topics:
            with self.subTest( topic = topic ):
                result = messages.getMessages( dataManager.testMsgSimId, topic = topic )
                expected = [ msg for msg in self._testData if msg[messages.topicAttr] in topics[topic] ]
                testingUtils.checkMessages( self, result, expected )
                
    def testGetMessagesByBetweeenEpochsAndProcessIds(self):
        '''
        Test getting messages with multiple parameters.
        Get messages from given processes send between given epochs. 
        '''
        startEpoch = 2
        endEpoch = 3
        processes = [ 'weatherDivinity', 'solarPlant1' ]
        result = messages.getMessages( dataManager.testMsgSimId, startEpoch = startEpoch, endEpoch = endEpoch, process = processes )
        expected = [ msg for msg in self._testData if msg[messages.processAttr] in processes and msg[messages.epochNumAttr] >= startEpoch and msg[messages.epochNumAttr] <= endEpoch ] 
        testingUtils.checkMessages( self, result, expected )
        
    def testGetMessagesByToSimDateAndTopic(self):
        '''
        Test getting messages with multiple parameters.
        Get messages posted to given topics before the given simulation date.
        '''
        toSimDate = dateutil.parser.isoparse( "2020-06-03T15:00:00Z" ) # end of epoch 2
        endEpoch = 2
        topic = 'energy.#'
        expectedTopics = [ 'energy.production.solar', 'energy.storage.state' ]
        result = messages.getMessages( dataManager.testMsgSimId, toSimDate = toSimDate, topic = topic )
        expected = [ msg for msg in self._testData if msg[messages.topicAttr] in expectedTopics and msg[messages.epochNumAttr] <= endEpoch  ] 
        testingUtils.checkMessages( self, result, expected )
        
    def testGetWarningMessagesFromEpoch(self):
        '''
        Test get messages with multiple  parameters.
        Get messages containing warnings from the given epoch.
        '''
        epoch = 3
        result = messages.getMessages( dataManager.testMsgSimId, epoch = epoch, onlyWarnings = True )
        expected = [ msg for msg in self._testData if messages.warningsAttr in msg and msg[messages.epochNumAttr] == epoch  ] 
        testingUtils.checkMessages( self, result, expected )
        
    def testGetInvalidMessagesSimulationNotFound(self):
        '''
        Test that we get None with id of a simulation that does not exist.
        '''
        result = messages.getInvalidMessages( 'foo' )
        self.assertIsNone( result )
        
    def testGetInvalidMessages(self):
        '''
        Test that we can get all invalid messages for a simulation.
        '''
        result = messages.getInvalidMessages(dataManager.testMsgSimId)
        self.assertEqual( result, self._testInvalidData )
        
    def testGetInvalidMessagesByTopic(self):
        '''
        Test that we can get invalid messages by topic.
        '''
        result = messages.getInvalidMessages(dataManager.testMsgSimId, 'Status.*')
        self.assertEqual( result, [self._testInvalidData[1]])
     
if __name__ == "__main__":
    unittest.main()