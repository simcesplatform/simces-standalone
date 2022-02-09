# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
Helper functions used with tests.
'''
import csv
import io
import unittest
from typing import List, Dict

from falcon import testing

from LogReader.app import api
from LogReader.db.simulations import simIdAttr

class ApiTest(testing.TestCase):
    '''
    Super class for api tests which gets the falcon api instance.
    '''

    def setUp(self):
        super(ApiTest, self).setUp()
        self.app = api

def checkSimulations( test: unittest.TestCase, resultSims: List[dict], expectedSims: List[dict]):
    '''
    Check by simulation id that results and expected simulations are the same.
    test: Test case which uses this so we can use its assert methods.
    resultSims: List of simulations.
    expectedSims: List of simulations.
    '''
    checkItemsById( test, simIdAttr, resultSims, expectedSims )
    
def checkMessages( test: unittest.TestCase, resultMsgs: List[dict], expectedMsgs: List[dict] ):
    '''
    Check by message id that the list of result messages matches with the list of expected messages.
    '''
    checkItemsById( test, 'MessageId', resultMsgs, expectedMsgs )
    
def checkItemsById( test: unittest.TestCase, idAttr: str, result: List[dict], expected: List[dict] ):
    '''
    Check by id that results and expected are the same.
    test:  Test case which uses this so we can use its assert methods.
    idAttr: Name of attribute containing the id of the item used in comparison.
    result: List of items.
    expected: List of expected items.
    '''
    # get ids of results and expected and check they contain the same.
    ids = [ item[ idAttr ] for item in result ]
    expectedIds = [ item[ idAttr ] for item in expected ]
    test.assertCountEqual( ids, expectedIds, 'Did not get the expected items.' )

def checkCsv( test: unittest.TestCase, result: str, expected: csv.DictReader, delimiter: str = ';' ):
    '''
    Check that result and expected csv contain the same data.
    '''
    # create a csv DictReader from result string.
    result = io.StringIO( result, newline = '' )
    result = csv.DictReader( result, delimiter = ';' )
    # check that both have the same column titles
    resultHeaders = set( result.fieldnames )
    expectedHeaders = set( expected.fieldnames )
    test.assertEqual( resultHeaders, expectedHeaders, 'Result and expected should have the same headers.' )
    # check the csvs line by line
    line = 1
    for expectedRow in expected:
        line += 1
        try:
            resultRow = next( result )
            
        except StopIteration:
            test.fail( f'No more rows in result but was expecting a row containing: {expectedRow}.' )
            
        test.assertEqual( resultRow, expectedRow, f'Result and expected rows do not match on line {line}.' )
    
    # result should not have more rows    
    with( test.assertRaises( StopIteration, msg = 'Result has more rows than expected.' )):
        next( result )
        
def getTestDataResultFileName( testName: str, scenarioName: str, actual: bool = False, fileType: str = 'json' ) -> str:
    '''
    For time series test get name for a result file for given test and scenario.
    Actual True gives the name of actual results file and False the expected results file.
      fileType should contain the file type extension.
    '''
    result = 'result'
    if actual:
        result = 'actual_result'
        
    # replace spaces in scenario name with underscores
    scenarioName = scenarioName.replace( ' ', '_' )
    return f'{testName}_{scenarioName}_{result}.{fileType}'