"""Utilities"""
import re
from jira_git_flow import config
from jira_git_flow.issues import Issue


def generate_branch_name(issue):
    """Generate branch name from issue"""
    issue_model = Issue.from_jira(issue)
    prefix = config.ISSUE_TYPES[issue_model.type]['prefix']
    summary = re.sub(r"[^a-zA-Z0-9]+", ' ', issue_model.summary).lower().replace(' ', '-')
    branch = '{}{}-{}'.format(prefix, issue_model.key, summary)
    return branch[0:70]
