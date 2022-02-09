#!/bin/bash
# Copyright 2022 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>

# Modifies all component manifest files found in the local folder
# Note, for the standalone platform version

old_tag=$1
new_tag=$2

for manifest_file in $(find manifests/local -type f)
do
    sed -i "s/DockerImage: ${old_tag}/DockerImage: ${new_tag}/" ${manifest_file}
done
