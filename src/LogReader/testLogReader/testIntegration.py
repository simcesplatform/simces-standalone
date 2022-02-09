# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
Some tests for the application when it is run with a real WSGI server.
'''
import os
import unittest
import threading

import waitress
import requests

# disable access logging for tests
os.environ['LOGREADER_ACCESS_LOGGING'] = 'false'

from testLogReader import dataManager, testingUtils
from LogReader.app import api
from LogReader.db.simulations import simIdAttr
from LogReader.db import messages

class ServerThread(threading.Thread):
    '''
    A Thread subclass for launching the application with waitress.
    Inspired by https://gist.githubusercontent.com/miohtama/1f716f0d6aa2a9d05406/raw/65ef485d134ae1c3f320675ab485c51c2c4e1843/webserver.py
    '''
    
    def __init__(self, app, port ):
        '''
        Initialise with the WSGI app to be run with waitress and the TCP port number to be used.
        '''
        threading.Thread.__init__(self)
        self._app = app
        self._port = port
        # mark as daemon so that when the tests are done in main thread this thread is terminated
        # there is no other way to tell waitress to stop.
        self.daemon = True
        
    def run(self):
        '''
        Launch the app with waitress.
        '''
        try:
            waitress.serve(self._app, host='127.0.0.1', port=self._port, log_socket_errors=False, clear_untrusted_proxy_headers = True, _quiet=True)
            
        except Exception as e:
            # We are a background thread so we have problems to interrupt tests in the case of error. Try spit out something to the console.
            import traceback
            traceback.print_exc()
            
class TestWebServer(unittest.TestCase):
    '''
    Tests for the running server.
    '''
    
    @classmethod
    def setUpClass(cls):
        '''
        Launch the server and insert test data.
        '''
        cls._port = os.environ.get( 'LOGREADER_PORT', 8080 ) 
        cls._server = ServerThread( api, cls._port )
        cls._server.start() 
        cls._testSimData = dataManager.insertTestSimData()
        cls._testMsgData = dataManager.insertTestMsgData()
        cls._baseURL = f'http://localhost:{cls._port}'
        # test that server is up
        retries = 10 # try retries times to make a test request
        success = False 
        while not success:
            try:
                requests.get( cls._baseURL)
                
            except requests.exceptions.ConnectionError as e:
                if retries == 0:
                    raise e
                
                retries -= 1
                continue
                
            success = True

    @classmethod
    def tearDownClass(cls):
        '''
        Remove test data when tests done.
        '''
        dataManager.deleteTestSimData() 
        dataManager.deleteTestMsgData()
        
    def testGetSimulations(self):
        '''
        Test get all simulations.
        '''
        result = requests.get( self._baseURL +'/simulations' )
        self.assertEqual( result.status_code, 200, 'Incorrect response status.' )
        testingUtils.checkSimulations(self, result.json(), self._testSimData )
        
    def testGetSimulationsBetweenDates(self):
        '''
        Test get simulations executed between given dates.
        '''
        params = { 'fromDate': '2020-06-03T09:01:52.345Z',
                  'toDate': '2020-06-03T11:01:52.345Z'
               }
        result = requests.get( self._baseURL +'/simulations', params = params )
        self.assertEqual( result.status_code, 200 )
        # we should get only the second simulation.
        testingUtils.checkSimulations(self, result.json(), self._testSimData[1:2] )
        
    def testGetSimulationById(self):
        '''
        Test get simulation by id.
        '''
        simId = self._testSimData[0][simIdAttr]
        result = requests.get( self._baseURL +'/simulations/' +simId )
        self.assertEqual( result.status_code, 200 )
        self.assertEqual( result.json()[simIdAttr], simId )
    
    def testGetAllMessages(self):
        '''
        Test get all messages.
        '''
        result = requests.get( f'{self._baseURL}/simulations/{dataManager.testMsgSimId}/messages' )
        self.assertEqual( result.status_code, 200 )
        testingUtils.checkMessages( self, result.json(), self._testMsgData )
        
    def testGetWarningMessagesBetweenSimDatesByTopic(self):
        '''
        Test get messages with multiple parameters.
        Get warning messages between given simulation dates from the given topic.
        '''
        fromSimDate = "2020-06-03T14:00:00Z"
        toSimDate = "2020-06-03T16:00:00Z"
        topic = 'energy.#'
        expectedTopics = [ 'energy.production.solar' ]
        result = requests.get( f'{self._baseURL}/simulations/{dataManager.testMsgSimId}/messages', params = { 'fromSimDate': fromSimDate, 'toSimDate': toSimDate, 'topic': topic, 'onlyWarnings': 'true' } )
        # we expect messages starting from epoch 2 and ending with epoch 3
        startEpoch = 2
        endEpoch = 3
        expected = [ msg for msg in self._testMsgData if messages.epochNumAttr in msg and msg[messages.epochNumAttr] >= startEpoch and msg[messages.epochNumAttr] <= endEpoch and msg[messages.topicAttr] in expectedTopics and messages.warningsAttr in msg ]
        self.assertEqual( result.status_code, 200 )
        testingUtils.checkMessages( self, result.json(), expected )
        
    def testGetTimeSeriesCsvForEpoch(self):
        '''
        Test get time series.
        ''' 
        result = requests.get( f'{self._baseURL}/simulations/{dataManager.testMsgSimId}/timeseries', params = { 'epoch': 2, 'attrs': 'batteryState.chargePercentage,batteryState.capacity', 'topic': 'energy.storage.state', 'format': 'csv' } )
        self.assertEqual( result.status_code, 200 )
        # save actual results to file
        testName = 'testGetTimeSeriesCsvForEpoch'
        actualName = testingUtils.getTestDataResultFileName( testName, '', True, 'csv' )
        dataManager.writeFile( actualName, result.text )
        # read expected results from file and compare to actual results.
        expectedName = testingUtils.getTestDataResultFileName(testName, '', False, 'csv' )
        expected = dataManager.readFile( expectedName )
        testingUtils.checkCsv( self, result.text, expected )
        
    def testGetUi(self):
        '''
        Check that we can get user interface files.
        '''
        # file path in url and expected content type
        filesAndTypes = {
            '': 'text/html',
            '/api.html': 'text/html',
            '/main.js': 'application/javascript',
            '/style.css': 'text/css'
        }
        
        for file, contentType in filesAndTypes.items():
            with self.subTest( file = file ):
                resp = requests.get( f'{self._baseURL}{file}' )
                self.assertEqual( resp.status_code, 200 )
                self.assertEqual( resp.headers['content-type'], contentType )

if __name__ == "__main__":
    # execute tests
    unittest.main()