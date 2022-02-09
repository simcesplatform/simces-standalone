#!/bin/bash
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

# Get the current UTC time in ISO 8601 format in millisecond precision.
simulation_id=$(date --utc +"%FT%T.%3NZ")

# Modify the configuration files with the new simulation id.
for env_file in $(ls env/*.env)
do
    sed -i "/SIMULATION_ID=/c\SIMULATION_ID=${simulation_id}" ${env_file}
done
