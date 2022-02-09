# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Unit test module for the random time series for DummyComponent."""

import unittest

# from dummy.random_series import get_all_random_series, get_latest_values, get_random_initial_values


class TestDummyRandomSeries(unittest.TestCase):
    """Unit tests for the random time series for DummyComponent."""

    def test_one_series(self):
        """Unit test for creating one collection of randomized attributes for a result message."""
        # TODO: implement test_one_series for DummyRandomSeries

    def test_several_series(self):
        """Unit test for creating several collections of randomized attributes for a result message."""
        # TODO: implement test_several_series for DummyRandomSeries


if __name__ == '__main__':
    unittest.main()
