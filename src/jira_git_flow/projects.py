from tinydb import TinyDB
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from jira_git_flow import config
from jira_git_flow.db import Model, Repository


class Statuses:
    def __init__(self):
        self.open = []
        self.progress = []
        self.review = []
        self.closed = []


class Workflow:
    def __init__(self, statuses, actions):
        self.statuses = statuses
        self.actions = actions


class Project(Model):
    def __init(self, key, instance):
        self.key = key
        self.instance = instance


class ProjectRepository(Repository):
    def __init__(self):
        super().__init__(Project, "projects.json")


class ProjectCLI:
    def __init__(self):
        super().__init__()

    def new(self):
        key = prompt("Project key: ")
        instance = prompt("Project instance: ")
        print("Enter issue statuses mapping (splitted by comma)")
        statuses = Statuses()
        statuses.open = prompt("Open: ").split(",")
        print(statuses.open)
