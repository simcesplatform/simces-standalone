#!/bin/bash
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

# Script to stop a simulation run by stopping all the associated Docker containers.
# NOTE: this will not effect any external component participating in the simulation.
# NOTE: this will not remove the stopped containers

container_prefix="Sim${1}_"

for container in $(docker ps | awk '{print $NF}' | grep "${container_prefix}")
do
    docker stop ${container}
done
