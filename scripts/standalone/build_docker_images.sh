#!/bin/bash
# Copyright 2022 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

# Builds the given Docker images from the source code.
# For the standalone platform version

if [ -z "$1" ]
then
    echo "Usage: source build_docker_images.sh <file_with_docker_image_names_and_source_folders>"
    return 0 2> /dev/null || exit 0
fi

input_file=$1
if ! test -f "$input_file"
then
    echo "Cannot find file '$input_file'"
    echo "Usage: source build_docker_images.sh <file_with_docker_image_names_and_source_folders>"
    return 0 2> /dev/null || exit 0
fi

current_folder=$(pwd)
script_folder=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)

echo "Reading '$input_file' for Docker image names and source folders"
while IFS= read -r docker_image || [ -n "$docker_image" ]
do
    first_character=${docker_image:0:1}
    # check that the current line is not a comment or empty line
    if [[ "$first_character" == "#" ]] || [[ "$docker_image" == "" ]]
    then
        continue
    fi

    docker_image_name=$(echo "${docker_image}" | cut -d';' -f1)
    source_folder=$(echo "${docker_image}" | cut -d';' -f2)
    dockerfile_name=$(echo "${docker_image}" | cut -d';' -f3)

    echo "Building Docker image '${docker_image_name}' from ${source_folder} using ${dockerfile_name}"
    cd ${script_folder}/${source_folder}
    docker build --tag ${docker_image_name} --file ${dockerfile_name} .

done < "$input_file"

cd ${current_folder}
