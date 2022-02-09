# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""Unit tests for the functions in tools.py."""

import logging
import unittest

from tools.tools import FullLogger, load_environmental_variables


def add_log_message(logger: FullLogger, check_list: list, log_level: int, log_message: str):
    """Adds a log message to a logger and check string to a check list."""
    if log_level == logging.DEBUG:
        logger.debug(log_message)
    elif log_level == logging.INFO:
        logger.info(log_message)
    elif log_level == logging.WARNING:
        logger.warning(log_message)
    elif log_level == logging.ERROR:
        logger.error(log_message)
    elif log_level == logging.CRITICAL:
        logger.critical(log_message)
    check_list.append(":".join([logger.MESSAGE_LEVEL[log_level], logger.logger_name, log_message]))


class TestTools(unittest.TestCase):
    """Unit tests for the tools module."""
    def test_load_environmental_variables(self):
        """Tests for loading environmental variables."""

        # the environmental values that are set in the docker-compose file
        # - ENV_TEST_VALUE_BOOL=true
        # - ENV_TEST_VALUE_INT=12
        # - ENV_TEST_VALUE_FLOAT=2.34
        # - ENV_TEST_VALUE_STRING=hello
        test_env_variables = load_environmental_variables(
            ("ENV_TEST_VALUE_BOOL", bool, False),
            ("ENV_TEST_VALUE_INT", int, 13),
            ("ENV_TEST_VALUE_FLOAT", float, 7.35),
            ("ENV_TEST_VALUE_STRING", str, "world"),
            ("ENV_TEST_VALUE_MISSING", str, "missing")
        )

        self.assertIsInstance(test_env_variables["ENV_TEST_VALUE_BOOL"], bool)
        self.assertEqual(test_env_variables["ENV_TEST_VALUE_BOOL"], True)
        self.assertIsInstance(test_env_variables["ENV_TEST_VALUE_INT"], int)
        self.assertEqual(test_env_variables["ENV_TEST_VALUE_INT"], 12)
        self.assertIsInstance(test_env_variables["ENV_TEST_VALUE_FLOAT"], float)
        self.assertEqual(test_env_variables["ENV_TEST_VALUE_FLOAT"], 2.34)
        self.assertIsInstance(test_env_variables["ENV_TEST_VALUE_STRING"], str)
        self.assertEqual(test_env_variables["ENV_TEST_VALUE_STRING"], "hello")
        self.assertIsInstance(test_env_variables["ENV_TEST_VALUE_MISSING"], str)
        self.assertEqual(test_env_variables["ENV_TEST_VALUE_MISSING"], "missing")

    def test_logging(self):
        """Tests for using FullLogger."""
        logger = FullLogger("test_logger", logger_level=logging.DEBUG, stdout_output=False)
        check_logs = []
        # The output for test_logger will have the default format, not the format used in FullLogger
        with self.assertLogs(logger.logger, logger.level) as test_logger:
            add_log_message(logger, check_logs, logging.DEBUG, "Debug test")
            add_log_message(logger, check_logs, logging.INFO, "Info test")
            add_log_message(logger, check_logs, logging.WARNING, "Warning test")
            add_log_message(logger, check_logs, logging.ERROR, "Error test")
            add_log_message(logger, check_logs, logging.CRITICAL, "Critical test")
        self.assertEqual(test_logger.output, check_logs)

        logger.level = logging.INFO
        check_logs = []
        with self.assertLogs(logger.logger, logger.level) as test_logger:
            logger.debug("Debug test")
            add_log_message(logger, check_logs, logging.INFO, "Info test")
            add_log_message(logger, check_logs, logging.WARNING, "Warning test")
            add_log_message(logger, check_logs, logging.ERROR, "Error test")
            add_log_message(logger, check_logs, logging.CRITICAL, "Critical test")
        self.assertEqual(test_logger.output, check_logs)

        logger.level = logging.WARNING
        check_logs = []
        with self.assertLogs(logger.logger, logger.level) as test_logger:
            logger.debug("Debug test")
            logger.info("Info test")
            add_log_message(logger, check_logs, logging.WARNING, "Warning test")
            add_log_message(logger, check_logs, logging.ERROR, "Error test")
            add_log_message(logger, check_logs, logging.CRITICAL, "Critical test")
        self.assertEqual(test_logger.output, check_logs)

        logger.level = logging.ERROR
        check_logs = []
        with self.assertLogs(logger.logger, logger.level) as test_logger:
            logger.debug("Debug test")
            logger.info("Info test")
            logger.warning("Warning test")
            add_log_message(logger, check_logs, logging.ERROR, "Error test")
            add_log_message(logger, check_logs, logging.CRITICAL, "Critical test")
        self.assertEqual(test_logger.output, check_logs)

        logger.level = logging.CRITICAL
        check_logs = []
        with self.assertLogs(logger.logger, logger.level) as test_logger:
            logger.debug("Debug test")
            logger.info("Info test")
            logger.warning("Warning test")
            logger.error("Error test")
            add_log_message(logger, check_logs, logging.CRITICAL, "Critical test")
        self.assertEqual(test_logger.output, check_logs)


if __name__ == '__main__':
    unittest.main()
