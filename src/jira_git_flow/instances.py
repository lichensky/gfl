import os
import questionary
from marshmallow import Schema, fields, post_load
from prompt_toolkit import prompt
from prompt_toolkit.completion.word_completer import WordCompleter
from tinydb import TinyDB, Query

from jira_git_flow import config
from jira_git_flow.db import EntityRepository
from jira_git_flow.cli import print_simple_collection
from jira_git_flow.validators import UniqueID, ExistenceValidator

JIRA_SERVER = "server"
JIRA_CLOUD = "cloud"

class Instance():
    def __init__(self, id, url, type, credentials):
        self.id = id
        self.url = url
        self.credentials = credentials
        self.type = type

class InstanceSchema(Schema):
    id = fields.Str()
    url = fields.Str()
    credentials = fields.Str()
    type = fields.Str()

    @post_load
    def deserialize(self, data, **kwargs):
        return Instance(**data)

class InstanceRepository(EntityRepository):
    def __init__(self):
        super().__init__(Instance, InstanceSchema(), "instances.json")


class InstanceCLI:
    def __init__(self, instance_repository, credentials_repository):
        self.instance_repository = instance_repository
        self.credentials_repository = credentials_repository

    def new(self):
        validator = UniqueID("Instance", self.instance_repository)
        id = prompt("Instance ID: ", validator=validator)
        url = prompt("Instance URL: ")

        type = questionary.select(
            "Instance type:",
            choices=[JIRA_CLOUD, JIRA_SERVER]
        ).ask()

        credentials = questionary.select(
            "Credentials:",
            choices=self.credentials_repository.ids()
        ).ask()

        i = Instance(id, url, type, credentials)
        self.instance_repository.save(i)

    def list(self):
        """List all instances."""
        print_simple_collection(InstanceSchema(), self.instance_repository.all(), "id")

