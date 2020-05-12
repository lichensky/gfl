"""Utilities"""
import re
from jira_git_flow import config
from jira_git_flow.issues import Issue


def generate_branch_name(workflow, issue):
    """Generate branch name from issue"""
    prefix = workflow.get_branch_prefix(issue)
    summary = re.sub(r"[^a-zA-Z0-9]+", ' ', issue.summary).lower().replace(' ', '-')
    branch = '{}{}-{}'.format(prefix, issue.key, summary)
    return branch[0:70]
