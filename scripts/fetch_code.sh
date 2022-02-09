#!/bin/bash
# Copyright 2022 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

# Fetches the source code for simces core components from the individual repositories

read -p "Do you want to replace local source code and documentation with versions fetched from GitHub? [y/n] " answer
if [[ -z "$answer" ]] || [[ "$answer" != "y" ]]
then
    return 0 2> /dev/null || exit 0
fi

current_folder=$(pwd)
script_folder=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)

repository_file="${script_folder}/repositories.txt"

# set the source code folder as the current folder
cd "${script_folder}/../src"

# go through all the repositories listed in the repository file and fetch the source code
while IFS= read -r repository || [ -n "$repository" ]
do
    first_character=${repository:0:1}
    # check that the current line is not a comment or empty line
    if [[ "$first_character" == "#" ]] || [[ "$repository" == "" ]]
    then
        continue
    fi

    target_folder=$(echo "${repository}" | cut -d';' -f1)
    git_address=$(echo "${repository}" | cut -d';' -f2)

    # remove the local source code folder
    rm -rf ${target_folder}
    # fetch the source code from GitHub
    git clone --recursive ${git_address}.git ${target_folder}

done < "$repository_file"

# remove .gitmodules files
for gitmodulefile in $(find . -type f | grep .gitmodules)
do
    if [[ ${gitmodulefile:(-11)} == ".gitmodules" ]]
    then
        rm ${gitmodulefile}
    fi
done

# remove .git folders
for gitfolder in $(find . | grep .git)
do
    if [[ ${gitfolder:(-4)} == ".git" ]]
    then
        rm -rf ${gitfolder}
    fi
done

# fetch the HTML documentation from its GitHub repository
docs_repository="https://github.com/simcesplatform/simcesplatform.github.io"
docs_target_folder_base="${script_folder}/.."
docs_source_folder="docs"
temp_folder="__temp__"

cd ${docs_target_folder_base}
# fetch the documentation from the GitHub repository
git clone --recursive ${docs_repository}.git ${temp_folder}

# pick only the HTML documentation from the repository and put it in the docs folder
rm -rf ${docs_source_folder}
mv ${temp_folder}/${docs_source_folder} .
rm -rf ${temp_folder}

# set the current folder back to the original
cd ${current_folder}
