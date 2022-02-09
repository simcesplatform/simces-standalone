#!/bin/bash
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

# Script to follow a running simulation with a colored output simular to docker-compose logs.

container_prefix="Sim${1}_"
current_color_number=1

set_color_code () {
    if [[ $1 == "SimulationManager" ]]
    then
        color_code="1;31"  # red
    elif [[ $1 == "LogWriter" ]]
    then
        color_code="1;37"  # white
    elif [[ $current_color_number == 1 ]]
    then
        color_code="1;32"  # green
        current_color_number=2
    elif [[ $current_color_number == 2 ]]
    then
        color_code="1;33"  # yellow
        current_color_number=3
    elif [[ $current_color_number == 3 ]]
    then
        color_code="1;34"  # blue
        current_color_number=4
    elif [[ $current_color_number == 4 ]]
    then
        color_code="1;35"  # magenta
        current_color_number=5
    elif [[ $current_color_number == 5 ]]
    then
        color_code="1;36"  # cyan
        current_color_number=1
    fi
}

comparison_name="SimulationManager"

all_commands=()
for container in $(docker ps | awk '{print $NF}' | grep "${container_prefix}")
do
    short_name=${container:${#container_prefix}}

    # add extra spaces to the prefix to have properly aligned output
    extra_spaces_number=$(( ${#comparison_name} - ${#short_name} ))
    extra_spaces=""
    for (( index=1; index<=$extra_spaces_number; index++))
    do
        extra_spaces="$extra_spaces "
    done
    output_prefix="$short_name$extra_spaces | "

    set_color_code "$short_name"
    all_commands+=( "docker logs --follow $container | sed -u -e 's/^/$output_prefix/' | GREP_COLOR='$color_code' grep --color '.' &" )
done

echo "{ ${all_commands[@]} printf ''; }" | bash
