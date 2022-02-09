# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>
#            Otto Hylli <otto.hylli@tuni.fi>

"""The initialization module to add the submodules to the python path."""

import os
import sys

SUB_MODULES = [
    "simulation-tools"
]

for sub_module in SUB_MODULES:
    library_path = os.path.realpath(sub_module)
    if library_path not in sys.path:
        sys.path.append(library_path)
