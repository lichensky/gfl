import questionary
from prompt_toolkit import prompt, print_formatted_text, HTML

from jira_git_flow.cli import print_simple_collection
from jira_git_flow.db import Model, EntityRepository
from jira_git_flow.actions import Action, ACTIONS
from jira_git_flow.statuses import STATUSES
from jira_git_flow.types import TYPES


class Workflow(Model):
    def __init__(self, id):
        self.id = id
        self.statuses = {}
        self.actions = {}
        self.types = {}

    def add_action(self, name, action):
        self.actions[name] = action

    def add_status(self, name, statuses):
        self.statuses[name] = statuses

    def add_type(self, name, types):
        self.types[name] = types

    @classmethod
    def from_db(cls, db):
        workflow = cls(db["id"])
        for status, mapping in db["statuses"].items():
            workflow.add_status(status, mapping)
        for type, mapping in db["types"].items():
            workflow.add_type(type, mapping)
        for name, action in db['actions'].items():
            workflow.add_action(name, action)
        return workflow


class WorkflowRepository(EntityRepository):
    def __init__(self):
        super().__init__(Workflow, "workflows.json")


class WorkflowCLI:
    def __init__(self, workflow_repository):
        self.workflow_repository = workflow_repository

    def new(self):
        id = questionary.text("Workflow ID:").ask()
        workflow = Workflow(id)
        print()

        print("Enter issue types mapping")
        for issue_type in TYPES:
            mapping = prompt(f"{issue_type}: ")
            workflow.add_type(issue_type, mapping)
        print()

        print("Enter issue statuses mapping (separated by comma)")
        for status in STATUSES:
            mapping = prompt_for_collection(status)
            workflow.add_status(status, mapping)
        print()

        for action_cls in ACTIONS:
            action = action_cls()
            print_formatted_text(
                HTML(
                    f"<b>Define action:</b> {action.name} ({action.initial_state} -> {action.next_state})"
                )
            )
            action.transitions = questionary.text(
                "Enter JIRA transitions (separated by comma):"
            ).ask()
            action.assign_to_user = questionary.confirm(
                "Assign during transition:"
            ).ask()

            workflow.add_action(action.name, action)
            print()

        self.workflow_repository.save(workflow)

    def list(self):
        print_simple_collection(self.workflow_repository.all(), "id")


def prompt_for_collection(name):
    collection = prompt(f"{name}: ").split(",")
    # Trim and filter mappings
    collection = [*map(str.strip, collection)]
    collection = [*filter(lambda x: x, collection)]
    return collection
