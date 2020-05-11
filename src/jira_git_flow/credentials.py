import os
from marshmallow import Schema, fields, post_load
from prompt_toolkit import prompt, print_formatted_text, HTML

from jira_git_flow import config
from jira_git_flow.cli import print_simple_collection
from jira_git_flow.db import EntityRepository, ForeignEntity
from jira_git_flow.validators import UniqueID


class Credentials:
    """Credentials object"""

    def __init__(self, id, username, email, token):
        self.id = id
        self.username = username
        self.email = email
        self.token = token


class CredentialsRepository(EntityRepository):
    """Credentials repository"""

    def __init__(self):
        super().__init__(Credentials, CredentialsSchema(), "credentials.json")


class CredentialsEntity(ForeignEntity):
    repository = CredentialsRepository


class CredentialsSchema(Schema):
    id = fields.Str()
    username = fields.Str()
    email = fields.Str()
    token = fields.Str()

    @post_load
    def deserialize(self, data, **kwargs):
        return Credentials(**data)


class CredentialsCLI:
    def __init__(self, repository):
        self.repository = repository

    def new(self):
        id = prompt(
            "Credentials ID: ", validator=UniqueID("Credentials", self.repository)
        )
        email = prompt("Email: ")
        username = prompt("Username: ")
        token = prompt("Token/password: ", is_password=True)

        c = Credentials(id, username, email, token)
        self.repository.save(c)

    def list(self):
        """List all credentials."""
        print_simple_collection(
            CredentialsSchema(), self.repository.all(), "id", exclude=["token"]
        )
