import questionary
from prompt_toolkit import prompt, print_formatted_text, HTML

from jira_git_flow.db import Model, Repository
from jira_git_flow.actions import ACTIONS
from jira_git_flow.statuses import STATUSES
from jira_git_flow.types import TYPES


class Action:
    def __init__(self, initial_state, transitions, next_state, assign):
        self.initial_state = initial_state
        self.transitions = transitions
        self.next_state = next_state
        self.assign_to_user = assign


class Workflow(Model):
    def __init__(self, name):
        self.name = name
        self.statuses = {}
        self.actions = {}
        self.types = {}

    def add_action(self, name, action):
        self.actions[name] = action

    def add_status(self, name, statuses):
        self.statuses[name] = statuses

    def add_type(self, name, types):
        self.types[name] = types


class WorkflowRepository(Repository):
    def __init__(self):
        super().__init__(Workflow, "workflows.json")


class WorkflowCLI:
    def __init__(self, workflow_repository):
        self.workflow_repository = workflow_repository

    def new(self):
        name = questionary.text("Workflow name:").ask()
        workflow = Workflow(name)

        print("Enter issue types mapping")
        for issue_type in TYPES:
            mapping = prompt(f"{issue_type}: ")
            workflow.add_type(issue_type, mapping)

        print("Enter issue statuses mapping (separated by comma)")
        for status in STATUSES:
            mapping = prompt_for_collection(status)
            workflow.add_status(status, mapping)

        for action in ACTIONS:
            print()
            print_formatted_text(HTML(f"<b>Define action:</b> {action}"))
            initial_state = questionary.select(
                "Initial state:", choices=STATUSES
            ).ask()
            transitions = questionary.text(
                "Enter JIRA transitions (separated by comma):"
            ).ask()
            next_state = questionary.select(
                "Next state:", choices=STATUSES
            ).ask()
            assign_to_user = questionary.confirm(
                "Assign during transition:"
            ).ask()

            actionModel = Action(initial_state, transitions, next_state, assign_to_user)
            workflow.add_action(action, actionModel)

        print(workflow.to_db())


def prompt_for_collection(name):
    collection = prompt(f"{name}: ").split(",")
    # Trim and filter mappings
    collection = [*map(str.strip, collection)]
    collection = [*filter(lambda x: x, collection)]
