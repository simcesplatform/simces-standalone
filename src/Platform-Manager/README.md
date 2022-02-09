# Platform Manager

Platform Manager handles starting new simulations for the simulation platform.

```text
NOTE: this readme has not been updated to the current version of Platform Manager and the contents are deprecated

See the simulation platform documentation on how to use the available scripts to install the platform
and on how to run simulations.
```

## Setup

To build the required Docker images, to make the needed static files available, and to start the background processes:

```bash
source platform_setup.sh
```

### Advanced setup

To only build the Docker images:

```bash
docker-compose -f build/docker-compose-build-images.yml build
```

To only copy the static resource files:

```bash
source copy_folder_to_volume.sh resources simulation_resources /resources
```

To only start the background processes (RabbitMQ, MongoDB, LogReader):

```bash
docker-compose -f background/docker-compose-background.yml up --detach
```

## Run simulation

To start a simulation: edit the simulation settings in [simulation_configuration.yml](simulation_configuration.yml) and the run the command

```bash
source start_platform.sh
```
