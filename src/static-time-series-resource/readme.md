# Static time series resource

A simulation platform component used to simulate simple loads and generators whose published states are determined by a file containing a simple time series of attribute values for each epoch.

## Requirements

- python 3.7
- pip for installing requirements

Install requirements:

```bash
# optional create a virtual environment:
python3 -m venv .env
# activate it
. .env/bin/activate # *nix
.env\scripts\activate # windows.
# install required packages
pip install -r requirements.txt
```

## Usage

The component is based on the AbstractSimulationCompoment class from the [simulation-tools](https://github.com/simcesplatform/simulation-tools)
 repository. It is configured via environment variables which include common variables for all AbstractSimulationComponent subclasses such as rabbitmq connection and component name. Environment variables specific to this component are listed below:
 
- RESOURCE_STATE_TOPIC (optional): The upper level topic under whose subtopics the resource states are published. If this environment variable is not present ResourceState is used.
- RESOURCE_TYPE (required): Type of this resource. Accepted values are Generator or Load.
- RESOURCE_STATE_CSV_FILE (required): Location of the csv file which contains the resource state information used in the simulation. Relative file paths are in relation to the current working directory.
- RESOURCE_STATE_CSV_DELIMITER (optional): Delimiter used in the csv file. The default is ,

The csv file should contain columns named after the ResourceState message attributes: RealPower, ReactivePower, CustomerId and Node. The Node column is optional. Each row containing values will then represent data for one epoch. There should be at least as many data rows as there will be epochs. 

The component can be launched with:

    python -m static_time_series_resource.component

Docker can be used with the included docker file

## Tests

The included unittests can be executed with:

    python -m unittest

This requires RabbitMQ connection information provided via environment variables as required by the AbstractSimulationComponent class. Tests can also be executed with docker compose:

    docker-compose -f docker-compose-test.yml up --build
    
After executing tests exit with ctrl-c and remove the test environment:

    docker-compose -f docker-compose-test.yml down -v