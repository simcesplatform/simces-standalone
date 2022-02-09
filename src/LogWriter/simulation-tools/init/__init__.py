# -*- coding: utf-8 -*-

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
