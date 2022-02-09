## API overview 

LogReader implements the HTTP based API described below. LogReader also offers a simple web browser based interface for the API available from the application root path for example http://localhost:8080/. The API offers the following features:

- Get list of simulations there are messages for.
- Get information about a single simulation by its id.
- Get messages for a simulation. Messages can be filtered in various ways such as topic and source process.
- Get invalid messages published during a simulation run.
- Create a json or csv time series from attribute values  in messages.     

This documentation assumes that the reader is familiar with the general messaging concepts of the simulation platform such as epochs and the various message attribute value blocks like TimeseriesBlock and QuantityBlock. The following notation is used to document request parameters and members of JSON objects in response and request bodies:

- name (data type, parameter type, required): description

- name: parameter or json member name
- data type: value data type such as string, integer or ISO datetime
- parameter type: Only for request parameters either in the URL path or in the URL query parameters
- required: Indicates that the parameter or JSON member is required. If this keyword is not present the parameter or member is optional. This is not used with response JSON where all members can be assumed to be present.
- description: Explain the purpose of the parameter or JSON member.

The API is available from the application root path. So for example if LogReader is running on localhost port 8080 the URL to get all simulations would be http://localhost:8080/simulations. The examples for each API endpoint use localhost port 8080 in example request URLs. Note that the message structures and topics used in the examples may not always match the actual topics and structures defined for the platfor. The examples are based on test data included with LogReader which can be imported to the LogReader database. This allows trying out the API. See the LogReader readme for instructions how to use the test data.
   
## Get simulations

method: GET  
path: /simulations

Returns a list of simulation runs the message database has messages for.

### Request parameters

- fromDate (ISO datetime, query): Return simulation runs which have started on or after the given date.
- toDate (ISO datetime, query) Return simulation runs that have been started before the given date.

### Response

List of simulation runs with the following information available about every run.

- SimulationId (string): The id of the simulation.
- Name (string): A human friendly name for the simulation.
- Description (string): A longer description of the simulation run meant for humans.
- StartTime (ISO datetime): The real world start time of the simulation run.
- EndTime (ISO datetime): The real world end time of the simulation run.
- Epochs (integer): Number of epochs in the simulation run.
- Processes (string[]): List of names of processes participating in the simulation run.

### Example

Get list of simulations executed on or after 3th of June 2020 at 10:00.

#### Request

    http://localhost:8080/simulations?fromDate=2020-06-03T10:00:00Z

#### Response

```
[
  {
    "Description": "This is a test simulation without example messages.",
    "EndTime": "2020-06-03T10:05:52.345000Z",
    "Epochs": 40,
    "Name": "test simulation 2",
    "Processes": [
      "simulationManager",
      "weatherDivinity",
      "solarPlant1",
      "battery1",
      "battery2"
    ],
    "SimulationId": "2020-06-03T10:01:52.345Z",
    "StartTime": "2020-06-03T10:01:52.345000Z"
  },
  {
    "Description": "This is a test simulation without example messages.",
    "EndTime": "2020-06-03T04:15:52.345000Z",
    "Epochs": 100,
    "Name": "test simulation 2",
    "Processes": [
      "simulationManager",
      "weatherDivinity",
      "solarPlant1",
      "battery1"
    ],
    "SimulationId": "2020-06-04T04:01:52.345Z",
    "StartTime": "2020-06-04T04:01:52.345000Z"
  }
]
```

## Get simulation

method: GET  
path: /simulations/{simulationId}

Returns general information about the given simulation run.

### Request parameters

- simulationId (string, path, required): The id of a simulation run.

### Response

Information about the given simulation run with the same contents as in each get simulations response item.

### Example

Get information about simulation with id 2020-06-03T04:01:52.345Z.

#### Request

    http://localhost:8080/simulations/2020-06-03T04:01:52.345Z

#### Response

