# LogWriter

Platform component for the simulation platform that listens to all the messages in the message bus and writes them to a Mongo database.

The messages stored in the database can be fetched using the [LogReader](https://github.com/simcesplatform/logreader) component.

## Cloning the repository

```bash
git clone --recursive https://github.com/simcesplatform/LogWriter.git
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

## Start the Log Writer

First configure the connection details for the RabbitMQ message bus, for the MongoDB database, and simulation id in the file [`log_writer.env`](log_writer.env). Instructions on how to setup a local RabbitMQ server can be found at [https://github.com/simcesplatform/simulation-manager#start-local-rabbitmq-server](https://github.com/simcesplatform/simulation-manager#start-local-rabbitmq-server) and instructions for starting a local MongoDB instance can be found at [mongodb](mongodb/README.md).

```bash
docker-compose -f docker-compose-log-writer.yml up --build
```

For running the Log Writer in the background add `--detach` to the end of the previous command.
