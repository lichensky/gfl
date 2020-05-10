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


class Issue():
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

    @classmethod
    def from_jira(cls, issue):
        if isinstance(issue, cls):
            return issue
        i = cls(issue.key, issue.fields.summary, _get_type(issue), _get_status(issue),)
        i.subtasks = _get_subtasks(issue)
        return i

    def add_subtask(self, subtask):
        if subtask not in self.subtasks:
            self.subtasks.append(subtask)


def _get_subtasks(jira_issue):
    try:
        return [Issue.from_jira(subtask) for subtask in jira_issue.fields.subtasks]
    except AttributeError as e:
        return []


def _get_type(jira_issue):
    jira_type = jira_issue.fields.issuetype.name
    for key, value in config.ISSUE_TYPES.items():
        if jira_type == value["name"]:
            return key
    raise Exception(f"Unable to map issue type: {jira_type}")


def _get_status(jira_issue):
    jira_status = jira_issue.fields.status.name
    for key, value in config.STATUSES.items():
        if jira_status in value:
            return key
    raise Exception(f"Unable to map issue status: {jira_status}")


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

    def choose_by_types(self, types):
        return self.choose_interactive(lambda issue: issue.type in types)

    def choose_by_status(self, status):
        return self.choose_interactive(lambda issue: issue.status == status)

    def choose_interactive(self, filter_function=lambda issue: True, show_only=False):
        issues = self.repository.all()

        if not issues:
            return []

        pointer_index = get_pointer_index(
            issues, self.workspace.current_issue, self.workspace.current_story
        )
        choices = convert_stories_to_choices(issues, filter_function)

        if choices[pointer_index].get("disabled") and not show_only:
            pointer_index = 0

        selected = select_issue(pointer_index=pointer_index, choices=choices)

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

    def new(self, type, is_subtask):
        issue = {}

        if is_subtask:
            last_story = self.workspace.current_story
            if last_story:
                print("Creating subtask for story {}".format(last_story))
                issue["parent"] = {"key": last_story}

        summary = prompt(f"Please enter {type} summary")
        description = prompt(
            "Description: (ESCAPE followed by ENTER to accept)\n > ", multiline=True
        )
        fields = {
            "project": {"key": workspace.project},
            "summary": summary,
            "description": description,
            "issuetype": {
                "name": config.ISSUE_TYPES[type]["name"],
                "subtask": is_subtask,
            },
        }

        issue.update(fields)

        return issue