```
{
  "Description": "This is a test simulation with some example messages.",
  "EndTime": "2020-06-03T04:11:52.345000Z",
  "Epochs": 50,
  "Name": "test simulation 1",
  "Processes": [
    "simulationManager",
    "weatherDivinity",
    "solarPlant1",
    "battery1",
    "battery2",
    "battery3"
  ],
  "SimulationId": "2020-06-03T04:01:52.345Z",
  "StartTime": "2020-06-03T04:01:52.345000Z"
}
```

## Get messages for simulation run

method: GET  
path: /simulations/{simulationId}/messages

Returns messages from the given simulation run. Without parameters returns all messages. Parameters allow filtering in various ways.

### Request parameters

- simulationId (string, path, required): Id of the simulation run messages are fetched from.
- startEpoch (integer, query): Return messages published on or after the given epoch. Not applicable if epoch, fromSimDate or toSimDate are used.
- endEpoch (integer, query): Return messages published on or before the given epoch. Not applicable if the epoch, fromSimDate or toSimDate are used.
- epoch (integer, query): return messages published during the given epoch. Not applicable if fromSimDate, toSimDate endEpoch or startEpoch are used.
- fromSimDate (ISO datetime, query): Return messages starting from the epoch that includes the given date. Not applicable if startEpoch, epoch or endEpoch are used.
- toSimDate (ISO datetime, query): Return messages published before or on  the epoch that includes the given date. Not applicable if startEpoch, epoch or endEpoch are used.
- process (string, query): Return messages that have been published by the given processes i.e. messages whose source is the given process. Value is a comma separated list of process ids.
- topic (string, query): Return messages published to the given topic. Supports the same notation that is used when subscribing to the topics i.e. the same wildcard mechanism including the * and # characters.
- onlyWarnings: (boolean, query): If true only messages that include warnings are returned. If false messages with and without warnings are both returned. False is the default behaviour if this parameter is not used.

### Response

List of messages as they have been saved into the database including the message metadata. The messages will be sorted in ascending order by timestamp.

### Example

Get messages that process solarPlant1 has published to topic energy.production.solar on or before epoch 2 for simulation with id 2020-06-03T04:01:52.345Z.

#### Request

    http://localhost:8080/simulations/2020-06-03T04:01:52.345Z/messages?process=solarPlant1&topic=energy.production.solar&endEpoch=2

#### Response

```
[
  {
    "EpochNumber": 1,
    "MessageId": "solarPlant1-1",
    "ReactivePower": {
      "UnitOfMeasure": "kV.A{r}",
      "Value": 0.2
    },
    "RealPower": {
      "UnitOfMeasure": "kW",
      "Value": 5
    },
    "SimulationId": "2020-06-03T04:01:52.345Z",
    "SourceProcessId": "solarPlant1",
    "Timestamp": "2020-06-03T04:01:56Z",
    "Topic": "energy.production.solar",
    "Type": "ControlState",
    "bus": "bus1"
  },
  {
    "EpochNumber": 2,
    "MessageId": "solarPlant1-2",
    "ReactivePower": {
      "UnitOfMeasure": "kV.A{r}",
      "Value": 0.5
    },
    "RealPower": {
      "UnitOfMeasure": "kW",
      "Value": 8
    },
    "SimulationId": "2020-06-03T04:01:52.345Z",
    "SourceProcessId": "solarPlant1",
    "Timestamp": "2020-06-03T04:02:56Z",
    "Topic": "energy.production.solar",
    "Type": "ControlState",
    "bus": "bus1"
  }
]
```

## Get invalid messages for simulation run

method: GET  
path: /simulations/{simulationId}/messages/invalid

Returns invalid messages from the given simulation run. This is intended for debugging simulation issues. A normal simulation run should not contain invalid messages. 

### Request parameters

- simulationId (string, path, required): Id of the simulation run messages are fetched from.
- topic (string, query): Return invalid messages published to the given topic. Supports the same notation that is used when subscribing to the topics i.e. the same wildcard mechanism including the * and # characters.

### Response

List of invalid messages. The messages will be sorted in ascending order by timestamp. The following attributes can be  available for each message:

