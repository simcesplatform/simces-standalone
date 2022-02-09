# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

"""This module contains general utils for working with simulation platform message classes."""

from typing import Iterator


def get_next_message_id(source_process_id: str, start_number: int = 1) -> Iterator[str]:
    """Generator for getting unique message ids."""
    message_number = start_number
    while True:
        yield "{:s}-{:d}".format(source_process_id, message_number)
        message_number += 1
