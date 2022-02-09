# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Unit tests for the simulation manager module."""

import unittest

# from manager.manager import SimulationManager


class TestSimulationManager(unittest.TestCase):
    """Unit tests for the SimulationManager class."""

    def test_creation(self):
        """Unit test for creating SimulationManager object."""
        # TODO: implement test_creation for SimulationManager

    def test_start(self):
        """Unit test for the handling of simulation start for SimulationManager."""
        # TODO: implement test_start for SimulationManager

    def test_epoch(self):
        """Unit test for the handling of starting a new epoch with simulation manager."""
        # TODO: implement test_epoch for SimulationManager

    def test_epoch_resends(self):
        """Unit test for the handling of resending epoch messages when necessary with simulation manager."""
        # TODO: implement test_epoch_resends for SimulationManager

    def test_stop(self):
        """Unit test for the handling of simulation end for SimulationManager."""
        # TODO: implement test_stop for SimulationManager


if __name__ == '__main__':
    unittest.main()
