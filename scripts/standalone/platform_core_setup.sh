#!/bin/bash
# Copyright 2022 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

# Builds the core components and starts the background containers for the Simulation platform.
# Note, for the standalone platform version

echo "Creating Docker volumes for the simulation platform."
docker volume create simces_mongodb_data
docker volume create simces_simulation_configuration
docker volume create simces_simulation_resources
docker volume create simces_simulation_logs

echo ""
echo "Creating Docker network for the simulation platform."
docker network inspect simces_platform_network >/dev/null 2>&1 || \
    docker network create simces_platform_network
docker network inspect simces_mongodb_network >/dev/null 2>&1 || \
    docker network create simces_mongodb_network
docker network inspect simces_rabbitmq_network >/dev/null 2>&1 || \
    docker network create simces_rabbitmq_network

echo ""
echo "Building the core Docker images from the source code"
source build_docker_images.sh docker_images_core_standalone.txt

echo ""
echo "Starting the background Docker containers."
docker-compose --file background/docker-compose-background.yml up --detach

echo ""
echo "Copying the component manifests."
source fetch_local_manifests.sh local_manifest_files.txt

echo ""
echo "Modifying the component manifest files to point to local Docker images"
source modify_local_manifests.sh ghcr.io local