- Timestamp: Timestamp from the message if the message had a valid timestamp. Otherwise this is a timestamp added when the message was stored to the database.
- Topic: The topic the message was published to.
- InvalidMessage: The message itself if it was valid json.
- InvalidJsonMessage: Message as a string if the message could not be parsed as json.   

### Example

Get all invalid messages for simulation with id 2020-06-03T04:01:52.345Z. 

#### Request

    http://localhost:8080/simulations/2020-06-03T04:01:52.345Z/messages/invalid

#### Response

```
[
  {
    "Timestamp": "2020-06-03T04:01:53Z",
    "Topic": "Epoch",
    "InvalidMessage": {
      "EndTime": "2020-06-03T14:00:00Z",
      "EpochNumber": 1,
      "MessageId": "SimulationManager-2",
      "SourceProcessId": "SimulationManager",
      "StartTime": "2020-06-03T13:00:00Z",
      "Timestamp": "2020-06-03T04:01:53Z",
      "Type": "Epoch"
    }
  },
  {
    "Timestamp": "2020-06-03T04:01:54Z",
    "Topic": "Status.Ready",
    "InvalidJsonMessage": "Ready"
  }
]
```

NOTE: The first message is considered invalid since it is missing the SimulationId attribute. The second message is invalid since it is just a text string containing the word Ready.

## Get simple timeseries for simulation

method: GET  
path: /simulations/{simulationId}/timeseries

Returns timeseries data constructed from values of given attributes of messages that meet the given time, topic and process based filtering conditions.

### Request parameters

Same parameters as in get simulation messages are used except onlyWarnings. In addition the following parameters are used:

- attrs (string, query, required) Comma separated list of names of message attributes whose values are suitable for time series and which are then included to the timeseries response. It is possible to refer deeper into the message structure using the dot notation for example foo.bar.
- format (string, query): Determines the response format. Possible values are csv and json. If this parameter is not used json is used as the default value.

The following kinds of message attribute values are suitable for time series and can be refered to in the attrs query parameter:

- Plain number, string or boolean values.
- QuantityBlocks in which case the Value part of the QuantityBlock is added to the created time series.
- TimeseriesBlock if only the attribute containing a time series block is referred to all attributes in the time series are included. It is also possible to refer to a particular attribute inside the time series block to only include it to the time series to be created.

### Response

json

A JSON object with the following members:

- TimeIndex (timeIndex[]): List of time index objects that indicate the timestamp for the data. For example if a timeindex object is the fifth item in the timeindex list then it has the time for the fifth value in each attribute values list. If there is no value for an attribute for a corresponding timeIndex value, the value will be nul.
- {topic} (topicData): For each topic there is timeseries data a member named after the topic. The value is a topicDATa object.

timeIndex object

- timestamp (ISO datetime): Indicates the simulation time for the corresponding data. 
- epoch (integer): Indicates the epoch for the message the corresponding data is from. 

TopicData object

- {processName} (attributeValues): For each process the timeseries has values for in the given topic a member where processName is replaced with the id of the process. The value is then attributeValues object.

attributeValues object

- {attr}: For each message attribute a member where attr is replaced with the attribute name. The value is then list of attribute values from the messages or another attributeValues object if the actual values are deeper in the message structure.

csv

csv data with the following column titles and colun value data types

- epoch (integer): Number of the epoch for the message the data in the row is from.
- timestamp (iso datetime): Simulation timestamp for the data in the row.
- {topic}:{processname}.{attr}: For each topic, process and message attribute the timeseries contains data for there is a column for it with a title consisting of the topic, process and attribute names. Attribute can consist of multiple parts separated by a period. If there is no data for the row at a certain time then the column has an empty cell.

### Example 1

Create a timeseries in the json format containing the real power and reactive power QuantityBlock values from  messages that process solarPlant1 has published to topic energy.production.solar on or before epoch 2 for simulation with id 2020-06-03T04:01:52.345Z.
The messages which are the source for this time series are shown in the response of example for Get messages for simulation. 

