# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
The main file which sets up the falcon framework based web application.
If this file  is executed as a main file, the application is started with the waitress WSGI server.
The WSGI application is available in LogReader.app.api
'''

import os
from functools import partial
import json
import logging
import pathlib

import markdown
import falcon
from paste.translogger import TransLogger
import waitress

from LogReader.controllers.simulations import SimController
from LogReader.controllers.messages import MsgController
from LogReader.controllers.timeSeries import TimeSeriesController
from LogReader.controllers.static import StaticSite
from LogReader.db import simulations, messages
from LogReader import utils
import LogReader

# log for this module
log = logging.getLogger( __name__ )

def buildApiDoc():
    '''
    Convert the API markdown documentation into a HTML file and  place it in the UI directory.
    '''
    # LogReader root directory
    appDir = pathlib.Path(__file__).parent.parent.absolute()
    # location of the API markdown
    apiMd = str(appDir / 'api.md')
    # location for the HTML API doc
    apiHtml = str(appDir / 'ui/api.html')
    log.info(f'Converting API doc {apiMd} to HTML file {apiHtml}.')
    
    # read the markdown to string
    with open(apiMd, 'r', encoding='utf-8') as file:
        text = file.read()
    
    # a python markdown extension is used to create a table of contents so add the table of contents location mark to the document 
    text = '[TOC]\n' +text
    # convert to html using fenced code extension for showing json and csv marked with ``` correctly 
    html = markdown.markdown( text, extensions = ['fenced_code', 'toc'] )
    # full html for the page where the converted markdown will be put
    template = '''<!DOCTYPE html>
<head>
   <title>LogReader API</title>
   <meta charset="utf-8">
</head>
<body>
<h1>LogReader API</h1>
{}
</body>'''
    html = template.format( html )
    
    # write to file.
    with open(apiHtml, 'w', encoding='utf-8', errors='xmlcharrefreplace') as file:
        file.write(html)

# convert api doc from markdown to html to be served as part of the ui
buildApiDoc()
# configure falcon to automatically convert datetime objects in to JSON when they are a part of the response
# falcon uses the default python json.dumps method which we will still use but with some parameters preset
# namely we give our own function for processing objects (datetime) that the default implementation cannot process
jsonHandler = falcon.media.JSONHandler(
    dumps = partial(
        json.dumps, default = utils.jsonSerializeDate,
        indent = 4, ensure_ascii=False, sort_keys=True
        )
    )

extra_handlers = {
    'application/json': jsonHandler,
}

api = falcon.API()
api.resp_options.media_handlers.update(extra_handlers)

# Add route for getting simulations
# simController is given the module used to get simulations from the db
simController = SimController( simulations )
api.add_route( '/simulations', simController, suffix = 'simulations' )
# add route for getting simulation by id.
api.add_route( '/simulations/{simId}', simController, suffix = 'simulation' )
# Add route for getting messages for simulation
# Give the messages controller the messages db module as the source for messages.
msgController = MsgController( messages )
api.add_route( '/simulations/{simId}/messages', msgController, suffix = 'messages' )
api.add_route( '/simulations/{simId}/messages/invalid', msgController, suffix = 'invalid_messages' )
timeSeriesController = TimeSeriesController( messages )
api.add_route( '/simulations/{simId}/timeseries', timeSeriesController )
# add route for the user interface consisting of static files
staticPrefix = '/' # ui available from the root path
static = StaticSite( staticPrefix ) # use the static controller for delivering the files.
# note works only on one level e.g. /foo/bar.html does not work.
api.add_route( staticPrefix +'{file}', static )
# use Translogger to get logging information about each connection attempt unless it has been disabled with environment variable
if os.environ.get('LOGREADER_ACCESS_LOGGING') != 'false':
    api = TransLogger(api)
   
if __name__ == '__main__':
    # this is main file launch the application
    # get listen ip and port from environment variables or use defaults
    host = os.environ.get( 'LOGREADER_HOST', '*' )
    port = os.environ.get( 'LOGREADER_PORT', 8080 )
    log.info( f'Starting LogReader. Listening on {host}:{port}.' )

    waitress.serve(
        app=api,
        host=host,
        port=port
    )
