#!/bin/bash
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

configuration_file=$1
platform_manager_env_file="common.env"

echo "Copying the simulation configuration file to the Platform Manager."
source copy_file_to_volume.sh $configuration_file simces_simulation_configuration /configuration

# Change the configuration file setting for Platform Manager.
sed -i "/SIMULATION_CONFIGURATION_FILE=/c\SIMULATION_CONFIGURATION_FILE=\/configuration\/${configuration_file}" ${platform_manager_env_file}

echo "Starting the Platform Manager."
docker-compose --file docker-compose.yml up
