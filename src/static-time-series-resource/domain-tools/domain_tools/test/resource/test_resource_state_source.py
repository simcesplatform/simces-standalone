# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>
#            Otto Hylli <otto.hylli@tuni.fi>
#            Kalle Ruuth <kalle.ruuth@tuni.fi>

'''
Tests for the state_source module.
'''

import unittest
import pathlib

from domain_tools.resource.resource_state_source import (
    ResourceState, CsvFileResourceStateSource, CsvFileError, NoDataAvailableForEpoch)


def getFilePath(fileName: str) -> pathlib.Path:
    '''
    Get full path to test data files located in  the same directory as this file.
    '''
    return pathlib.Path(__file__).parent.absolute() / fileName


class TestDataSource(unittest.TestCase):
    '''
    Tests for the csv resource state source.
    '''

    def testReadData(self):
        '''
        Test that csv is read correctly and converted correctly to ResourceState objects.
        '''
        # test with different files: define file name and ResourceStates expected to be created from it
        scenarios = [
            {
                'file': 'load1.csv',
                'expected': [
                    ResourceState(real_power=-10, reactive_power=-1, customerid='GridA-1', node=None),
                    ResourceState(real_power=-11.5, reactive_power=-2.0, customerid='GridA-1', node=1),
                    ResourceState(real_power=-9.1, reactive_power=0, customerid='GridA-1', node=2)
                ]
            },
            # contains an Epoch field which is not used but should be allowed for human convenience
            {
                'file': 'generator1.csv',
                'expected': [
                    ResourceState(real_power=4.5, reactive_power=0.5, customerid='GridA-1'),
                    ResourceState(real_power=7.5, reactive_power=1.0, customerid='GridA-1')
                ]
            }
        ]

        for scenario in scenarios:
            fileName = scenario['file']
            expected = scenario['expected']
            with self.subTest(file=fileName):
                stateSource = CsvFileResourceStateSource(getFilePath(fileName))
                result = []
                for _ in range(0, len(expected)):
                    result.append(stateSource.getNextEpochData())

                self.assertEqual(result, expected)

    def testMissingColumns(self):
        '''
        Check that missing RealPower, ReactivePower or CustomerId columns causes an exception.
        '''
        # each file has a different missing column
        files = ['invalid_fields1.csv', 'invalid_fields2.csv', 'invalid_fields3.csv']
        for file in files:
            with self.subTest(file=file):
                with self.assertRaises(CsvFileError) as cm:
                    CsvFileResourceStateSource(getFilePath(file))

                # check that exception message is the correct one.
                self.assertTrue(
                    str(cm.exception).startswith('Resource state source csv file missing required columns:'),
                    f'Exception message was {str(cm.exception)}.'
                )

    def testUnableToreadFile(self):
        '''
        Test that file not found raises the correct exception.
        '''
        with self.assertRaises(CsvFileError) as cm:
            CsvFileResourceStateSource('foo.csv')

        message = str(cm.exception)
        self.assertTrue(message.startswith('Unable to read file'), f'Exception message was {message}.')

    def test_invalid_values_and_no_more_data(self):
        '''
        Test that invalid values in csv cause an exception and when there are no more rows the correct exception is raised.
        '''
        stateSource = CsvFileResourceStateSource(getFilePath('invalid_values.csv'))
        # each row has an invalid value for an attribute in the following order
        invalidAttrs = ['RealPower', 'ReactivePower', 'Node']
        for attr in invalidAttrs:
            with self.assertRaises(ValueError, msg=f'{attr} should have an invalid value.') as cm:
                stateSource.getNextEpochData()

            message = str(cm.exception)
            self.assertIn(attr, message, 'Should contain the name of the invalid attribute.')

        with self.assertRaises(NoDataAvailableForEpoch):
            stateSource.getNextEpochData()


if __name__ == "__main__":
    unittest.main()
