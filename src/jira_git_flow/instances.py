import os
import questionary
from marshmallow import Schema, fields, post_load
from prompt_toolkit import prompt
from prompt_toolkit.completion.word_completer import WordCompleter
from tinydb import TinyDB, Query

from jira_git_flow import config
from jira_git_flow.db import EntityRepository, ForeignEntity
from jira_git_flow.cli import print_simple_collection
from jira_git_flow.jira import Jira
from jira_git_flow.validators import UniqueID, ExistenceValidator
from jira_git_flow.credentials import CredentialsSchema, CredentialsEntity

JIRA_SERVER = "server"
JIRA_CLOUD = "cloud"


class Instance:
    def __init__(self, id, url, type, credentials):
        self.id = id
        self.url = url
        self.credentials = credentials
        self.type = type

    def connect(self, project, workflow):
        connection_user = self.get_connection_user()
        return Jira(self, project, workflow, connection_user)

    def get_connection_user(self):
        user = (
            self.credentials.username
            if self.type == JIRA_SERVER
            else self.credentials.email
        )
        return user


class InstanceSchema(Schema):
    id = fields.Str()
    url = fields.Str()
    credentials = CredentialsEntity()
    type = fields.Str()

    @post_load
    def deserialize(self, data, **kwargs):
        return Instance(**data)


class InstanceRepository(EntityRepository):
    def __init__(self):
        super().__init__(Instance, InstanceSchema(), "instances.json")


class InstanceEntity(ForeignEntity):
    repository = InstanceRepository


class InstanceCLI:
    def __init__(self, instance_repository, credentials_repository):
        self.instances = instance_repository
        self.credentials = credentials_repository

    def new(self):
        validator = UniqueID("Instance", self.instances)
        id = prompt("Instance ID: ", validator=validator)
        url = prompt("Instance URL: ")

        type = questionary.select(
            "Instance type:", choices=[JIRA_CLOUD, JIRA_SERVER]
        ).ask()

        credentials = questionary.select(
            "Credentials:", choices=self.credentials.ids()
        ).ask()
        credentials = self.credentials.find_by_id(credentials)

        i = Instance(id, url, type, credentials)
        self.instances.save(i)

    def list(self):
        """List all instances."""
        print_simple_collection(InstanceSchema(), self.instances.all(), "id")
