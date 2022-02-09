# -*- coding: utf-8 -*-
# Copyright 2021 Tampere University and VTT Technical Research Centre of Finland
# This software was developed as a part of the ProCemPlus project: https://www.senecc.fi/projects/procemplus
# This source code is licensed under the MIT license. See LICENSE in the repository root directory.
# Author(s): Ville Heikkilä <ville.heikkila@tuni.fi>
#            Otto Hylli <otto.hylli@tuni.fi>

"""This module contains a class for writing and reading documents to a Mongo database."""

import datetime
import operator
from typing import Any, Dict, List, Optional, Tuple, Union

import motor.motor_asyncio
import pymongo
import pymongo.results

from tools.datetime_tools import to_utc_datetime_object
from tools.tools import EnvironmentVariableType, EnvironmentVariableValue, FullLogger, load_environmental_variables

LOGGER = FullLogger(__name__)


def default_env_variable_definitions() -> List[Tuple[str, EnvironmentVariableType, EnvironmentVariableValue]]:
    """Returns the default environment variable definitions for MongodbClient."""
    def env_variable_name(simple_variable_name):
        return "{:s}{:s}".format(MongodbClient.DEFAULT_ENV_VARIABLE_PREFIX, simple_variable_name.upper())

    return [
        (env_variable_name("host"), str, "localhost"),
        (env_variable_name("port"), int, 27017),
        (env_variable_name("username"), str, ""),
        (env_variable_name("password"), str, ""),
        (env_variable_name("database"), str, "db"),
        (env_variable_name("appname"), str, "log_writer"),
        (env_variable_name("tz_aware"), bool, True),
        (env_variable_name("metadata_collection"), str, "simulations"),
        (env_variable_name("messages_collection_prefix"), str, "simulation_"),
        (env_variable_name("invalid_messages_collection_prefix"), str, "invalid_simulation_"),
        (env_variable_name("collection_identifier"), str, "SimulationId"),
        (env_variable_name("admin"), bool, True),
        (env_variable_name("tls"), bool, False),
        (env_variable_name("tls_allow_invalid_certificates"), bool, False)
    ]


def load_config_from_env_variables() -> Dict[str, Optional[EnvironmentVariableValue]]:
    """Returns configuration dictionary from which values are fetched from environmental variables."""
    def simple_name(env_variable_name):
        return env_variable_name[len(MongodbClient.DEFAULT_ENV_VARIABLE_PREFIX):].lower()

    env_variables = load_environmental_variables(*default_env_variable_definitions())

    return {
        simple_name(variable_name): env_variables[variable_name]
        for variable_name in env_variables
    }


