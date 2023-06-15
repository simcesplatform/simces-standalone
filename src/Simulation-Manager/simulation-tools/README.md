# Simulation Tools

Tools for working with simulation messages and with the RabbitMQ message bus in Python.

<!-- no toc -->
- [Contents](#contents)
    - [Message classes](#message-classes)
    - [Message client class](#message-client-class)
    - [Abstract simulation component](#abstract-simulation-component)
    - [Tools for handling datetime values](#tools-for-handling-datetime-values)
    - [Callback class for transforming incoming messages to message objects](#callback-class-for-transforming-incoming-messages-to-message-objects)
    - [Timer class for handling timed tasks](#timer-class-for-handling-timed-tasks)
    - [MongoDB client](#mongodb-client)
    - [Miscellaneous tools](#miscellaneous-tools)
- [How to include simulation-tools to your own project](#how-to-include-simulation-tools-to-your-own-project)
- [How to add support for a new message type as a Python class](#how-to-add-support-for-a-new-message-type-as-a-python-class)
- [General instructions for creating a new simulation component](#general-instructions-for-creating-a-new-simulation-component)
- [How to use the example code](#how-to-use-the-example-code)
- [Things not yet covered here](#things-not-yet-covered-here)
- [Run unit tests for the simulation-tools library](#run-unit-tests-for-the-simulation-tools-library)
- [Clean up after running the tests](#clean-up-after-running-the-tests)

## Contents

### Message classes

[`tools/messages.py`](tools/messages.py)

- Contains message classes that can be used to handle messages in the simulation platform.
- The message classes contains some validation for the message attribute values and the creation of message objects will fail, by throwing an exception, if some attribute has an invalid value.
- The timestamps for the message objects are generated automatically if the timestamp is not explicitly given.
- The actual implementations for the message classes can be found in the folder `tools/message/` but the main file can be used to simplify import calls.
    - For example, `from tools.messages import StatusMessage` is equivalent to `from tools.message.status import StatusMessage`
- Currently supported message types (more supported message types can be found from [domain-messages](https://github.com/simcesplatform/domain-messages) repository):
    - `BaseMessage` (defined in [tools/message/abstract.py](tools/message/abstract.py))
        - Message object that contains only Type, SimulationId and Timestamp
        - Log Writer can handle any message that contains at least these three attributes.
        - `message_type` property corresponds to the JSON attribute Type
        - `simulation_id` property corresponds to the JSON attribute SimulationId
        - `timestamp` property corresponds to the JSON attribute Timestamp
    - `AbstractMessage` (defined in [tools/message/abstract.py](tools/message/abstract.py))
        - Child class of BaseMessage
        - Adds SourceProcessId and MessageId attributes
        - Definition: [AbstractMessage](https://simcesplatform.github.io/core_msg-abstractmessage/)
        - `source_process_id` property corresponds to the JSON attribute SourceProcessId
        - `message_id` property corresponds to the JSON attribute MessageId
    - `AbstractResultMessage` (defined in [tools/message/abstract.py](tools/message/abstract.py))
        - Child class of AbstractMessage
        - Adds EpochNumber, LastUpdatedInEpoch, TriggeringMessageIds and Warnings
        - Definition [AbstractResult](https://simcesplatform.github.io/core_msg-abstractresult/)
        - `epoch_number` property corresponds to the JSON attribute EpochNumber
        - `last_updated_in_epoch` property corresponds to the JSON attribute LastUpdatedInEpoch
        - `triggering_message_ids` property corresponds to the JSON attribute TriggeringMessageIds
        - `warnings` property corresponds to the JSON attribute Warnings
    - `SimulationStateMessage` (defined in [tools/message/simulation_state.py](tools/message/simulation_state.py))
        - Child class of AbstractMessage
        - Adds SimulationState, Name and Description
        - Definition: [SimState](https://simcesplatform.github.io/core_msg-simstate)
        - `simulation_state` property corresponds to the JSON attribute SimulationState
        - `name` property corresponds to the JSON attribute Name
        - `Description` property corresponds to the JSON attribute Description
    - `EpochMessage` (defined in [tools/message/epoch.py](tools/message/epoch.py))
        - Child class of AbstractResultMessage
        - Adds StartTime and EndTime
        - Definition: [Epoch](https://simcesplatform.github.io/core_msg-epoch/)
        - `start_time` property corresponds to the JSON attribute StartTime
        - `end_time` property corresponds to the JSON attribute EndTime
    - `StatusMessage` (defined in [tools/message/status.py](tools/message/status.py))
        - Child class of AbstractResultMessage
        - Adds Value and Description
        - Definition: [Status](https://simcesplatform.github.io/core_msg-status/)
        - `value` property corresponds to the JSON attribute Value
        - `description` property corresponds to the JSON attribute Description
    - `ResultMessage`
        - Child class of AbstractResultMessage
        - Can add any user chosen attributes but does not provide any checks for validity of the attribute values.
        - Can be useful for testing but should not be used in production ready components.
    - `GeneralMessage`
        - Child class of BaseMessage
        - Similar to ResultMessage but only requires the SimulationId and Timestamp attributes
    - `ExampleMessage`
        - Child class of AbstractResult
        - Not to be used in the actual simulation components but made as an example for a message type that uses [Quantity block](https://simcesplatform.github.io/core_block-quantity/), [Quantity array block](https://simcesplatform.github.io/core_block-quantity-array/) and [Time series block](https://simcesplatform.github.io/core_block-time-series/) as the attribute value types.
- Common methods for all message classes:
    - `__init__` (constructor)
        - Takes in all the arguments as defined in the documentation pages for the message.
        - Any additional arguments that are not part of the message definition are ignored.
        - Does some validity checks for the attribute values and throws an exception if at least one value was found to be invalid. For example, the EpochNumber must be a non-negative integer.
    - `from_json` (class method)
        - Returns a new message instance if the `json_message` contains valid values for the message type. Returns None, if there is at least one invalid value or missing required attribute.
        - Can be used instead of the constructor to avoid exception handling. However, direct use of the constructor is faster during runtime.
    - `json`
        - Returns the message instance as a Python dictionary.
    - `bytes`
        - Returns the message instance in UTF-8 encoded bytes format.
    - property getters and setters for each message attribute
    - `register_to_factory` (class method)
        - Factory registration method to allow the general message handling utils to know about new message class types.
- Class for QuantityBlock that can be used as a value for a message attribute
    - QuantityBlock is constructed similarly to the message classes
    - Supports Value and UnitOfMeasure attributes
    - Definition: [Quantity block](https://simcesplatform.github.io/core_block-quantity/)
    - `value` property corresponds to the JSON attribute Value
    - `unit_of_measure` property corresponds to the JSON attribute UnitOfMeasure
- Class for TimeSeriesBlock that can be used as a value for a message attribute
    - TimeSeriesBlock is constructed similarly to the message classes
    - Supports TimeIndex and Series attributes
    - Definition: [Time series block](https://simcesplatform.github.io/core_block-time-series/)
    - `time_index` property corresponds to the JSON attribute TimeIndex
    - `series` property corresponds to the JSON attribute Series
    - A separate class ValueArrayBlock that can be used as a value for the value series inside a Time series block
        - Supports UnitOfMeasure and Values attributes
        - `values` property corresponds to the JSON attribute Values
        - `unit_of_measure` property corresponds to the JSON attribute UnitOfMeasure
- Class for QuantityArrayBlock that can be used as a value for a message attribute
    - QuantityArrayBlock is child class of ValueArrayBlock that only allows float values
    - Supports Values and UnitOfMeasure attributes
    - Definition: [Quantity array block](https://simcesplatform.github.io/core_block-quantity-array/)
    - `values` property corresponds to the JSON attribute Values
    - `unit_of_measure` property corresponds to the JSON attribute UnitOfMeasure
- Implementation for all the block types are found at [tools/message/block.py](tools/message/block.py)
- MessageGenerator class for creating a series message of messages that have common SimulationId and SourceProcessId.
    - The message generator class implementation can be found at [tools/message/generator.py](tools/message/generator.py)
    - `__init__` (constructor)
        - `simulation_id`
            - The simulation id for the messages.
        - `source_process_id`
            - The source process id, i.e. the component name for the messages.
    - `get_message`
        - Returns a new message instance or throws an appropriate exception if some attributes were invalid or missing.
            - `message_class`
                - The message class name for the new message instance.
            - `**kwargs`
                - All the appropriate attributes for the message. Type, SimulationId, SourceProcessId, MessageId and Timestamp are not required.
    - Special methods for generating specific message types are available.
        - `get_epoch_message`
            - Returns an epoch message.
        - `get_simulation_state_message`
            - Returns a simulation state message.
        - `get_status_ready_message`
            - Returns a status ready message.
        - `get_status_error_message`
            - Returns a status error message.
- Note: the current implementation of the message classes is quite verbose. The implementation might be changed in the future in order to make it easier to create additional message classes. However, the interface, i.e. how the messages are created or used, will not change.

### Message client class

[`tools/clients.py`](tools/clients.py)

- Contains RabbitmqClient class that can be used as a client to send and receive messages to and from a RabbitMQ message bus.
- Uses the asynchronous RabbitMQ library aio_pika.
- One client can handle messaging only for one exchange. Separate clients are needed if more than one exchanges are used.
- Methods for RabbitmqClient:
    - `__init__` (constructor):
        - Used for creating a new client instance with the given parameters.
        - `host`
            - the host name for the RabbitMQ server
        - `port`
            - the port number for the RabbitMQ server
        - `login`
            - username for access to the RabbitMQ server
        - `password`
            - password for access to the RabbitMQ server
        - `ssl`
            - whether to use SSL connection to the RabbitMQ server
        - `ssl_version`
            - the SSL version parameter for the SSL connection, ignored if ssl is False
        - `exchange`
            - the name for the exchange used by the client
        - `exchange_autodelete`
            - whether to automatically delete the exchange after use
        - `exchange_durable`
            - whether to setup the exchange to survive message bus restarts
    - `add_listener`
        - Used for adding a message listener for the given topic(s).
        - `topic_names`
            - Either a single topic name or a list of topic names
        - `callback_function`
            - The function which will called when new message is received.
            - The callback function must be awaitable (async keyword) and it must callable with two parameters: the message object and the topic name.
    - `send_message`
        - Used for sending a new message to a given topic.
        - `topic_name`
            - The topic to be used when sending the message
        - `message_bytes`
            - The message in UTF-8 encoded bytes format. The message objects have `bytes()`-method for this. General string can be converted to bytes format with: `bytes(<string_variable>, "UTF-8")`
    - `close`
        - Used for closing the message bus connection.
        - Should always be called before exiting the program.

### Abstract simulation component

[`tools/components.py`](tools/components.py)

- Contains AbstractSimulationComponent that can be used as base class when creating new simulation component.
- Uses tools.clients.RabbitmqClient for the message bus communication.
- Contains the base workflow common for any simulation component.
    - Sends Status ready message after receiving SimState running message.
        - If there has been an initialization error, sends Status error message instead.
    - Stops the component after receiving SimState stopped message.
    - Provides functions that user can overwrite to create new components for a specific use cases.
    - Sends Status ready message automatically after the component is finished with the current epoch.
    - Methods for AbstractSimulationComponent:
        - `__init__` (constructor)
            - `simulation_id`
                - The simulation id for the simulation run
            - `component_name`
                - The component name, i.e. the source process id, for the simulation run
            - `other_topics`
                - A list of topics that the components wants to listen to (in addition to the Epoch and SimState topics)
            - The RabbitMQ connection parameters can be either given as constructor parameters or taken from environmental variables.
            - Also, all other parameters can be given as environmental variables. See the source code [components.py (line 38)](tools/components.py) for detailed information about the parameters and the corresponding environmental variables and their default values.
        - `start`
            - Starts the component including setting up the message bus topic listeners.
        - `stop`
            - Stops the component including closing the message bus connection.
        - `clear_epoch_variables`
            - Clears and initializes all the variables that are used to store received data within each epoch.
            - The function is called automatically after receiving an Epoch message for a new epoch.
        - `general_message_handler`
            - Should be overwritten when creating new component.
            - Should handle all received messages except SimState and Epoch messages.
            - `message_object`
                - The received message object or a dictionary containing the message in cases where there was no message class available for the message type.
            - `message_routing_key`
                - The topic name for the received message
        - `all_messages_received_for_epoch`
            - Should be overwritten when creating new component.
            - Should check that all the messages required to start calculations for the current epoch have been received.
            - Checking for a new Epoch message as well as for the simulation state is done automatically by AbstractSimulationComponent in the method ready_for_new_epoch.
            - Should return True, if the component is ready to handle the current epoch. Otherwise, should return False.
        - `ready_for_new_epoch`
            - Checks if the component is ready to do calculations for the current epoch. Returns True if the component is ready and otherwise return False.
            - Uses a call to the method all_messages_received_for_epoch to determine whether all necessary information is available for the epoch calculations.
            - Usually no modifications are needed for this and it is automatically called by the start_epoch method.
        - `process_epoch`
            - Should be overwritten when creating new component.
            - Should do the calculations for the current epoch.
            - Should send all the appropriate result messages to the message bus.
            - Should return True, if the component is finished with current epoch. Otherwise, should return False.
        - `start_epoch`
            - Checks if the component is ready to do the calculations for the current epoch, using `ready_for_new_epoch`, and if that is the case calls `process_epoch`. If the `process_epoch` returns True, sends a Status ready message to the message bus.
            - Should be called whenever it is possible that the component is ready to proceed with the current epoch, I.e. usually after handling a received message in `general_message_handler`.
            - The function is called automatically after each Epoch message.
        - `send_error_message`
            - Sends an error message to the message bus.
            - Sets the component in an error state so that it will no longer participate in the simulation.
            - `description`
                - The description for the error

### Tools for handling datetime values

[`tools/datetime_tools.py`](tools/datetime_tools.py)

- Contains tools for handling datetime objects and strings.
- `get_utcnow_in_milliseconds`
    - Returns the current ISO 8601 format datetime string in UTC timezone.
- `to_iso_format_datetime_string`
    - `datetime_value`
        - A datetime value given either as a string or as a datetime object.
    - Returns the given datetime_value as a ISO 8601 formatted string in UTC timezone.
    - Returns None if the given string is not in an appropriate format.
- `to_utc_datetime_object`
    - `datetime_str`
        - A datetime given as a ISO 8601 formatted string
    - Returns the corresponding datetime object.

### Callback class for transforming incoming messages to message objects

[`tools/callbacks.py`](tools/callbacks.py)

- Contains MessageCallback class that can convert a message received from the message bus to a message object, e.g. EpochMessage, StatusMessage or some other message type.
- All message types that have been registered are recognized by the callback class.
    - The registering is done by using the `register_to_factory()` method as is mentioned in the instructions for creating a new message.
- Used also by `tools.clients.RabbitmqClient` when setting up topic listeners.

### Timer class for handling timed tasks

[`tools/timer.py`](tools/timer.py)

- Contains Timer class that can be used to setup timed tasks.
- The constructor requires at least 3 arguments:
    - `is_repeating`
        - True or False, whether the task is repeated or not. A repeating task will only end after calling the cancel() method.
    - `timeout`
        - The delay of the execution of the task in seconds. For repeating tasks this is the interval between repeated executions.
    - `callback`
        - The function that is called after timeout. The function must be awaitable and compatible with the other parameters given in this constructor.
    - Extra parameters that are given in the constructor will be passed on to the callback function.
- See the example code [examples/timer.py](examples/timer.py) for an example on how to use the Timer class for timed tasks.

### MongoDB client

[`tools/db_clients.py`](tools/db_clients.py)

- Contains a MongodbClient client that can be used to store messages to Mongo database.
- Currently contains mainly functionalities required by Log Writer.

### Miscellaneous tools

[`tools/tools.py`](tools/tools.py)

- Contains tools that can be used to fetch environmental variables and to setup a logger object that can output logging information both to a file and to the screen.

## How to include simulation-tools to your own project

NOTE: If you intend to use [domain-messages](https://github.com/simcesplatform/domain-messages)
you do not have to include simulation-tools separately since domain-messages already includes it.
Use the [instructions](https://github.com/simcesplatform/domain-messages/blob/master/README.md#how-to-include-domain-messages-to-your-own-project) at domain-messages instead of these when using domain-messages.

These instructions try to take into account the problems arising from the fact that the GitLab server uses self signed SSL certificate. Two optional ways of including simulation-tools are described here.

- Manual copy of the tools folder

    - The easiest way to get the most recent version of the library.
    - No easy way of checking if there are updates for the library code. For a work in progress library this is a significant downside.

    Installation instructions:
    - Clone the simulation-tools repository:

        ```bash
        git clone https://github.com/simcesplatform/simulation-tools.git
        ```

    - Copy the `tools` folder from simulation-tools repository manually to the root folder of your own Python project.
    - Start using the library. For example the RabbitMQ client class can be made available by using:

       ```python
       from tools.clients import RabbitmqClient
       ```

- Using simulation-tools as a Git submodule in your own Git repository
    - Allows an easy way to update to the newest version of the library.
    - Requires the use of Git repository (some kind of version control is always recommended when working source code).
    - Requires more initial setup than manual copying.
    - For example, simulation-manager repository is including the library as a Git submodule.

    Installation instructions:
    - In the root folder of your Git repository add simulation-tools as a Git submodule

        ```bash
        # run this from the root folder of your Git repository
        git submodule add -b master https://github.com/simcesplatform/simulation-tools.git
        git submodule init
        git submodule update --remote
        ```

    - The simulation-tools folder should now contain a copy of the simulation-tools repository with the library code found in the `simulation-tools/tools` folder. To enable similar way of importing library modules as is used in the library itself or when using the manual copy of the tools folder, the Python interpreter needs to be told of the location of the tools folder. One way to do this is to use the init code from simulation-tools:
        1. Copy the init folder from simulation-tools to the root folder of your code repository:

            ```bash
            # run this from the root folder of your Git repository
            cp -r simulation-tools/init .
            ```

        2. Include a line `import init` at the beginning of the Python source code file from where your program is started. E.g. if your program is started with `python master.py` or `python -m master` include the import init line at the `master.py` file before any imports from the simulation-tools library.
            - Another way to avoid modifying your source code would be to include the import init line in `__init__.py` file as has been used for example in the [Simulation Manager repository](https://github.com/simcesplatform/simulation-manager/tree/master/manager).
    - Start using the library. For example the RabbitMQ client class can be made available by using:

       ```python
       from tools.clients import RabbitmqClient
       ```

    - To update the simulation-tools library to the newest version, run:

        ```bash
        # run this from inside your Git repository (but not from the simulation-tools folder)
        git submodule update --remote
        ```

## How to add support for a new message type as a Python class

Assumption is that the new message type is based on AbstractResult message.

There are some examples available:

- The Python class for [Epoch](https://simcesplatform.github.io/core_msg-epoch/) message can be found at [tools/message/epoch.py](tools/message/epoch.py)
- The Python class for [Status](https://simcesplatform.github.io/core_msg-status/) message can be found at [tools/message/status.py](tools/message/status.py)
- The Python class for Example message type can be found at [tools/message/example.py](tools/message/example.py). This example message type is made as an example of a message that adds some attributes to the AbstractResult message type with some of the attributes using the [Quantity block](https://simcesplatform.github.io/core_block-quantity/) or [Time series block](https://simcesplatform.github.io/core_block-time-series/) as the attribute values.

A template for a new message type is given at [`message_template.txt`](message_template.txt).

- The current implementation of the message classes is quite verbose but a template is provided to make it easier for the development of new message classes.
- All `<message type>`, `<property name 1>`, ... should be replaced with the appropriate names for the new message. For example `<message type>` for a NetworkState.Current message could be NetworkStateCurrentMessage.
- Attributes containing [Quantity blocks](https://simcesplatform.github.io/core_block-quantity/) as attributes have special support. However, no such support exists yet for [Quantity array block](https://simcesplatform.github.io/core_block-quantity-array/) or [Time series block](https://simcesplatform.github.io/core_block-time-series/).
- Existing message classes can be used as examples when implementing new message classes.
- Overview of what is required from a new message class for it to be compatible with the existing message classes:
    - Set the class constants `CLASS_MESSAGE_TYPE`, `MESSAGE_TYPE_CHECK`, `MESSAGE_ATTRIBUTES`, `OPTIONAL_ATTRIBUTES`, `QUANTITY_BLOCK_ATTRIBUTES`, `TIMESERIES_BLOCK_ATTRIBUTES`, `MESSAGE_ATTRIBUTES_FULL`, `OPTIONAL_ATTRIBUTES_FULL`, `QUANTITY_BLOCK_ATTRIBUTES_FULL` and `TIMESERIES_BLOCK_ATTRIBUTES_FULL` with the instructions given in the template.
    - Add a property getter for each new attribute in the message (those attributes that don't belong to [AbstractResult](https://simcesplatform.github.io/core_msg-abstractresult/)).
    - Add a property setter for each new attribute in the message (those attributes that don't belong to [AbstractResult](https://simcesplatform.github.io/core_msg-abstractresult/)).
    - Add a check function (with a name of `"_check_<property name>"` for each property that checks the validity of the given value. This can be very general in some cases. For example, "isinstance(value, str) and len(value) > 0" would ensure that "value" is a non-empty string.
    - Add a new implementation for the equality check method `"__eq__"`.
    - Add a new implementation for the "from_json" method. This is only for the return value type for the use of Python linters, not for any actual additional functionality.
    - Add a call to the `register_to_factory` method after the message class definition.

## General instructions for creating a new simulation component

When implementing a new simulation component in Python it is advisable to try to use the abstract simulation component class as the base class and implement the new simulation component as its child class. Some of the general workflow required from a component participating in a simulation run has already been implemented for the abstract class. The already implemented simulation components can be used as an example for using the abstract component as a base. Some general instructions are given here. There is also a template file, [examples/component_template.py](examples/component_template.py), that can be used as a starting point when implementing a new component.

- Import the abstract component class to the project: `from tools.components import AbstractSimulationComponent`
- Make a new class that is a child of the abstract class: `class MyComponent(AbstractSimulationComponent)`
- Overwrite the constructor, `__init__`
    - Add new arguments as needed. Remember to call the parent class constructor with the appropriate parameters at the beginning of the new constructor: `super().__init__(<abstract_component_parameters>)`
    - Add any initialization needed code to the new constructor. This includes initialization of any new object variables that are needed. For example, `self._received_messages` variable could be used to store all the input messages for the current epoch and initialized to an empty list in the constructor.
- Overwrite the `clear_epoch_variables` method
    - This method is automatically called after receiving an Epoch message for a new epoch. It should clear and initialize all the variables that are used to store information about the received input data within each data.
    - For example, if `self._received_messages` variable is used to store all the received input messages from the other components for the current epoch, this method would include setting that variable to an empty list.
- Overwrite the `general_message_handler` method
    - Handling of all incoming messages other than Epoch or SimState messages should be added here.
    - After handling the incoming message call `start_epoch` method unless it is clear that the component is not yet ready to do any calculations for the current epoch.
- Overwrite the `all_messages_received_for_epoch` method
    - This method should return True only if all the necessary information is available for the component to process the current epoch.
    - The use of additional object variables, initialized in the constructor, is almost certainly necessary to achieve the required checks.
- Overwrite the `process_epoch` method
    - This method is automatically called by `start_epoch` if the component is ready to process the current epoch. Usually it should not be called directly from user-added code.
    - Add all the calculations that are needed for processing the epoch here.
    - Add sending of any result messages here.
    - Return True if the component is fully finished with the current epoch and will not be sending any other result messages after this. Return value True will automatically trigger the sending of Status ready message from this component.
    - Return False if the component can do further processing within the current epoch.
- If required, add other changes or overwrites to the abstract component class.
    - Usually these should not be needed.

## How to use the example code

- Message class examples, [`examples/messages.py`](examples/messages.py)
    - Contains some examples on how create and use the message classes.
    - The default Python interpreter can be used to run the test code (run `python` or `python3` from the the project root):

        ```python
        from examples.messages import *

        test_from_json()            # examples on creating message objects from JSON
        test_invalid_status()       # examples on trying to create status messages with invalid input
        test_message_generator()    # examples on creating messages using the message generator helper class
        test_timeseries_from_csv()  # examples on creating TimeSeriesBlock objects from CSV files
        ```

- Message bus client examples
    - Contains an example on how to create an instance of the RabbitmqClient that can be used to send and receive messages to and from the message bus, [`examples/client.py`](examples/client.py).
    - Contains examples on how to send messages to the message bus using the RabbitmqClient class, [`examples/client_send.py`](examples/client_send.py).
    - Contains an example on how to receive and handle messages incoming from the message bus using the RabbitmqClient class, [`examples/client_receive.py`](examples/client_receive.py).
    - To start the message receiver example (from the command line):

        ```python
        python -u -m examples.client_receive
        ```

    - To start the message sender example (from the command line):

        ```python
        python -u -m examples.client_send
        ```

- The Timer class examples, [examples/timer.py](examples/timer.py)
    - Contains a couple of examples on how to start timed tasks with or without extra parameters.
    - To start the timer example (from the command line):

        ```python
        python -u -m examples.timer
        ```

## Things not yet covered here

- Test code or how to write unit tests for new message classes or other tools based on the common code.
- How to use the code library or your own code with Docker.

## Run unit tests for the simulation-tools library

Note: if you are using an old version of Docker and separately installed Docker Compose, in the following replace `docker compose` with `docker-compose`

```bash
docker network create tools_test_network
docker compose -f rabbitmq/docker-compose-rabbitmq.yml up --detach
docker compose -f mongodb/docker-compose-mongodb.yml up --detach
# Wait a few seconds to allow the local RabbitMQ message bus to initialize.
docker compose -f docker-compose-tests.yml up --build
```

To see more log output during the tests use a lower number for `SIMULATION_LOG_LEVEL` in the file `docker-compose-tests.yml`, for example `SIMULATION_LOG_LEVEL=30`, and run the last command again. By default only critical log messages are shown since some of the tests will output error level log messages even when the unit tests are passing.

## Clean up after running the tests

```bash
docker compose -f rabbitmq/docker-compose-rabbitmq.yml down --remove-orphans
docker compose -f mongodb/docker-compose-mongodb.yml down --remove-orphans
docker compose -f docker-compose-tests.yml down --remove-orphans
docker network rm tools_test_network
```
