import questionary
from marshmallow import Schema, fields, post_load
from prompt_toolkit import prompt, print_formatted_text, HTML
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

from jira_git_flow.cli import print_simple_collection
from jira_git_flow.db import EntityRepository
from jira_git_flow.actions import Action, ActionSchema, ACTIONS
from jira_git_flow.statuses import (
    IssueStatusMapping,
    IssueStatusMappingSchema,
    STATUSES,
)
from jira_git_flow.types import IssueTypeMapping, IssueTypeMappingSchema, TYPES


class Workflow:
    def __init__(self, id):
        self.id = id
        self.statuses = []
        self.actions = []
        self.types = []

    def add_action(self, action):
        self.actions.append(action)

    def add_status(self, status_mapping):
        self.statuses.append(status_mapping)

    def add_type(self, type_mapping):
        self.types.append(type_mapping)


class WorkflowSchema(Schema):
    id = fields.Str()
    statuses = fields.Nested(IssueStatusMappingSchema, many=True)
    actions = fields.Nested(ActionSchema, many=True)
    types = fields.Nested(IssueTypeMappingSchema, many=True)

    @post_load
    def deserialize(self, data, **kwargs):
        workflow = Workflow(data["id"])
        for status in data["statuses"]:
            workflow.add_status(status)
        for type in data["types"]:
            workflow.add_type(type)
        for action in data["actions"]:
            workflow.add_action(action)
        return workflow


class WorkflowRepository(EntityRepository):
    def __init__(self):
        super().__init__(Workflow, WorkflowSchema(), "workflows.json")


class WorkflowCLI:
    def __init__(self, workflow_repository):
        self.workflow_repository = workflow_repository

    def new(self):
        id = questionary.text("Workflow ID:").ask()
        workflow = Workflow(id)
        print()

        print("Enter issue types mapping")
        for issue_type in TYPES:
            print("---")
            mapping = prefixed_prompt(issue_type, "Mapping")
            prefix = prefixed_prompt(issue_type, "Branch prefix")
            issue_type_mapping = IssueTypeMapping(issue_type, mapping, prefix)
            workflow.add_type(issue_type_mapping)
        print()

        print("Enter issue statuses mapping (if multiple, enter splitted by comma)")
        for status in STATUSES:
            mapping = prompt(([("bold", f"{status}: ")]))
            mapping = parse_collection(mapping)
            s = IssueStatusMapping(status, mapping)
            workflow.add_status(s)
        print()

        for action_cls in ACTIONS:
            action = action_cls()
            print_formatted_text(
                HTML(
                    f"<b>Define action:</b> {action.name} ({action.initial_state} -> {action.next_state})"
                )
            )
            transitions = questionary.text(
                "Enter JIRA transitions (separated by comma):"
            ).ask()
            action.transitions = parse_collection(transitions)

            action.assign_to_user = questionary.confirm(
                "Assign during transition:"
            ).ask()

            workflow.add_action(action)
            print()

        self.workflow_repository.save(workflow)

    def list(self):
        for workflow in self.workflow_repository.all():
            print_formatted_text(HTML(f"<b>ID: </b>{workflow.id}"))
            print()
            print_formatted_text(HTML("<b>Actions</b>"))
            print("---")
            print_simple_collection(ActionSchema(), workflow.actions, "name")
            print()
            print_formatted_text(HTML("<b>Statuses</b>"))
            print("---")
            print_simple_collection(IssueStatusMappingSchema(), workflow.statuses, "status")
            print()
            print_formatted_text(HTML("<b>Issue types</b>"))
            print("---")
            print_simple_collection(IssueTypeMappingSchema(), workflow.types, "issue_type")


def prefixed_prompt(prefix, msg):
    msg = [("bold", f"({prefix}) "), ("", f"{msg}: ")]
    return prompt(msg)


def parse_collection(collection):
    collection = collection.split(",")
    # Trim and filter mappings
    collection = [*map(str.strip, collection)]
    collection = [*filter(lambda x: x, collection)]
    return collection
