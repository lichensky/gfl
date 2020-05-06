from jira_git_flow.db import Model, Repository

class Workspace(Model):
    def __init__(self, path):
        self.path = path
        self.current_task = None

class WorkspaceRepository(Repository):
    def __init__(self):
        super().__init__(Workspace, "workspaces.json")
