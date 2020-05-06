import os
from prompt_toolkit import prompt, print_formatted_text, HTML

from jira_git_flow import config
from jira_git_flow.cli import print_simple_collection
from jira_git_flow.db import Model, Repository, FindableByName
from jira_git_flow.validators import NameValidator


class Credentials(Model):
    """Credentials object"""

    def __init__(self, name, username, email, token):
        self.name = name
        self.username = username
        self.email = email
        self.token = token


class CredentialsRepository(Repository, FindableByName):
    """Credentials repository"""

    def __init__(self):
        super().__init__(Credentials, "credentials.json")


class CredentialsCLI:
    def __init__(self, repository):
        self.repository = repository

    def new(self):
        nv = NameValidator("Credentials", self.repository)
        name = prompt("Credentials name: ", validator=nv)
        email = prompt("Email: ")
        username = prompt("Username: ")
        token = prompt("Token/password: ", is_password=True)

        c = Credentials(name, username, email, token)
        self.repository.save(c)

    def list(self):
        """List all credentials."""
        print_simple_collection(self.repository.all(), "name",
            exclude=["token"])
