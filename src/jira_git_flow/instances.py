import os
from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.completion.word_completer import WordCompleter
from tinydb import TinyDB, Query

from jira_git_flow import config


class NameValidator(Validator):
    def __init__(self, repo):
        self.repo = repo

    def validate(self, document):
        text = document.text

        if self.repo.find_by_name(text):
            raise ValidationError(message='Project name already exists')

class Instance():
    def __init__(self, name, url, credentials):
        self.name = name
        self.url = url
        self.credentials = credentials


class InstanceRepository():
    def __init__(self):
        self.db = TinyDB(os.path.join(config.DATA_DIR, 'instances.json'))

    def add(self, instance):
        self.db.insert(instance.__dict__)

    def find_by_name(self, name):
        Instance = Query()
        instances = self.db.search(Instance.name == name)
        if instances:
            return instances[0]
        return None


class InstanceCLI():
    def __init__(self, credentials_manager, instance_repository):
        self.cm = credentials_manager
        self.repository = instance_repository

    def new(self):
        name = prompt("Name: ", validator=NameValidator(self.ir))
        url = prompt("Instance URL: ")
        available_credentials = WordCompleter(self.cm.get_names())
        credentials = prompt("Credentials: ", completer=available_credentials,
            complete_while_typing=True)
        return Instance(name, url, credentials)