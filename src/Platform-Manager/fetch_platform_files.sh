#!/bin/bash
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>
#            Otto Hylli <otto.hylli@tuni.fi>

# Fetches all the files required to install the simulation platform and run simulations.

# take the repository type and access token from command line parameters
repository_type=$1
access_token=$2

if [[ -z "$repository_type" || ("$repository_type" != "gitlab" && "$repository_type" != "github") ]]
then
    echo "Usage: source fetch_platform_files.sh [gitlab|github] [<access_token>]"
    return 0 2> /dev/null || exit 0
fi

current_folder=$(pwd)
read -p "Do you want to install the simulation platform to the folder $current_folder? [y/n] " answer
if [[ -z "$answer" ]] || [[ "$answer" != "y" ]]
then
    return 0 2> /dev/null || exit 0
fi

# hard coded values for the repository
if [[ "$repository_type" == "gitlab" ]]
then
    repository_host="https://git.ain.rd.tut.fi"
    repository_name="procemplus/platform-manager"
    repository_ssl="false"
else
    repository_host="https://github.com"
    repository_name="simcesplatform/platform-manager"
    repository_ssl="true"
fi

repository_branch="master"
file_list_file="platform_file_list.txt"
access_token_file="access_tokens.env"

set_current_address () {
    current_file=$1
    if [[ "$repository_type" == "gitlab" ]]
    then
        current_file_encoded=$(echo "$current_file" | sed -r "s/\//%2F/g")
        current_address="$repository_host/api/v4/projects/$repository_name_encoded/repository/files/$current_file_encoded/raw?ref=$repository_branch"
    elif [[ -z "$access_token" ]]  # private GitHub repository
    then
        current_address="https://$access_token@raw.githubusercontent.com/$repository_name/$repository_branch/$current_file"
    else  # public GitHub repository
        current_address="https://raw.githubusercontent.com/$repository_name/$repository_branch/$current_file"
    fi
}

fetch_file() {
    set_current_address $1

    if [[ $current_file == *"/"* ]]
    then
        component_folder=${current_file%/*}
        if [[ "$component_folder" != *"."* ]]
        then
            mkdir -p "$component_folder"
        fi
    fi

    if [[ "$repository_type" == "gitlab" ]] && [[ ! -z "$access_token" ]]
    then
        curl --silent $curl_insecure --header "Private-Token: $access_token" "$current_address" > "$current_file"
    else
        curl --silent $curl_insecure "$current_address" > "$current_file"
    fi
}

repository_name_encoded=$(echo "$repository_name" | sed -r "s/\//%2F/g")
if [[ "$repository_ssl" == "false" ]]
then
    curl_insecure="--insecure"
else
    curl_insecure=""
fi

echo "Fetching the list for required files from $repository_type repository '$repository_name'."
fetch_file "$file_list_file"

if ! test -f "$file_list_file"
then
    echo "Cannot find file '$file_list_file'. Check the repository type and the access token."
    echo "Usage: source fetch_platform_files.sh [gitlab|github] [<access_token>]"
    return 0 2> /dev/null || exit 0
fi

# fetch all the files marked as required files in the fetched file list
while read -r required_file
do
    first_character=${required_file:0:1}
    # check that the current line is not a comment or empty line
    if [[ "$first_character" == "#" ]] || [[ "$required_file" == "" ]]
    then
        continue
    fi

    echo "Fetching file $required_file"
    fetch_file "$required_file"
done < "$file_list_file"

echo ""
echo "Checking if all required files have been fetched."

# check that all required files are found
check_all="true"
while read -r required_file
do
    first_character=${required_file:0:1}
    # check that the current line is not a comment or empty line
    if [[ "$first_character" == "#" ]] || [[ "$required_file" == "" ]]
    then
        continue
    fi

    if ! test -f "$required_file"
    then
        echo "File '$required_file' was not found!"
        check_all="false"
    fi
done < "$file_list_file"

if [[ "$check_all" == "true" ]]
then
    # if the access token is given, set it to the access token file for the manifest file fetcher
    if [[ ! -z "$access_token" ]]
    then
        if [[ "$repository_type" == "gitlab" ]]
        then
            sed -i "/GITLAB_ACCESS_TOKEN=/c\GITLAB_ACCESS_TOKEN=$access_token" "$access_token_file"
        else
            sed -i "/GITHUB_ACCESS_TOKEN=/c\GITHUB_ACCESS_TOKEN=$access_token" "$access_token_file"
        fi
        echo "Added access token to the settings file '$access_token_file'."
    fi
    echo "All files where found. Platform is ready for installation."
else
    echo "There were missing files. Check $file_list_file for the required files."
fi
