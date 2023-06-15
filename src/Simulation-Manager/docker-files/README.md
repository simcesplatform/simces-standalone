# Docker compose file for full simulation setup

Includes SimulationManager, 5 Dummy components, LogWriter, and LogReader as well as local Mongo database and RabbitMQ message bus server.

Requires an environment with Bash, Docker, and Docker Compose installed.

## Setup

The docker-compose file assumes that the LogReader repository is at folder `logreader`, LogWriter repository is at folder `logwriter`, and SimulationManager repository is at `simulation-manager`.

1. Edit environment variable files [`env/mongodb.env`](env/mongodb.env), [`env/mongo_express.env`](env/mongo_express.env), and [`env/components_mongodb.env`](env/components_mongodb.env) to setup the username and password for MongoDB.

2. Edit environment variable files [`env/rabbitmq.env`](env/rabbitmq.env) and [`env/components_rabbitmq.env`](env/components_rabbitmq.env) to setup the username and password for RabbitMQ.

3. Edit logging level at the environment variable file [`env/components_common.env`](env/components_common.env).

4. Edit the simulation manager behavior (for example the maximum number of epochs) at the environment variable file [`env/manager.env`](env/manager.env).

5. Edit the dummy component behavior (for example the wait time before response) at the environment variable file [`env/dummy.env`](env/dummy.env).

6. Copy the script [`start_simulation.sh`](start_simulation.sh), the docker-compose file, [`docker-compose-env.yml`](docker-compose-env.yml), and the entire [`env`](env) folder to the root folder of the different repositories.

    ```bash
    cp -r start_simulation.sh docker-compose-full.yml env ../..
    ```

## Starting the simulation

At the location of the copied starting script run:

```bash
source start_simulation.sh
```

The simulation will run in the background. The logging system, MongoDB and RabbitMQ will remain running even after the simulation is finished. However, the simulation manager and the dummy components are closed at the simulation end.

New simulation can be started by running the starting script again.
