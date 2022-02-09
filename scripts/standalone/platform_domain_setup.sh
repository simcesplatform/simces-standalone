#!/bin/bash
# Copyright 2022 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

# Fetches the Docker images and component manifest files for the domain component for the Simulation platform.
# Also makes the resource files available for the Simulation platform.
# Note, for the standalone platform version

echo ""
echo "Building the domain Docker images from the source code"
source build_docker_images.sh docker_images_domain_standalone.txt

echo ""
echo "Copying the component manifests."
source fetch_local_manifests.sh local_manifest_files.txt

echo ""
echo "Modifying the component manifest files to point to local Docker images"
source modify_local_manifests.sh ghcr.io local

echo ""
source copy_folder_to_volume.sh resources simces_simulation_resources /resources
