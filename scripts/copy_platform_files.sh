#!/bin/bash
# Copyright 2022 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>
#            Otto Hylli <otto.hylli@tuni.fi>

# Fetches all the files required to install the simulation platform and run simulations.
# The standalone platform version

current_folder=$(pwd)
script_folder=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)
source_folder=$(echo "${script_folder}/Platform-Manager" | sed 's/scripts/src/')
platform_folder=$(echo "${script_folder}" | sed 's/scripts/platform/')

read -p "Do you want to install the simulation platform to the folder $platform_folder? [y/n] " answer
if [[ -z "${answer}" ]] || [[ "${answer}" != "y" ]]
then
    return 0 2> /dev/null || exit 0
fi

file_list_file="${source_folder}/platform_file_list.txt"

copy_file() {
    current_file=$1

    if [[ ${current_file} == *"/"* ]]
    then
        component_folder=${current_file%/*}
        if [[ ${component_folder} != *"."* ]]
        then
            mkdir -p ${platform_folder}/${component_folder}
        fi
    fi

    cp ${source_folder}/${current_file} ${platform_folder}/${current_file}
}

echo "Copying the required platform files to ${platform_folder}"
mkdir -p ${platform_folder}

if ! test -f "${file_list_file}"
then
    echo "Cannot find file '${file_list_file}'."
    return 0 2> /dev/null || exit 0
fi

# fetch all the files marked as required files in the fetched file list
while IFS= read -r required_file || [ -n "${required_file}" ]
do
    first_character=${required_file:0:1}
    # check that the current line is not a comment or empty line
    if [[ "${first_character}" == "#" ]] || [[ "${required_file}" == "" ]]
    then
        continue
    fi

    echo "Copying file ${required_file}"
    copy_file "${required_file}"
done < "${file_list_file}"

echo ""
echo "Checking if all required files have been copied."

# check that all required files are found
check_all="true"
while read -r required_file
do
    first_character=${required_file:0:1}
    # check that the current line is not a comment or empty line
    if [[ "${first_character}" == "#" ]] || [[ "${required_file}" == "" ]]
    then
        continue
    fi

    if ! test -f "${platform_folder}/${required_file}"
    then
        echo "File '${required_file}' was not found!"
        check_all="false"
    fi
done < "${file_list_file}"

if [[ "${check_all}" == "true" ]]
then
    echo "All files where found. Platform is ready for installation."
else
    echo "There were missing files. Check ${file_list_file} for the required files."
fi

# set the current folder back to the original
cd ${current_folder}
