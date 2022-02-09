# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
Code for managing test data i.e. inserting and removing it from the database.
If run as the main file will insert the test data to the db: python -m testLogReader.dataManager
The parameter -d can be used to remove the test data: python -m testLogReader.dataManager -d
'''

import sys
import json
from bson import json_util
import pathlib
from functools import partial
import csv
import io
from typing import Union

from LogReader.db import db, simulations, messages

# the mongodb collection where simulations are stored.
simCollection = db[simulations.simCollection]
# location of json files containing test data.
testDataDir = pathlib.Path(__file__).parent.absolute() / 'data'

# id of simulation for which there are test messages.
testMsgSimId = '2020-06-03T04:01:52.345Z'

def writeFile( fileName: str, data: Union[str, dict] ):
    '''
    Write given data to file with given name in the test data directory.
    Data can be a string containing csv or dict which is converted to json.
    'fileName should have extension json or csv.
    '''
    filePath = testDataDir / fileName
    # get file type extension used to determine how data is saved
    fileType = filePath.suffix[1:]
    with open( filePath, 'w' ) as file:
        if fileType == 'json':
            # we want to be able to automatically convert datetime objects to and from json so they can be compared if needed.
            # so we want that json.dump uses jsonutil.default with specific options to write the file 
            opt = json_util.JSONOptions(strict_number_long=False, datetime_representation=json_util.DatetimeRepresentation.ISO8601, strict_uuid=False, json_mode=0, document_class=dict, tz_aware=True,  unicode_decode_error_handler='strict'  )
            default = partial( json_util.default, json_options = opt ) 
            json.dump( data, file, default = default, indent = 3 )
            
        elif fileType == 'csv':
            file.write( data )

def readFile( fileName: str, csvDelimiter: str = ';' ) -> Union[dict, csv.DictReader]:
    '''
    Read the given file from test data directory.
    If the file extension is json contents are read to a dict.
    If csv they are read into a csv DictReader using the given delimiter.
    '''
    filePath = testDataDir / fileName
    fileType = filePath.suffix[1:]
    fileParams = {} 
    if fileType == 'csv':
        fileParams[ 'newline' ] = ''
         
    with( open( filePath, 'r', **fileParams )) as data:
        if fileType == 'json':
            # json_util is used to parse the mongodb extended JSON data correctly mainly  dates to python datetime objects
            data = json.load(data, object_hook=json_util.object_hook)
            
        elif fileType == 'csv':
            data = io.StringIO( data.read(), newline = '' ) 
            data = csv.DictReader( data, delimiter = csvDelimiter )
        
    return data
    
def insertDataFromFile( fileName: str, collectionName: str ) -> dict:
    '''
    Inserts data from a file from the test data directory whose name is given to the given collection.
    Returns a dict containing the test data.
    '''
    testItems = readFile( fileName )
    # ensure collection is empty before adding data.
    collection = db[collectionName]
    collection.drop()
    collection.insert_many( testItems )
    for item in testItems:
        del item['_id']
        
    return testItems

def insertTestSimData() -> dict:
    '''
    Inserts the test simulation data.
    Returns a dict containing the test data.
    '''
    return insertDataFromFile( 'simulations.json', simulations.simCollection )

def deleteTestSimData():
    '''
    Removes the test simulations from the db by dropping the simulations collection.
    '''
    simCollection.drop()
    
def insertTestMsgData() -> dict:
    '''
    Inserts test messages to db.
    Returns inserted data.
    '''
    return insertDataFromFile( 'messages1.json', messages._getMessageCollectionName( testMsgSimId ))

def deleteTestMsgData():
    '''
    Delete test messages from db.
    '''
    db[messages._getMessageCollectionName( testMsgSimId ) ].drop()

def insertTestInvalidMsgData() -> dict:
    '''
    Inserts invalid test messages to db.
    Returns inserted data.
    '''
    return insertDataFromFile( 'invalid_messages.json', messages._getInvalidMessageCollectionName( testMsgSimId ))

def deleteTestInvalidMsgData():
    '''
    Delete invalid test messages from db.
    '''
    db[messages._getInvalidMessageCollectionName( testMsgSimId ) ].drop()

if __name__ == '__main__':
    # insert or delete the test data
    if len( sys.argv ) < 2:
        insertTestSimData()
        insertTestMsgData()
        insertTestInvalidMsgData()
        print( 'Inserted test simulation and message data.' )
        
    elif sys.argv[1] == '-d':
        deleteTestSimData()
        deleteTestMsgData()
        deleteTestInvalidMsgData()
        print( 'Deleted test simulations and messages from database.' )
        
    else:
        print( 'Usage: without parameters adds test data. With parameter -d removes inserted test data.' )