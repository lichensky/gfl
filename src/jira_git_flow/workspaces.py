import json
import pathlib
import questionary
from os import path

from marshmallow import Schema, fields, post_load
from tinydb import Query

from jira_git_flow.db import Repository
from jira_git_flow.cli import print_simple_collection


class Workspace():
    def __init__(self, path, project):
        self.path = path
        self.project = project
        self.current_story = None
        self.current_issue = None



class WorkspaceSchema(Schema):
    path = fields.Str()
    project = fields.Str()
    current_story = fields.Str(allow_none=True)
    current_issue = fields.Str(allow_none=True)

    @post_load
    def deserialize(self, data, **kwargs):
        workspace = Workspace(data['path'], data['project'])
        workspace.current_issue = data['current_issue']
        workspace.current_story = data['current_story']
        return workspace

class WorkspaceRepository(Repository):
    def __init__(self):
        super().__init__(Workspace, WorkspaceSchema(), "workspaces.json")

    def upsert(self, workspace):
        query = Query()
        self.db.upsert(workspace.__dict__, query.path == workspace.path)

    def exists(self, path):
        workspace = Query()
        return bool(self.db.search(workspace.path.matches(path)))

    def get_by_path(self, path):
        workspace = Query()
        try:
            return self.schema.load(self.db.search(workspace.path == path)[0])
        except IndexError:
            return None

    def get_current_workspace(self):
        path = pathlib.Path().absolute().as_posix()
        return self.get_by_path(path)

    def update(self, workspace):
        serialized = self.schema.dump(workspace)
        self.db.update(serialized, Query().path == workspace.path)


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

    def list(self):
        print_simple_collection(WorkspaceSchema(), self.workspaces.all(), "path")
