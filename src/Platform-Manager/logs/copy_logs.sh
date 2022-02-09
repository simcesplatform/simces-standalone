#!/bin/bash
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

# Script that copies all the log files from the Docker volume to a local folder.
# This can be useful with Docker installation where sharing local folders as Docker volumnes is limited.

container="simces_log_access"
volume_name="simces_simulation_logs"
container_log_folder="logs"
local_log_folder="."
log_file_type="log"

# start a container that has access to the volume containing the log files
docker run -d --name $container --volume $volume_name:/$container_log_folder:ro ubuntu:18.04 sleep 10m > /dev/null

for log_file in $(docker exec -t ${container} ls -l ${container_log_folder} | grep .${log_file_type} | grep --invert-match total | awk '{print $NF}')
do
    log_file_name=$(echo "${log_file}" | cut --delimiter="." --fields=1)
    docker cp ${container}:${container_log_folder}/${log_file_name}.${log_file_type} ${local_log_folder}
done

# stop and remove the helper container
docker stop $container > /dev/null
docker rm $container > /dev/null
