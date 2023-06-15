#!/bin/bash
# Copyright 2023 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

# Script that copies all the log files from the Docker volume to a local folder.
# This can be useful with Docker installation where sharing local folders as Docker volumnes is limited.

exists() {
    command -v "$1" >/dev/null 2>&1;
}

if exists "docker compose"
then
    compose_command="docker compose"
else
    compose_command="docker-compose"
fi

container="log_access"
container_log_folder="logs"
local_log_folder="."
log_file_type="log"

$compose_command -f docker-compose-logs.yml up --detach
for log_file in $(docker exec -t ${container} ls -l ${container_log_folder} | grep .${log_file_type} | grep --invert-match total | awk '{print $NF}')
do
    log_file_name=$(echo "${log_file}" | cut --delimiter="." --fields=1)
    docker cp ${container}:${container_log_folder}/${log_file_name}.${log_file_type} ${local_log_folder}
done

$compose_command -f docker-compose-logs.yml down --remove-orphans
