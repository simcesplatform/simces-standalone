# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Unit test for the components module."""

import unittest

from manager.components import SimulationComponents

NO_MESSAGES = -1


class TestSimulationComponents(unittest.TestCase):
    """Unit tests for the SimulationComponents class."""

    def test_new_class(self):
        """Unit test for an empty component list."""
        self.assertEqual(SimulationComponents.NO_MESSAGES, NO_MESSAGES)

        components = SimulationComponents()
        self.assertEqual(components.get_component_list(), [])
        self.assertEqual(components.get_latest_full_epoch(), NO_MESSAGES)
        self.assertEqual(str(components), "")
        self.assertEqual(components.get_latest_epoch_for_component("test"), None)

    def test_add_and_remove_components(self):
        """Tests adding new components."""
        new_component_names = ["dummy", "generator", "extra", "planner", "logger"]
        removed_component_names = ["dummy", "extra", "logger"]
        remaining_component_names = ["generator", "planner"]

        # add new components
        components = SimulationComponents()
        for component_name in new_component_names:
            components.add_component(component_name)

        self.assertEqual(components.get_component_list(), new_component_names)
        self.assertEqual(components.get_latest_full_epoch(), NO_MESSAGES)
        self.assertEqual(str(components), ", ".join([
            "{:s} ({:d}, False)".format(component_name, NO_MESSAGES)
            for component_name in new_component_names
        ]))

        self.assertEqual(components.get_latest_epoch_for_component("test"), None)
        for component_name in new_component_names:
            self.assertEqual(components.get_latest_epoch_for_component(component_name), NO_MESSAGES)

        # remove some components
        for component_name in removed_component_names:
            components.remove_component(component_name)

        self.assertEqual(components.get_component_list(), remaining_component_names)
        self.assertEqual(components.get_latest_full_epoch(), NO_MESSAGES)
        self.assertEqual(str(components), ", ".join([
            "{:s} ({:d}, False)".format(component_name, NO_MESSAGES)
            for component_name in remaining_component_names
        ]))

        for component_name in removed_component_names:
            self.assertEqual(components.get_latest_epoch_for_component(component_name), None)
        for component_name in remaining_component_names:
            self.assertEqual(components.get_latest_epoch_for_component(component_name), NO_MESSAGES)

    def test_simulation_phases(self):
        """Tests the latest epoch calculations."""
        new_component_names = ["generator", "planner", "logger", "extra", "watcher"]
        component_names_expect_first = new_component_names[1:]
        component_names_expect_last = new_component_names[:len(new_component_names) - 1]
        component_names_expect_middle = new_component_names[:len(new_component_names) // 2] + \
            new_component_names[len(new_component_names) // 2 + 1:]

        # Define which components send ready messages at which epochs.
        # The tuple format is (component_name_list, expected_last_full_epoch).
        ready_messages = {
            0: (new_component_names, 0),
            1: (component_names_expect_first, 0),
            2: (new_component_names, 2),
            3: (new_component_names, 3),
            4: (component_names_expect_first, 3),
            5: (component_names_expect_first, 3),
            6: (component_names_expect_middle, 5),
            7: (component_names_expect_last, 6),
            8: (new_component_names, 8)
        }

        components = SimulationComponents()
        for component_name in new_component_names:
            components.add_component(component_name)

        for epoch_number, (component_names, full_epoch) in ready_messages.items():
            with self.subTest(epoch_number=epoch_number):
                for epoch_component_name in component_names:
                    components.register_status_message(epoch_component_name, epoch_number, epoch_component_name)

                self.assertEqual(components.get_latest_full_epoch(), full_epoch)
                self.assertEqual(components.get_latest_status_message_ids(), ready_messages[epoch_number][0])

                for actual_component_name in new_component_names:
                    with self.subTest(component_name=actual_component_name):
                        self.assertGreaterEqual(
                            components.get_latest_epoch_for_component(actual_component_name), full_epoch)
                        if actual_component_name in component_names:
                            self.assertEqual(
                                components.get_latest_epoch_for_component(actual_component_name), epoch_number)
                        else:
                            self.assertLess(
                                components.get_latest_epoch_for_component(actual_component_name), epoch_number)

                self.assertTrue(components.is_in_normal_state())

        # test handling of status error messages
        # The tuple format is (component_name_list, components_with_error).
        status_messages = {
            9: (new_component_names, ["generator"]),
            10: (new_component_names, ["generator", "planner"]),
            11: (new_component_names, ["planner"])
        }

        self.assertTrue(components.is_component_in_normal_state("generator"))
        self.assertTrue(components.is_component_in_normal_state("planner"))
        self.assertTrue(components.is_component_in_normal_state("logger"))

        for epoch_number, (component_names, error_list) in status_messages.items():
            with self.subTest(epoch_number=epoch_number):
                for epoch_component_name in component_names:
                    components.register_status_message(
                        component_name=epoch_component_name,
                        epoch_number=epoch_number,
                        status_message_id=epoch_component_name,
                        error_state=epoch_component_name in error_list)
                self.assertFalse(components.is_in_normal_state())

        # "generator" and "planner" should be in error state and the last "ready" message
        #  should not have registered for "generator" because it was in an error state.
        self.assertEqual(components.get_latest_epoch_for_component("generator"), 10)
        self.assertEqual(components.get_latest_epoch_for_component("planner"), 11)
        self.assertEqual(components.get_latest_epoch_for_component("logger"), 11)
        self.assertFalse(components.is_component_in_normal_state("generator"))
        self.assertFalse(components.is_component_in_normal_state("planner"))
        self.assertTrue(components.is_component_in_normal_state("logger"))

        self.assertIsNone(components.get_latest_epoch_for_component("unknown"))
        self.assertIsNone(components.is_component_in_normal_state("unknown"))


if __name__ == '__main__':
    unittest.main()
