# Simulation Manager

Implementation of the simulation manager component as well as dummy components for the simulation platform.
The simulation manager handles the starting and ending of the simulation and starting simulation epochs when all simulation components are ready for a new epoch, see: [Simulation Manager](https://github.com/simcesplatform/core_simulationmanager).

## Contents of the repository

<!-- no toc -->
- Readme instruction
    - [Cloning the repository](#cloning-the-repository)
        - Instructions on how to clone the repository.
    - [Pulling changes to previously cloned repository](#pulling-changes-to-previously-cloned-repository)
        - Instructions on how to pull updates to an existing repository.
    - [Start local RabbitMQ server](#start-local-rabbitmq-server)
        - Instructions on how to start locally deployed RabbitMQ message bus server.
    - [Run test simulation](#run-test-simulation)
        - Instructions on how to run a test simulation.
    - [Run unit tests](#run-unit-tests)
        - Instructions on how to run the unit tests.
    - [Stop running simulation](#stop-running-simulation)
        - Instructions on how to stop a running simulation in the middle of a simulation run.
    - [Stop local RabbitMQ server](#stop-local-rabbitmq-server)
        - Instructions on how to stop locally deployed RabbitMQ server.
- Folder contents
    - [manager](manager)
        - The main code for the simulation manger component.
        - [manager.py](manager/manager.py) contains the main code for the simulation manager.
        - [components.py](manager/components.py) contains a helper class to keep track of the simulation components.
        - [Dockerfile-manager](Dockerfile-manager) can be used to create a Docker image of the simulation manager.
    - [dummy](dummy)
        - An implementation of a dummy simulation component for test simulation.
        - [dummy.py](dummy/dummy.py) contains the main code for the dummy component.
        - [random_series.py](dummy/random_series.py) contains helper function to generate random time series for the dummy component.
        - [Dockerfile-dummy](Dockerfile-dummy) can be used to create a Docker image of the dummy component.
    - [listener](listener)
        - A simple message bus listener component for testing purposes. The basis of the listener part for the LogWriter.
    - [simulation-tools](tools)
        - The helper library [simulation-tools](https://github.com/simcesplatform/simulation-tools) as a Git submodule. See [README.md](https://github.com/simcesplatform/simulation-tools/blob/master/README.md) for information about the contents of the helper library.
    - [init](init)
        - Init file that adds the submodule simulation-tools to the python path to allow the other code easy access to the tools library.
    - [env](env)
        - Examples of environmental variable files required by the components.
    - [docker_tests](docket_tests)
        - docker-compose file for the unit tests.
    - [docker-files](docker-files)
        - Combined docker-compose file to run a test simulation with the LogReader and the [LogWriter](https://github.com/simcesplatform/core_logwriter/).
    - [rabbitmq](rabbitmq)
        - docker-compose file for setting up a local RabbitMQ server.
    - [logs](logs)
        - Script to help copy the log files produced by the Docker components to a local folder.

## Cloning the repository

```bash
git clone --recursive https://github.com/simcesplatform/simulation-manager.git
```

## Pulling changes to previously cloned repository

Cloning the submodules for repository that does not yet have them:

```bash
git submodule update --init --recursive
```

Pulling changes to both this repository and all the submodules:

```bash
git pull --recurse-submodules
git submodule update --remote
```

To prevent any local changes made to the configuration files containing usernames or passwords showing with `git status`:

```bash
git update-index --skip-worktree env/common.env rabbitmq/rabbitmq.env
```

## Start local RabbitMQ server

Edit the username and password in the file [`rabbitmq/rabbitmq.env`](rabbitmq/rabbitmq.env)

```bash
docker network create rabbitmq_network
docker-compose -f rabbitmq/docker-compose-rabbitmq.yml up --detach
```

## Run test simulation

Edit the files [`common.env`](common.env), [`simulation_manager.env`](simulation_manager.env), [`dummy.env`](dummy.env), and [`docker-compose-test-simulation.yml`](docker-compose-test-simulation.yml) files with the parameters you want. At least [`common.env`](common.env) needs to be edited with the correct username and password for the RabbitMQ server.

Running the `create_new_simulation_id.sh` script creates new simulation id based on the current time and inserts it to the configuration files.

```bash
source create_new_simulation_id.sh
docker-compose -f docker-compose-test-simulation.yml up --build
```

Or to just see all the messages in the message bus:

```bash
docker-compose -f docker_tests/docker-compose-listener.yml up --build --detach
docker-compose -f docker-compose-test-simulation.yml up --build --detach
docker attach listener_component
```

## Run unit tests

```bash
docker network create manager_test_network
docker-compose -f docker_tests/docker-compose-rabbitmq.yml up --detach
docker-compose -f docker_tests/docker-compose-tests.yml up --build
```

Only unit test for the manager and dummy component are run. To run the unit tests defined in the simulation-tools submodule go into the the simulation-tools folder and follow the instructions there.

## Stop running simulation

```bash
docker-compose -f docker_tests/docker-compose-listener.yml down --remove-orphans
docker-compose -f docker-compose-test-simulation.yml down --remove-orphans
```

## Stop local RabbitMQ server

```bash
docker-compose -f rabbitmq/docker-compose-rabbitmq.yml down --remove-orphans
```