class MongodbClient:
    """MongoDB client that can be used to write JSON documents to Mongo database."""
    DEFAULT_ENV_VARIABLE_PREFIX = "MONGODB_"
    CONNECTION_PARAMTERS = ["host", "port", "username", "password", "appname", "tz_aware", "tls"]
    AUTHENTICATION_INPUT_PARAMETER = "database"
    AUTHENTICATION_OUTPUT_PARAMETER = "authSource"
    TLS_INVALID_CERTIFICATES_INPUT_PARAMETER = "tls_allow_invalid_certificates"
    TLS_INVALID_CERTIFICATES_OUTPUT_PARAMETER = "tlsAllowInvalidCertificates"
    ADMIN_ATTRIBUTE = "admin"
    TLS_ATTRIBUTE = "tls"
    TOPIC_ATTRIBUTE = "Topic"

    TIMESTAMP_ATTRIBUTE = "Timestamp"
    STARTTIME_ATTRIBUTE = "StartTime"
    ENDTIME_ATTRIBUTE = "EndTime"

    # These attributes will be converted to datetime objects before writing to database.
    DATETIME_ATTRIBUTES = [
        TIMESTAMP_ATTRIBUTE,
        STARTTIME_ATTRIBUTE,
        ENDTIME_ATTRIBUTE
    ]

    # Additional attributes that are used in the collection indexes.
    EPOCH_ATTRIBUTE = "EpochNumber"
    PROCESS_ATTRIBUTE = "SourceProcessId"

    FULL_ATTRIBUTE_NAME_LIST = CONNECTION_PARAMTERS + \
        [
            "database",
            "metadata_collection",
            "messages_collection_prefix",
            "invalid_messages_collection_prefix",
            "collection_identifier",
            "admin",
            "tls_allow_invalid_certificates"
        ]

    # List of possible metadata attributes in addition to the simulation id.
    # Each element is a tuple (attribute_name, attribute_types, comparison_operator)
    # attribute_types is 1-element list for non-list-attribute types and
    # n-element list for list-attribute types with the last element describing the internal type.
    # For attributes with comparison_operator is None, the previous value is always overwritten,
    # for other attributes, the previous value is overwritten only if old_value <comparison_operator> new_value.
    METADATA_ATTRIBUTES = [
        ("StartTime", [datetime.datetime], operator.gt),
        ("EndTime", [datetime.datetime], operator.lt),
        ("Name", [str], None),
        ("Description", [str], None),
        ("Epochs", [int], operator.lt),
        ("Processes", [list, str], None)
    ]

    def __init__(self, **kwargs):
        """Available attributes, all other attributes are ignored:
           - host                        : the host name for the MongoDB (str)
           - port                        : the port number for the MongoDB (int)
           - username                    : username for access to the MongoDB (str)
           - password                    : password for access to the MongoDB (str)
           - database                    : the database name used with the MongoDB (str)
           - appname                     : application name for the connection to the MongoDB (str)
           - tz_aware                    : are datetime values timezone aware (bool)
           - metadata_collection         : the collection name for the simulation metadata (str)
           - messages_collection_prefix  : the prefix for the collection names for the simulation messages (str)
           - invalid_messages_collection_prefix  : the prefix for the collection names for the invalid
                                                   simulation messages (str)
           - collection_identifier       : the attribute name in the messages that tells the simulation id (str)
           - admin                       : whether the given account has root user access (bool)
           - tls                         : Is TLS encryption used with the MongoDB server (bool).
           - tls_allow_invalid_certificates : Are invalid server certificates accepted (bool).

           If a value for attribute is missing from kwargs, the value is read from
           the corresponding environmental variable with the given default value as a backup.
           - MONGODB_HOST (default value: "localhost")
           - MONGODB_PORT (default value: 27017)
           - MONGODB_USERNAME (default value: "")
           - MONGODB_PASSWORD (default value: "")
           - MONGODB_DATABASE (default value: "db")
           - MONGODB_APPNAME (default value: "log_writer")
           - MONGODB_TZ_AWARE (default value: True)
           - MONGODB_METADATA_COLLECTION (default value: "simulations")
           - MONGODB_MESSAGES_COLLECTION_PREFIX (default value: "simulation_")
           - MONGODB_INVALID_MESSAGES_COLLECTION_PREFIX (default value: "invalid_simulation_")
           - MONGODB_COLLECTION_IDENTIFIER (default value: "SimulationId")
           - MONGODB_ADMIN (default value: True)
           - MONGODB_TLS (default value: False)
           - MONGODB_TLS_ALLOW_INVALID_CERTIFICATES (default value: False)
        """
        kwargs_env = load_config_from_env_variables()
        kwargs = {
            attribute_name: kwargs.get(attribute_name, kwargs_env[attribute_name])
            for attribute_name in MongodbClient.FULL_ATTRIBUTE_NAME_LIST
        }

        self.__connection_parameters = MongodbClient.__get_connection_parameters_only(kwargs)
        self.__database_name = str(kwargs["database"])
        self.__metadata_collection_name = str(kwargs["metadata_collection"])
        self.__messages_collection_prefix = str(kwargs["messages_collection_prefix"])
        self.__invalid_messages_collection_prefix = str(kwargs["invalid_messages_collection_prefix"])
        self.__collection_identifier = str(kwargs["collection_identifier"])

        # Set up the Mongo database connection and the metadata collection
        self.__mongo_client = motor.motor_asyncio.AsyncIOMotorClient(**self.__connection_parameters)
        self.__mongo_database = self.__mongo_client[self.__database_name]
        self.__metadata_collection = self.__mongo_database[self.__metadata_collection_name]

    @property
    def host(self) -> str:
        """The host name of the MongoDB."""
        return str(self.__connection_parameters["host"])

    @property
    def port(self) -> int:
        """The port number of the MongoDB."""
        return int(str(self.__connection_parameters["port"]))

    async def store_message(self, json_document: dict, document_topic: Optional[str] = None, invalid: bool = False,
                            default_simulation_id: Optional[str] = None) -> bool:
        """Stores a new JSON message to the database. The used collection is determined by the 'simulation_id'
           attribute in the message or if message has no simulation id default simulation id is used.
           If invalid is False the normal messages collection is used.
           If it is True the invalid messages collection is used.
           Returns True, if writing to the database was successful.
        """
        # use the store_messages method and check that it has returned id of the stored document.
        return len(await self.store_messages([(json_document, document_topic)], invalid, default_simulation_id)) == 1

    async def store_messages(self, documents: List[Tuple[dict, Optional[str]]], invalid: bool = False,
                             default_simulation_id: Optional[str] = None) -> List[str]:
        """Stores several messages to the database. All documents are expected to belong to the same simulation.
           The simulation is identified based on the first message on the list or default simulation id
           if the first message does not have a simulation id.
           Invalid tells if the invalid or normal message collection should be used.

           documents parameters is expected to be a list of tuples (message_json, topic_name),
           where message_json is the message in JSON format and topic_name is a string for the message topic."""
        if not documents or not isinstance(documents, list):
            return []

        # Add the topic attribute to the JSON documents.
        full_documents = [
            {
                **document,
                MongodbClient.TOPIC_ATTRIBUTE: topic_name
            }
            for document, topic_name in documents
        ]

        message_collection_name = self.__get_message_collection(full_documents[0], invalid, default_simulation_id)
        if message_collection_name is None:
            LOGGER.warning(
                "The first document does not have '{:s}' attribute and default simulation was not given.".format(
                    self.__collection_identifier))
            return []

        await MongodbClient.datetime_attributes_to_objects(full_documents)

        mongodb_collection = self.__mongo_database[message_collection_name]
        inserted_ids = []  # ids of inserted documents

        # use insert_one or insert_many depending on the number of documents
        if len(full_documents) > 1:
            write_result = await mongodb_collection.insert_many(full_documents)
            if write_result.acknowledged:
                inserted_ids = write_result.inserted_ids

        elif len(full_documents) == 1:
            write_result = await mongodb_collection.insert_one(full_documents[0])
            if write_result.acknowledged:
                inserted_ids = [write_result.inserted_id]

        return inserted_ids

    async def update_metadata(self, simulation_id: str, **attribute_updates) -> bool:
        """Creates or updates the metadata information for a simulation."""
        if not isinstance(simulation_id, str):
            LOGGER.warning("Given simulation id was not of type str: '{:s}'".format(str(type(simulation_id))))
            return False

        simple_document = {self.__collection_identifier: simulation_id}
        metadata_document = await self.__metadata_collection.find_one(simple_document)

        # Add a new metadata document.
        if metadata_document is None:
            metadata_document = await self.get_metadata_json(simple_document, attribute_updates)
            if metadata_document is None:
                LOGGER.warning("Problem creating the metadata document for simulation {:s}".format(simulation_id))
                return False

            write_result = await self.__metadata_collection.insert_one(metadata_document)
            return (
                isinstance(write_result, pymongo.results.InsertOneResult) and
                write_result.acknowledged
            )

        # Update previous document.
        metadata_document = await self.get_metadata_json(metadata_document, attribute_updates)
        if metadata_document is None:
            LOGGER.warning("Problem creating the metadata document for simulation {:s}".format(simulation_id))
            return False

        write_result = await self.__metadata_collection.replace_one(simple_document, metadata_document)
        return (
            isinstance(write_result, pymongo.results.UpdateResult) and
            write_result.acknowledged and
            write_result.modified_count == 1
        )

    async def update_metadata_indexes(self):
        """Updates indexes to the metadata collection and adds them if they do not exist yet."""
        metadata_indexes = [
            pymongo.IndexModel(
                [(self.__collection_identifier, pymongo.ASCENDING)],
                name="simulation_id_index",
                unique=True
            ),
            pymongo.IndexModel(
                [
                    (MongodbClient.STARTTIME_ATTRIBUTE, pymongo.ASCENDING),
                    (MongodbClient.ENDTIME_ATTRIBUTE, pymongo.ASCENDING)
                ],
                name="start_time_index"
            ),
            pymongo.IndexModel(
                [(MongodbClient.ENDTIME_ATTRIBUTE, pymongo.ASCENDING)],
                name="end_time_index",
                sparse=True
            )
        ]

        result = await self.__metadata_collection.create_indexes(metadata_indexes)

        if len(result) != len(metadata_indexes):
            LOGGER.warning("Problem with updating metadata collection indexes, result: {:s}".format(str(result)))
        else:
            LOGGER.debug("Updated the metadata collection indexes successfully.")

    async def add_simulation_indexes(self, simulation_id: str):
        """Adds or updates indexes to the collections containing the valid and invalid messages
           from the specified simulation."""
        # indexes for the valid messages collection
        simulation_indexes = [
            pymongo.IndexModel(
                [
                    (MongodbClient.EPOCH_ATTRIBUTE, pymongo.ASCENDING),
                    (MongodbClient.PROCESS_ATTRIBUTE, pymongo.ASCENDING),
                    (MongodbClient.TOPIC_ATTRIBUTE, pymongo.ASCENDING),
                ],
                name="epoch_index"
            ),
            pymongo.IndexModel(
                [
                    (MongodbClient.PROCESS_ATTRIBUTE, pymongo.ASCENDING),
                    (MongodbClient.TOPIC_ATTRIBUTE, pymongo.ASCENDING)
                ],
                name="process_index"
            ),
            pymongo.IndexModel(
                [
                    (MongodbClient.TOPIC_ATTRIBUTE, pymongo.ASCENDING),
                    (MongodbClient.STARTTIME_ATTRIBUTE, pymongo.ASCENDING)
                ],
                name="topic_index"
            )
        ]

        message_collection_name = self.__get_message_collection({self.__collection_identifier: simulation_id})
        result = await self.__mongo_database[message_collection_name].create_indexes(simulation_indexes)

        if len(result) != len(simulation_indexes):
            LOGGER.warning("Problem with updating message collection indexes for {:s}, result: {:s}".format(
                simulation_id, str(result)))
        else:
            LOGGER.debug("Updated the message collection indexes for {:s} successfully.".format(simulation_id))

        # indexes for invalid messages collection
        simulation_indexes = [
            pymongo.IndexModel(
                [
                    (MongodbClient.TOPIC_ATTRIBUTE, pymongo.ASCENDING),
                    (MongodbClient.TIMESTAMP_ATTRIBUTE, pymongo.ASCENDING)
                ],
                name="topic_index"
            ),
            pymongo.IndexModel(
                [
                    (MongodbClient.TIMESTAMP_ATTRIBUTE, pymongo.ASCENDING)
                ],
                name="timestamp_index"
            )
        ]

        message_collection_name = self.__get_message_collection(
            {self.__collection_identifier: simulation_id},
            invalid=True
        )
        result = await self.__mongo_database[message_collection_name].create_indexes(simulation_indexes)

        if len(result) != len(simulation_indexes):
            LOGGER.warning("Problem with updating invalid message collection indexes for {:s}, result: {:s}".format(
                simulation_id, str(result)))
        else:
            LOGGER.debug("Updated the invalid message collection indexes for {:s} successfully.".format(simulation_id))

    def __get_message_collection(self, json_document: dict, invalid: bool = False,
                                 default_simulation_id: Optional[str] = None) -> Optional[str]:
        """Returns the collection name for the document.
        Invalid False gives the normal messages collection and True gives the invalid messages collection.
        Default_simulation_id is used with invalid messages which do not have simulation id.
        """
        if self.__collection_identifier in json_document:
            simulation_id = str(json_document[self.__collection_identifier])

        elif default_simulation_id is not None:
            simulation_id = default_simulation_id

        else:
            return None

        if invalid:
            collection = self.__invalid_messages_collection_prefix + simulation_id

        else:
            collection = self.__messages_collection_prefix + simulation_id

        return collection

    @classmethod
    async def datetime_attributes_to_objects(cls, json_documents: Union[dict, List[dict]]):
        """Convert the datetime attributes from type str to datetime.datetime
           in the given json object or list of json objects."""
        if not isinstance(json_documents, list):
            json_documents = [json_documents]

        for json_document in json_documents:
            for datetime_attribute in cls.DATETIME_ATTRIBUTES:
                if datetime_attribute in json_document and isinstance(json_document[datetime_attribute], str):
                    json_document[datetime_attribute] = to_utc_datetime_object(json_document[datetime_attribute])

    async def get_metadata_json(self, old_values: dict, new_values: dict) -> Optional[Dict[str, Any]]:
        """Returns a validated metadata document. Any attributes that not
           simulation_id or in METADATA_ATTRIBUTES list are ignored."""
        if new_values is None:
            return None
        if old_values is None:
            old_values = {}

        simulation_id_old = old_values.get(self.__collection_identifier, None)
        simulation_id_new = new_values.get(self.__collection_identifier, None)
        if ((simulation_id_old is None and simulation_id_new is None) or
                (simulation_id_old is not None and simulation_id_new is not None and
                 simulation_id_old != simulation_id_new)):
            # The simulation ids from the new and old values did not match.
            return None

        metadata_values = {self.__collection_identifier: simulation_id_old}
        for metadata_attribute in MongodbClient.METADATA_ATTRIBUTES:
            attribute_name, attribute_types, comparison_operator = metadata_attribute
            old_value = old_values.get(attribute_name, None)
            new_value = new_values.get(attribute_name, None)

            # New value is of proper type.
            if MongodbClient.__check_value_types(new_value, attribute_types):
                # Old value is of proper type.
                if MongodbClient.__check_value_types(old_value, attribute_types):
                    if comparison_operator is None or comparison_operator(old_value, new_value):
                        metadata_values[attribute_name] = new_value
                    else:
                        metadata_values[attribute_name] = old_value
                # Old value either does not exist is not of proper type.
                else:
                    metadata_values[attribute_name] = new_value
            # New value does not exist but the old value is usable.
            elif MongodbClient.__check_value_types(old_value, attribute_types):
                metadata_values[attribute_name] = old_value

        return metadata_values

    @classmethod
    def __check_value_types(cls, value: Any, types: list) -> bool:
        """Checks that value is of proper type. Used for the metadata attributes."""
        if value is None:
            return False
        if len(types) == 0:
            return True
        if len(types) == 1:
            return isinstance(value, types[0])
        if not isinstance(value, types[0]):
            return False

        try:
            for value_element in value:
                if not cls.__check_value_types(value_element, types[1:]):
                    return False
        except TypeError as error:
            LOGGER.warning("TypeError : {:s}".format(str(error)))
            return False

        return True

    @classmethod
    def __get_connection_parameters_only(cls, connection_config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Returns only the parameters needed for creating a connection."""
        stripped_connection_config = {
            config_parameter: parameter_value
            for config_parameter, parameter_value in connection_config_dict.items()
            if config_parameter in cls.CONNECTION_PARAMTERS
        }

        # for non-root users: authorize only for the database containing the documents instead to admin
        if (not connection_config_dict.get(cls.ADMIN_ATTRIBUTE, True) and
                cls.AUTHENTICATION_INPUT_PARAMETER in connection_config_dict):
            stripped_connection_config[cls.AUTHENTICATION_OUTPUT_PARAMETER] = \
                connection_config_dict[cls.AUTHENTICATION_INPUT_PARAMETER]

        if connection_config_dict.get(cls.TLS_ATTRIBUTE, False):
            stripped_connection_config[cls.TLS_INVALID_CERTIFICATES_OUTPUT_PARAMETER] = \
                connection_config_dict.get(cls.TLS_INVALID_CERTIFICATES_INPUT_PARAMETER, False)

        return stripped_connection_config
