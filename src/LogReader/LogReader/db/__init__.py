# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
The db pakcage is for interacting with the mongodb database.
This file initialises the database connection.
'''

import os
import logging
import pymongo

log = logging.getLogger( __name__ )
# create the database client used in this application
host = os.environ.get("MONGODB_HOST", "localhost")
port = int(os.environ.get("MONGODB_PORT", 27017))
dbName = os.environ.get("MONGODB_DATABASE", "messages")
authDbName = 'admin' if os.environ.get("MONGODB_ADMIN", 'true' ) == 'true' else dbName
useTls = os.environ.get("MONGODB_TLS", 'false' ) == 'true'
# should not be False if tls is not used since mongo connection raises an exception
invalidCertificates = os.environ.get("MONGODB_TLS_ALLOW_INVALID_CERTIFICATES", 'false' ) == 'true' if useTls else True
log.info( f'Establishing connection to MongoDB. host: {host}, port: {port}, database: {dbName}, authentication database: {authDbName}, use tls: {useTls}, allow invalid certificates: {invalidCertificates}.' )
client = pymongo.MongoClient( 
    host = host,
    port = port,
    tz_aware = True, # Returns datetime objects that are timezone aware.
    username = os.environ.get("MONGODB_USERNAME", None ),
    password = os.environ.get("MONGODB_PASSWORD", None ),
    authSource = authDbName,
    tls = useTls,
    tlsAllowInvalidCertificates = invalidCertificates,
    appname = 'LogReader' ) # app name should be visible in some mongodb logs
# the database containing the messages and simulation information
db = client[ dbName ]