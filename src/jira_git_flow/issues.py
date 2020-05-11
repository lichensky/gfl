import questionary

from marshmallow import Schema, fields, post_load
from prompt_toolkit import prompt
from tinydb import Query

from jira_git_flow import config
from jira_git_flow.db import Repository
from jira_git_flow.cli import (
    get_pointer_index,
    convert_stories_to_choices,
    select_issue,
)
from jira_git_flow import types


class CLIError:
    parent_required = "You must choose story to create a subtask."


class Issue:
    """Jira simplified issue"""

    def __init__(self, key, summary, type, status):
        self.key = key
        self.summary = summary
        self.type = type
        self.status = status
        self.subtasks = []
        self.full_name = self.__repr__()
        self.workspace = None

    def __hash__(self):
        return self.key.split("-")[1]

    def __eq__(self, obj):
        return self.key == obj.key

    def __repr__(self):
        return "{}: {}".format(self.key, self.summary)

    def add_subtask(self, subtask):
        if subtask not in self.subtasks:
            self.subtasks.append(subtask)


class IssueSchema(Schema):
    key = fields.Str()
    summary = fields.Str()
    type = fields.Str()
    status = fields.Str()
    subtasks = fields.Nested("IssueSchema", many=True)
    full_name = fields.Str()
    workspace = fields.Str(allow_none=True)

    @post_load
    def deserialize(self, data, **kwargs):
        issue = Issue(data["key"], data["summary"], data["type"], data["status"])
        issue.subtasks = data["subtasks"]
        return issue


class IssueRepository(Repository):
    def __init__(self):
        super().__init__(Issue, IssueSchema(), "issues.json")

    def find_by_key(self, key):
        for story in self.all():
            if story.key == key:
                return story

            for subtask in story.subtasks:
                if subtask.key == key:
                    return subtask

    def update(self, issue):
        self.db.update(self.schema.dump(issue), Query().key == issue.key)

    def remove(self, issue):
        self.db.remove(Query().key == issue.key)


class IssuesCLI:
    def __init__(self, repository, workspace):
        self.repository = repository
        self.workspace = workspace

    def choose_issue(self):
        issues = self.choose_interactive()
        if issues:
            return issues[0]

    def choose_by_types(self, types, msg=None):
        return self.choose_interactive(lambda issue: issue.type in types, msg=msg)

    def choose_by_status(self, status, msg=None):
        return self.choose_interactive(lambda issue: issue.status == status, msg=msg)

    def choose_interactive(
        self, filter_function=lambda issue: True, show_only=False, msg=None
    ):
        issues = self.repository.all()

        if not issues:
            return []

        pointer_index = get_pointer_index(
            issues, self.workspace.current_issue, self.workspace.current_story
        )
        choices = convert_stories_to_choices(issues, filter_function)

        if choices[pointer_index].get("disabled") and not show_only:
            pointer_index = 0

        selected = select_issue(pointer_index=pointer_index, choices=choices, msg=msg)

        return selected

    def choose_issues_from_simple_view(self, issues):
        if not issues:
            exit("No issues.")
        print("Matching issues")
        for idx, issue in enumerate(issues):
            issue_model = Issue.from_jira(issue)
            print("{}: {} {}".format(idx, issue_model.key, issue_model.summary))
        issue_id = int(questionary.text("Choose issue").ask())
        return issues[issue_id]

    def new(self, type):
        issue = {}

        is_subtask = type == types.SUBTASK
        if is_subtask:
            story = self.repository.find_by_key(self.workspace.current_story)
            if not story:
                try:
                    story = self.choose_by_types(
                        types.STORY, msg="Choose story to create subtask:"
                    )[0]
                except IndexError:
                    raise Exception(CLIError.parent_required)

            if not story:
                raise Exception(CLIError.parent_required)

            print("Creating subtask for story {}".format(story))
            issue["parent"] = {"key": story.key}

        summary = prompt(f"Please enter {type} summary: ")
        description = prompt(
            "Description: (ESCAPE followed by ENTER to accept)\n > ", multiline=True
        )
        fields = {
            "project": {"key": self.workspace.project},
            "summary": summary,
            "description": description,
            "issuetype": {
                "name": workspace.workflow.get_type_mapping(type),
                "subtask": is_subtask,
            },
        }

        issue.update(fields)

        return issue
