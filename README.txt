# SimCES Simulation Platform

SimCES, Simulation Environment of Complex Energy System

Copyright (c) 2022 Tampere University and VTT Technical Research Centre of
Finland. Please see the attached license file.


## SimCES in short

SimCES is a simulation platform for modular development, enabling the
components to execute in any runtime. If desirable, the components can run in
any location and connect over Internet. The platform enables loose coupling
between the components, facilitating development and management.

To reduce the burden of development, the simulation components can run as
Docker containers. Furthermore, there is a component framework for Python to
simplify the implementation of workflows, although any runtime and language
are possible.

Despite "energy" in the name, the core of SimCES platform is domain agnostic.
However, energy is mentioned in the name due to the original motivation of the
platform.

This is the "standalone" version of SimCES. Please read below what this means.


## About this standalone version

This is the standalone version of SimCES platform. This is different from the
basic version of the platform, which is distributed component-by-component and
relies on remote container registries. Instead, this standalone version
provides all of the code in one location. It was created to enable reliable
archiving so that none of the required components can cause conflicts due to
availability or versioning.

This standalone version enables merely a subset of the simulations made with
the platform. This is because it would be impossible to include all of the
simulation components (some of which run on an external platform) along with
all of the data, some of which is cannot be openly distributed. Therefore,
this distribution aims primarily at enabling easy experiments with the
platform rather than exhaustively providing all of the software implemented.

You can find the documentation of the basic version here:
https://simcesplatform.github.io/ . Although this was written for the basic
version, the same design principles apply even in the standalone version.


## System requirements

TODO!

- Platform: Docker Compose (version?)
- Memory: ?
- Storage space: ?


## Quick instructions for standalone version

Preparation for the installation:
- (Optional) Update source code from for the components from GitHub: `source scripts/fetch_code.sh`
- (Required) Copy the required platform files to installation directory: `source scripts/copy_platform_files.sh`

Installing the platform:
- Enter the installation directory: `cd platform`
- Build and install the core platform: `source platform_core_setup.sh`
- Build and install the included domain components: `source platform_domain_setup.sh`
- Run the test simulation: `source start_simulation.sh simulation_configuration_test.yml`
- Run the Energy Community test scenario: `source start_simulation.sh simulation_configuration_ec.yml`
