# -*- coding: utf-8 -*
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
Tests for get messages API
'''
import unittest
import json
import os
# disable access logging for tests
os.environ['LOGREADER_ACCESS_LOGGING'] = 'false'


from LogReader.db import messages
from LogReader import utils

from testLogReader import dataManager, testingUtils

# URL path for getting test messages
path = f'/simulations/{dataManager.testMsgSimId}/messages'
invalidPath = path +'/invalid'

class TestMessagesApi( testingUtils.ApiTest ):
    
    @classmethod
    def setUpClass(cls):
        '''
        Adds the test message data to the db
        '''
        cls._testData = dataManager.insertTestMsgData()
        cls._testInvalidData = dataManager.insertTestInvalidMsgData()
        
    @classmethod
    def tearDownClass(cls):
        '''
        Removes the test message data from the db.
        '''
        dataManager.deleteTestMsgData()
        dataManager.deleteTestInvalidMsgData()

    def testGetAllMessages(self):
        '''
        Test we can get all messages.
        '''
        result = self.simulate_get(  path )
        testingUtils.checkMessages( self, result.json, self._testData )
        
    def testGetMessagesSimulationNotFound(self):
        '''
        Check that a 404 response is received when getting messages with simulation id that does not exist.
        ''' 
        result = self.simulate_get( '/simulations/foo/messages' )
        self.assertEqual( result.status_code, 404 )
        
    def testGetMessagesByEpoch(self):
        '''
        Test get messages by epoch number.
        '''
        epoch = 1
        params = { 'epoch':  epoch }
        result = self.simulate_get( path, params  = params )
        self.assertEqual( result.status_code, 200 )
        expected = [ msg for msg in self._testData if msg.get( messages.epochNumAttr ) == epoch ]
        testingUtils.checkMessages( self, result.json, expected )
        
    def testGetMessagesBetweenEpochs(self):
        '''
        Test get messages between given start and end epochs.
        '''
        start = 2
        end = 3
        params = { 'startEpoch': start, 'endEpoch': end }
        result = self.simulate_get( path, params = params )
        expected = [ msg for msg in self._testData if messages.epochNumAttr in msg and msg[messages.epochNumAttr] >= start and msg[messages.epochNumAttr] <= end ]
        testingUtils.checkMessages( self, result.json, expected )
        
    def testGetMessagesByInvalidEpoch(self):
        '''
        Test get bad request error with epoch number not an integer.
        '''
        params = { 'epoch': 'foo' }
        result = self.simulate_get( path, params = params )
        self.assertEqual( result.status_code, 400 )
        
    def testGetMessagesByProcesses(self):
        '''
        Test get messages by multiple source process ids.
        '''
        process = [ 'solarPlant1', 'weatherDivinity' ]
        params = { 'process': ','.join( process ) }
        result = self.simulate_get( path, params = params )
        expected = [ msg for msg in self._testData if msg[ messages.processAttr ] in process ]
        testingUtils.checkMessages( self, result.json, expected )
        
    def testGetOnlyWarningMessages(self):
        '''
        Test get only messages that contain warnings.
        '''
        params = { 'onlyWarnings': 'true' }
        result = self.simulate_get( path, params = params )
        expected = [ msg for msg in self._testData if messages.warningsAttr in msg ]
        testingUtils.checkMessages( self, result.json, expected )
        
    def testGetMessagesInvalidOnlyWarnings(self):
        '''
        Test that invalid onlyWarning is handled correctly.
        '''
        result = self.simulate_get( path, params = { 'onlyWarnings': 'foo' } )
        self.assertEqual( result.status_code, 400 )
        
    def testGetMessagesBetweenSimDate( self ):
        '''
        Get messages between epochs  that contain the given simulation dates.
        '''
        fromSimDate = "2020-06-03T14:00:00Z"
        toSimDate = "2020-06-03T16:00:00Z"
        result = self.simulate_get( path, params = { 'fromSimDate': fromSimDate, 'toSimDate': toSimDate } )
        # we expect messages starting from epoch 2 and ending with epoch 3
        startEpoch = 2
        endEpoch = 3
        expected = [ msg for msg in self._testData if messages.epochNumAttr in msg and msg[messages.epochNumAttr] >= startEpoch and msg[messages.epochNumAttr] <= endEpoch ]
        testingUtils.checkMessages( self, result.json, expected )
        
    def testGetMessagesByTopic(self):
        '''
        Test get messages by topic.
        '''
        topicPattern = 'energy.#'
        # topics we expect the topic pattern to match in test data
        topics = [ 'energy.production.solar', 'energy.storage.state' ]
        result = self.simulate_get( path, params = { 'topic': topicPattern } )
        expected = [ msg for msg in self._testData if msg[messages.topicAttr] in topics ]
        testingUtils.checkMessages( self, result.json, expected )
        
    def testGetMessagesByBetweeenEpochsAndProcessIds(self):
        '''
        Test getting messages with multiple parameters.
        Get messages from given processes send between given epochs. 
        '''
        startEpoch = 2
        endEpoch = 3
        processes = 'weatherDivinity,solarPlant1'
        result = self.simulate_get( path, params = { 'process': processes, 'startEpoch': startEpoch, 'endEpoch': endEpoch }) 
        expected = [ msg for msg in self._testData if msg[messages.processAttr] in processes and msg[messages.epochNumAttr] >= startEpoch and msg[messages.epochNumAttr] <= endEpoch ] 
        testingUtils.checkMessages( self, result.json, expected )
        
    def testGetMessagesByToSimDateAndTopic(self):
        '''
        Test getting messages with multiple parameters.
        Get messages posted to given topics before the given simulation date.
        '''
        toSimDate = "2020-06-03T15:00:00Z" # end of epoch 2
        endEpoch = 2
        topic = 'energy.#'
        expectedTopics = [ 'energy.production.solar', 'energy.storage.state' ]
        result = self.simulate_get( path, params = { 'toSimDate': toSimDate, 'topic': topic }) 
        expected = [ msg for msg in self._testData if msg[messages.topicAttr] in expectedTopics and msg[messages.epochNumAttr] <= endEpoch  ] 
        testingUtils.checkMessages( self, result.json, expected )
        
    def testGetWarningMessagesFromEpoch(self):
        '''
        Test get messages with multiple  parameters.
        Get messages containing warnings from the given epoch.
        '''
        epoch = 3
        result = self.simulate_get( path, params = { 'epoch': 3, 'onlyWarnings': 'true' })
        expected = [ msg for msg in self._testData if messages.warningsAttr in msg and msg[messages.epochNumAttr] == epoch  ] 
        testingUtils.checkMessages( self, result.json, expected )
        
    def testGetAllInvalidMessages(self):
        '''
        Test we can get all invalid messages.
        '''
        result = self.simulate_get(  invalidPath )
        self.assertEqual( result.status_code ,200 )
        # result json has timestamp as string and test data as datetime so test data has to be converted
        expected = json.dumps( self._testInvalidData, default = utils.jsonSerializeDate )
        expected = json.loads( expected )
        self.assertEqual( result.json, expected)
        
    def testGetInvalidMessagesSimulationNotFound(self):
        '''
        Check that a 404 response is received when getting messages with simulation id that does not exist.
        ''' 
        result = self.simulate_get( '/simulations/foo/messages/invalid' )
        self.assertEqual( result.status_code, 404 )
        
    def testGetInvalidMessagesByTopic(self):
        '''
        Test we can get invalid messages by topic.
        '''
        result = self.simulate_get(  invalidPath, params = { 'topic': 'Status.*' } )
        self.assertEqual( result.status_code ,200 )
        expected = json.dumps( [self._testInvalidData[1]], default = utils.jsonSerializeDate )
        expected = json.loads( expected )
        self.assertEqual( result.json, expected)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testGetAllMessages']
    unittest.main()