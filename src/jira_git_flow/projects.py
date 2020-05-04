from tinydb import TinyDB
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from jira_git_flow import config

db = TinyDB(config.DATA_DIR + 'projects.json')

class Project():
    def __init(self, url, key, credentials):
        self.key = key
        self.url = url
        self.credentials = credentials

    def save(self):
        db.insert(self.__dict__)


class ProjectRepository():
    def add(self):

