#!/bin/bash
# Copyright 2023 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

exists() {
    command -v "$1" >/dev/null 2>&1;
}

if exists "docker compose"
then
    compose_command="docker compose"
else
    compose_command="docker-compose"
fi

configuration_file=$1
platform_manager_env_file="common.env"

echo "Copying the simulation configuration file to the Platform Manager."
source copy_file_to_volume.sh $configuration_file simces_simulation_configuration /configuration

# Change the configuration file setting for Platform Manager.
sed -i "/SIMULATION_CONFIGURATION_FILE=/c\SIMULATION_CONFIGURATION_FILE=\/configuration\/${configuration_file}" ${platform_manager_env_file}

echo "Starting the Platform Manager."
$compose_command --file docker-compose.yml up
