# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains tools for dealing with UCUM unit codes."""

from __future__ import annotations
import csv
import pathlib
import subprocess
from typing import Dict, Union

from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class UnitCode:
    """Class for verifying a string as a valid UCUM (The Unified Code for Units of Measure) code."""

    # Parameters related to the premade unit code files.
    UNIT_CODE_FILE_PATH = "resources"
    UNIT_CODE_FILE_NAMES = ["unit_codes.csv", "unit_codes_addition.csv"]
    UNIT_CODE_FILE_COLUMN_SEPARATOR = ";"
    UNIT_CODE_FILE_CODE_COLUMN = "Code"
    UNIT_CODE_FILE_DESCRIPTION_COLUMN = "Description"

    # Name of the Javascript UCUM unit code validator.
    # The use of the validator requires that NodeJS is installed in the system.
    JAVASCRIPT_VALIDATOR = "validator.js"
    JAVASCRIPT_SYSTEM_CALL = "nodejs"
    VALIDATOR_VALID_TEXT = "valid"
    VALIDATOR_RESULT_SEPARATOR = ";"

    UNIT_CODE_LIST = {}

    @classmethod
    def is_valid(cls, unit_code: str) -> bool:
        """Returns True if unit_code is a valid UCUM code."""
        if not cls.UNIT_CODE_LIST:
            cls.UNIT_CODE_LIST = cls.__return_unit_code_list()

        # Check against the preloaded unit codes.
        if unit_code in cls.UNIT_CODE_LIST:
            return True

        # Use Javascript library ucum-lhc to validate the unit code.
        javascript_validator = cls.__find_resource_filename(cls.UNIT_CODE_FILE_PATH, cls.JAVASCRIPT_VALIDATOR)
        if javascript_validator is None:
            # Could not find the JavaScript validator file and the given unit code was not in the premade lists.
            return False
        try:
            validator_result = subprocess.run([cls.JAVASCRIPT_SYSTEM_CALL, javascript_validator, unit_code],
                                              check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            validator_output = validator_result.stdout.decode("UTF-8").strip()

            # The output from the Javascript validator should be <validator_text>;<unit_description>
            output_parts = validator_output.split(cls.VALIDATOR_RESULT_SEPARATOR)
            LOGGER.debug("Result UCUM unit validator: {:s} -> {:s}".format(unit_code, output_parts[0]))
            if output_parts[0] != cls.VALIDATOR_VALID_TEXT:
                return False

            unit_description = cls.VALIDATOR_RESULT_SEPARATOR.join(output_parts[1:])
            cls.UNIT_CODE_LIST[unit_code] = unit_description
            cls.__add_new_unit_code(unit_code, unit_description)
            return True

        except subprocess.CalledProcessError as error:
            LOGGER.warning("CalledProcessError '{}' when trying to validate unit code: {:s}".format(error, unit_code))
        except OSError as error:
            LOGGER.warning("OSError '{}' when trying to validate unit code: {:s}".format(error, unit_code))

        # An error occurred while trying to use the JavaScript validator and
        # the given unit code was not in the premade lists.
        return False

    @classmethod
    def get_description(cls, unit_code: str) -> Union[str, None]:
        """Returns the description for the given unit code. Return None if the code is not valid."""
        if not cls.UNIT_CODE_LIST:
            cls.UNIT_CODE_LIST = cls.__return_unit_code_list()

        return cls.UNIT_CODE_LIST.get(unit_code, None)

    @classmethod
    def __find_resource_filename(cls, resource_path, resource_file) -> Union[str, None]:
        """Returns the full path to the resource file or None if the file is not found."""
        file_list = list(pathlib.Path(".").glob("/".join(["**", resource_path, resource_file])))
        if file_list:
            return "/".join(file_list[0].parts)
        return None

    @classmethod
    def __return_unit_code_list(cls) -> Dict[str, str]:
        unit_code_dict = {}

        current_path = pathlib.Path(".")
        for unit_code_file_name in cls.UNIT_CODE_FILE_NAMES:
            # Use glob to find the resource file paths to allow code usage in a submodule.
            for unit_code_file in current_path.glob("/".join(["**", cls.UNIT_CODE_FILE_PATH, unit_code_file_name])):
                try:
                    with open(unit_code_file, mode="r") as csv_file:
                        csv_reader = csv.DictReader(csv_file, delimiter=cls.UNIT_CODE_FILE_COLUMN_SEPARATOR)
                        for csv_row in csv_reader:
                            unit_code = csv_row[cls.UNIT_CODE_FILE_CODE_COLUMN]
                            unit_description = csv_row[cls.UNIT_CODE_FILE_DESCRIPTION_COLUMN]

                            unit_code_dict[unit_code] = unit_description

                except KeyError as key_error:
                    LOGGER.error("KeyError '{:s}' while trying to read unit codes from file {:s}".format(
                        str(key_error), unit_code_file))

                except csv.Error as csv_error:
                    LOGGER.error("csv.Error '{:s}' while trying to read unit codes from file {:s}".format(
                        str(csv_error), unit_code_file))

                except OSError as os_error:
                    LOGGER.error("OSError '{:s}' while trying to read file {:s}".format(
                        str(os_error), unit_code_file
                    ))

        return unit_code_dict

    @classmethod
    def __add_new_unit_code(cls, unit_code: str, unit_description: str):
        """Adds a new unit code to the unit code file that is preloaded before the first validator query."""

        # find out the actual path of the unit code file to allow use when included as a submodule
        unit_code_file_path = next(pathlib.Path(".").glob(
            "/".join(["**", cls.UNIT_CODE_FILE_PATH, cls.UNIT_CODE_FILE_NAMES[0]])))
        additional_file = "/".join(list(unit_code_file_path.parts[:-1]) + [cls.UNIT_CODE_FILE_NAMES[-1]])

        try:
            with open(additional_file, mode="a", encoding="UTF-8") as additional_unit_file:
                additional_unit_file.write(cls.UNIT_CODE_FILE_COLUMN_SEPARATOR.join(
                    [unit_code, unit_description]) + "\n")
        except OSError as os_error:
            LOGGER.error("OSError '{:s}' while trying to write to file {:s}".format(
                str(os_error), additional_file
            ))
