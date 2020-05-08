import json
import pathlib
import questionary
from os import path

from tinydb import Query

from jira_git_flow.db import Model, Repository


class Workspace(Model):
    def __init__(self, path, project):
        self.path = path
        self.project = project
        self.current_story = None
        self.current_issue = None

    @classmethod
    def from_db(cls, db):
        workspace = cls(db['path'], db['project'])
        workspace.current_issue = db['current_issue']
        workspace.current_story = db['current_story']
        return workspace


class WorkspaceRepository(Repository):
    def __init__(self):
        super().__init__(Workspace, "workspaces.json")

    def upsert(self, workspace):
        query = Query()
        self.db.upsert(workspace.__dict__, query.path == workspace.path)

    def exists(self, path):
        workspace = Query()
        return bool(self.db.search(workspace.path.matches(path)))

    def get_by_path(self, path):
        workspace = Query()
        try:
            return Workspace.from_db(self.db.search(workspace.path == path)[0])
        except IndexError:
            return None

    def get_current_workspace(self):
        path = pathlib.Path().absolute().as_posix()
        return self.get_by_path(path)


class WorkspaceCLI:
    def __init__(self, workspace_repository, project_repository):
        self.workspaces = workspace_repository
        self.projects = project_repository

    def init(self):
        path = pathlib.Path().absolute().as_posix()
        project = questionary.select(
            "Choose project:", choices=self.projects.ids()
        ).ask()
        w = Workspace(path, project)
        self.workspaces.upsert(w)
