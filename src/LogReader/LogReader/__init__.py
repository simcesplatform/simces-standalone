# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi> and Ville Heikkilä <ville.heikkila@tuni.fi>
'''
Initialises logging for the application.
'''

import logging
import os

level = logging.INFO
if os.environ.get( 'LOGREADER_DEBUG' ) == 'true':
    level = logging.DEBUG
    
logging.basicConfig( level = level )
# pakcage logger for possible package level logging configuration
log = logging.getLogger( __name__ )
log.debug( 'Debug logging is on.' )