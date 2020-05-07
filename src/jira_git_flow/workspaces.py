import json
import pathlib
import questionary
from os import path

WORKSPACE_FILE = ".gfl"


class Workspace:
    def __init__(self, project):
        if path.exists(WORKSPACE_FILE):
            return

        with open(WORKSPACE_FILE, "w+") as f:
            workspace = {"project": project}
            print(workspace)
            json.dump(workspace, f)


class WorkspaceCLI:
    def __init__(self, project_repository):
        self.projects = project_repository

    def init(self):
        project = questionary.select(
            "Choose project:", choices=self.projects.ids()
        ).ask()
        return Workspace(project)
