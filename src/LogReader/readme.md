# LogReader

LogReader is a component of the Simces simulation platform. It is a part of the logging system. It is used to access the message database on a higher level. It provides a RESTful HTTP based API for accessing information about executed simulations, their messages and timeseries constructed from the message data. The API is further documented in [api.md](api.md). It also provides a simple web based user interface for making API queries available from the application root path e.g. if the LogReader is running on localhost port 8080 the ui is available on http:://localhost:8080.

## Implementation status

- get simulations: done 
- get simulation: done 
- get messages for simulation: done
- get simple timeseries: done 
- get complex timeseries: Time series creation code implemented, not tested. API not implemented. 

## Requirements

- python 3 (developed with version 3.7)
- MongoDB (developed with version 4.2)
- Docker and docker-compose (optional) 

## Installation and running

LogReader can be run with a local python installation and a MongoDB instance accessible from the local machine. It can also be run with Docker by using Docker-compose.

### Local usage

You probably want to use a virtual python environment:

    python -m venv .env
    . .env/bin/activate # unix
    .env\scripts\activate # windows

Install required python packages:

    pip install -r requirements.txt

LogReader is a [WSGI web application](https://wsgi.readthedocs.io/en/latest/index.html)
It can thus be run with any WSGI server. By default it uses [waitress](https://docs.pylonsproject.org/projects/waitress/en/stable/),
which works both on Windows and Unix based systems. To use this default option run LogReader with:

    python -m LogReader.app

By default the app listens on every available interface on port 8080. It tries to connect to a MongoDB instance running on localhost at the default MongoDB port 27017. There it uses a database named messages. The app logs information about each HTTP request and some additional informational messages but more verbose debug logging is also available. These defaults can be changed with the following environment variables:

- MONGODB_HOST: MongoDB server host name.
- MONGODB_PORT: MongoDB serverport. 
- MONGODB_DATABASE: MongoDB database name.
- MONGODB_USERNAME: User name for authentication to MongoDB.
- MONGODB_PASSWORD: Password for authentication to MongoDB.
- MONGODB_ADMIN: If set to true MongoDB authentication is done against the admin database. If set to false the "messages" database or the one given in MONGODB_DATABASE is used as the authentication source.
- MONGODB_TLS: If set to true TLS is used when connecting to MongoDB.
- MONGODB_TLS_ALLOW_INVALID_CERTIFICATES: When using TLS if set to true MongoDB server certificates are not validated.
- LOGREADER_HOST: LogReader listen address.
- LOGREADER_PORT: LogReader listen port.
- LOGREADER_DEBUG: Print more verbose log messages when the value of this variable is set to true.
- LOGREADER_ACCESS_LOGGING: Do not print access information about each request when this is set to false.

For running with another WSGI server the WSGI application is available in the api attribute of the LogReader.app module. So for example to run with Gunicorn:

    gunicorn LogReader.app:api

For experimenting with the API some test data can be inserted to the used MongoDB database with:

    python -m testLogReader.dataManager

This uses the same MongoDB connection information as the main app. This data can be removed with:

    python -m testLogReader.dataManager -d

NOTE: This drops the whole simulations and test message collection before inserting data and when removing test data.

The test data includes a couple simulations and some messages for the first simulation.

### Dokcer compose

Docker-compose can be used to launch Logreader and a MongoDB instance. First build the LogReader Docker image:

    docker-compose build

Then launch LogReader and MongoDB in the background:

    docker-compose up -d

LogReader listens on localhost port 8080 and MongoDB on localhost 27017. The test data can be inserted by running the data insertion commmand inside the LogReader container:

    docker exec -it logreader python -m testLogReader.dataManager

and test data can be removed with:

    docker exec -it logreader python -m testLogReader.dataManager -d

NOTE: This drops the whole simulations and test message collections before inserting data and when removing test data.

The system can be removed with:

    docker-compose down -v
    
Omit the -v option if you want to keep the MongoDB data contents for the next time. -v removes the docker volume used by mongodb.

The LogReader.env and mongodb.env files contain environment variables used by docker-compose for the containers.

## Developing

When developing [hupper](https://github.com/Pylons/hupper)
can be used to launch LogReader. When the code is then modified hupper automatically reloads the application:

    hupper -m LogReader.app 

Hupper is installed as part of the LogReader requirements.

### Overview

WSGI application is implemented with the [falcon](https://falcon.readthedocs.io/en/stable/)
web framework. MongoDB is used with the [Pymongo](https://pymongo.readthedocs.io/en/stable/) library.

The LogReader code is in the LogReader package. The following is a short overview of its contents:

- \_\_init\_\_.py: Initializes logging.
- app.py: Creates the falcon application including configuring its routes.
- utils.py: miscellaneous helper methods.
- db: Pakcage for dealing with MongoDB.
    - \_\_init\_\_.py: Initialises the DB connection.
    - simulations.py: Methods for querying simulations from the DB.
    - messages.py: Methods for querying messages for a simulation run from the DB.
- controllers: Contains falcon request handler classes.
    - simulations.py: Request handlers related to simulations.
    - messages.py: Request handlers related to messages.
    - timeSeries.py: Request handlers for time series.
    - static.py: Serves the web ui.
- services
    - timeSeries.py: Code related to creation of time series data from messages.  

### Testing

Testing code and test data is available in the testLogReader pakcage / directory. The testing code uses the build-in Python [unittest](https://docs.python.org/3.7/library/unittest.html) framework.
All tests can be executed with:

    python -m unittest

Tests from a particular module can be also executed for example:

    python -m unittest testLogReader.testSimulations

These tests require a running MongoDB instance. The tests will delete all existing data in the simulations and test messages collections. Connection information is given with the same environment variables as for LogReader itself. Tests can be also run with docker-compose. First build the logreader container which is the same container used when running LogReader:

    docker-compose build       

Then run tests using the testing compose file:

    docker-compose -f docker-compose-test.yml up
    
After the test output is complete quit with ctrl-c and remove the containers:

    docker-compose -f docker-compose-test.yml down
    
Note: MongoDB logging is disabled in this compose file.

There are four kinds of tests:

1. database tests: They test stuff in the LogReader.db package for example testLogrEader.testSimulations.
2. time series tests which test the time series creation code. They are located at testLogReader.testTimeSeries
3. controller tests: They test the request handlers using [Falcon's testing tools](https://falcon.readthedocs.io/en/stable/api/testing.html)
which simulate HTTP requests. For example testLogReader.testSimulationsApi.
4. integration tests: They start their own web server and test with real HTTP requests. They are located at testLogReader.testIntegration.

There is also the testLogReader.dataManager module which is used to insert and remove test data and which can also be run to insert the test data for experimenting with the API as described before. 

#### A note about time series tests

Most of the time series related tests in testLogReader.testTimeSeries and testLogReader.testTimeSeriesApi read their expected test results from files located at testLogReader/data. They also save the actual results they got to files at the same location which can help in comparing expected and actual test results. These tests are also executed multiple times with different parameters called test scenarios. Thus for each test there are multiple expected result and actual result files named after the test and test scenario. Adding a new scenario can then be quite easy: first the tests are executed without expected results. Actual results can then be checked manually and if they are correct the file can be renamed to be the expected result file.  