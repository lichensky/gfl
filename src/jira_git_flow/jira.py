import click
from jira import JIRA, JIRAError

from jira_git_flow.issues import Issue


class Jira(object):
    """JIRA objects and operations."""

    def __init__(self, instance, project, workflow, connection_user, max_results=50):
        self.workflow = workflow
        self.project = project
        self.username = instance.credentials.username
        self.max_results = max_results
        self.jira = JIRA(
            instance.url, basic_auth=(connection_user, instance.credentials.token)
        )

    def search_issues(self, keyword, **kwargs):
        """
        Search Jira issues.

        Filtering by keyword is not done on JIRA query becasue it does not support
        filtering both summary and key by string values.
        """
        keyword = keyword.lower()
        query_parameters = []
        if kwargs.get("type"):
            query_parameters.append('type = "{}"'.format(kwargs.get("type")))

        query = " OR".join(query_parameters) + " order by created desc"
        issues = self.jira.search_issues(query, maxResults=self.max_results)

        matching_issues = []
        for issue in issues:
            if keyword in issue.key.lower() or keyword in issue.fields.summary.lower():
                matching_issues.append(issue)

        return matching_issues

    def get_issue_by_key(self, key):
        """Get issue by key"""
        try:
            jira_issue = self.jira.issue(key)
            return self._convert_to_issue(jira_issue)

        except JIRAError as e:
            if e.status_code == 404:
                raise click.UsageError(
                    "The specified JIRA issue: {}, does not exist.".format(key)
                )
            raise

    def create_issue(self, fields):
        jira_issue = self.jira.create_issue(fields=fields)
        return self._convert_to_issue(jira_issue)

    def get_resolution_by_name(self, name):
        resolutions = self.jira.resolutions()
        for r in resolutions:
            if r.name == name:
                return r.id
        return None

    def get_transition(self, issue, name):
        return self.jira.find_transitionid_by_name(issue, name)

    def transition_issue(self, issue, transition):
        transition_id = self.get_transition(issue, transition)
        if transition_id:
            self.jira.transition_issue(issue, transition_id)

    def assign_issue(self, issue, assignee):
        self.jira.assign_issue(issue, assignee)

    def make_action(self, action, issue):
        issue.status = action.next_state
        # Get jira issue to perform transitions
        jira_issue = self.jira.issue(issue.key)
        for transition in action.transitions:
            self.transition_issue(jira_issue, transition)
        if action.assign_to_user:
            self.assign_issue(jira_issue, self.username)
        return issue

    def _convert_to_issue(self, jira_issue):
        """Convert to simplified issue."""
        i = Issue(
            jira_issue.key,
            jira_issue.fields.summary,
            self._get_type(jira_issue),
            self._get_status(jira_issue),
        )
        i.subtasks = self._get_subtasks(jira_issue)
        return i

    def _get_type(self, jira_issue):
        jira_type = jira_issue.fields.issuetype.name
        for type_mapping in self.workflow.types:
            if type_mapping.mapping == jira_type:
                return type_mapping.issue_type
        raise Exception(f"Unable to map issue type: {jira_type}")

    def _get_status(self, jira_issue):
        jira_status = jira_issue.fields.status.name
        for status_mapping in self.workflow.statuses:
            if jira_status in status_mapping.mapping:
                return status_mapping.status
        raise Exception(f"Unable to map issue status: {jira_status}")

    def _get_subtasks(self, jira_issue):
        try:
            return [
                self._convert_to_issue(subtask)
                for subtask in jira_issue.fields.subtasks
            ]
        except AttributeError as e:
            return []