#### Request

    http://localhost:8080/simulations/2020-06-03T04:01:52.345Z/timeseries?process=solarPlant1&topic=energy.production.solar&endEpoch=2&attrs=RealPower,ReactivePower
    
#### Response 

```
{
  "TimeIndex": [
    {
      "epoch": 1,
      "timestamp": "2020-06-03T13:00:00Z"
    },
    {
      "epoch": 2,
      "timestamp": "2020-06-03T14:00:00Z"
    }
  ],
  "energy.production.solar": {
    "solarPlant1": {
      "ReactivePower": [
        0.2,
        0.5
      ],
      "RealPower": [
        5,
        8
      ]
    }
  }
}
```

### Example 2

Same as example 1 except the time series should be in the csv format.

#### Request

    http://localhost:8080/simulations/2020-06-03T04:01:52.345Z/timeseries?process=solarPlant1&topic=energy.production.solar&endEpoch=2&attrs=RealPower,ReactivePower&format=csv

#### Response

```
epoch;timestamp;energy.production.solar:solarPlant1.RealPower;energy.production.solar:solarPlant1.ReactivePower
1;2020-06-03T13:00:00Z;5.0;0.2
2;2020-06-03T14:00:00Z;8.0;0.5
```

### Example 3

Create a time series in the json format containing the chargePercentage values from the batteryState timeseries block from messages published to the energy.storage.state topic by processes battery1 and battery2 for simulation with id 2020-06-03T04:01:52.345Z. The published messages look like the following:

```
{
  "EpochNumber": 1,
  "MessageId": "battery1-1",
  "SimulationId": "2020-06-03T04:01:52.345Z",
  "SourceProcessId": "battery1",
  "Timestamp": "2020-06-03T04:01:56Z",
  "Topic": "energy.storage.state",
  "Type": "Result",
  "batteryState": {
    "Series": {
      "capacity": {
        "UnitOfMeasure": "kWh",
        "Values": [
          300,
          280
        ]
      },
      "chargePercentage": {
        "UnitOfMeasure": "%",
        "Values": [
          90,
          88
        ]
      }
    },
    "TimeIndex": [
      "2020-06-03T13:00:00Z",
      "2020-06-03T13:30:00Z"
    ]
  }
}
```

#### Request

    http://localhost:8080/simulations/2020-06-03T04:01:52.345Z/timeseries?process=battery1,battery2&topic=energy.storage.state&attrs=batteryState.chargePercentage
    
#### Response

```  
{
  "TimeIndex": [
    {
      "epoch": 1,
      "timestamp": "2020-06-03T13:00:00Z"
    },
    {
      "epoch": 1,
      "timestamp": "2020-06-03T13:30:00Z"
    },
    {
      "epoch": 2,
      "timestamp": "2020-06-03T14:00:00Z"
    },
    {
      "epoch": 2,
      "timestamp": "2020-06-03T14:30:00Z"
    }
  ],
  "energy.storage.state": {
    "battery1": {
      "batteryState": {
        "chargePercentage": [
          90,
          88,
          87,
          91
        ]
      }
    },
    "battery2": {
      "batteryState": {
        "chargePercentage": [
          40,
          42,
          45,
          48
        ]
      }
    }
  }
}
```

### Example 4

Same as example 3 except timeseries is created in the csv format.

#### Request

    http://localhost:8080/simulations/2020-06-03T04:01:52.345Z/timeseries?process=battery1,battery2&topic=energy.storage.state&attrs=batteryState.chargePercentage&format=csv
    
#### Response

```
epoch;timestamp;energy.storage.state:battery1.batteryState.chargePercentage;energy.storage.state:battery2.batteryState.chargePercentage
1;2020-06-03T13:00:00Z;90;40
1;2020-06-03T13:30:00Z;88;42
2;2020-06-03T14:00:00Z;87;45
2;2020-06-03T14:30:00Z;91;48
``` 