#!/bin/bash
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

filename=$1
volume_name=$2
volume_folder=$3

helper_container="simces_file_copy_container"

echo "Copying '$filename' to Docker volume '$volume_name' to folder '$volume_folder'"
docker volume create $volume_name > /dev/null

# remove earlier helper container
docker stop $helper_container > /dev/null 2>&1
docker rm $helper_container > /dev/null 2>&1

# start the helper container
docker run -d --name $helper_container --volume $volume_name:$volume_folder:rw ubuntu:18.04 sleep 10m > /dev/null

docker cp $filename $helper_container:$volume_folder/$filename > /dev/null

# remove the helper container
docker stop $helper_container > /dev/null
docker rm $helper_container > /dev/null
