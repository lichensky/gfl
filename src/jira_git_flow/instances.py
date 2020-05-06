import os
import questionary
from prompt_toolkit import prompt
from prompt_toolkit.completion.word_completer import WordCompleter
from tinydb import TinyDB, Query

from jira_git_flow import config
from jira_git_flow.db import Model, Repository, FindableByName
from jira_git_flow.cli import print_simple_collection
from jira_git_flow.validators import NameValidator, ExistenceValidator

JIRA_SERVER = "server"
JIRA_CLOUD = "cloud"

class Instance(Model):
    def __init__(self, name, url, type, credentials):
        self.name = name
        self.url = url
        self.credentials = credentials
        self.type = type


class InstanceRepository(Repository, FindableByName):
    def __init__(self):
        super().__init__(Instance, "instances.json")


class InstanceCLI:
    def __init__(self, instance_repository, credentials_repository):
        self.instance_repository = instance_repository
        self.credentials_repository = credentials_repository

    def new(self):
        nv = NameValidator("Instance", self.instance_repository)
        name = prompt("Name: ", validator=nv)
        url = prompt("Instance URL: ")

        type = questionary.select(
            "Instance type:",
            choices=[JIRA_CLOUD, JIRA_SERVER]
        ).ask()

        credentials = questionary.select(
            "Credentials:",
            choices=self.credentials_repository.names()
        ).ask()

        i = Instance(name, url, type, credentials)
        self.instance_repository.save(i)

    def list(self):
        """List all instances."""
        print_simple_collection(self.instance_repository.all(), "name")

