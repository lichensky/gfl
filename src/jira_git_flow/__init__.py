import click
from prompt_toolkit import prompt
from jira_git_flow import config
from jira_git_flow.credentials import CredentialsRepository, CredentialsCLI
from jira_git_flow.instances import InstanceCLI, InstanceRepository
from jira_git_flow.workflow import WorkflowRepository, WorkflowCLI
from jira_git_flow.projects import ProjectCLI
from jira_git_flow import git
from jira_git_flow.jira_api import Jira
from jira_git_flow import cli
from jira_git_flow.issues import Issue, IssueRepository, IssuesCLI
from jira_git_flow.storage import storage
from jira_git_flow.util import generate_branch_name

# Initialize repositories
credentials_repository = CredentialsRepository()
instance_repository = InstanceRepository()
workflow_repository = WorkflowRepository()
issue_repository = IssueRepository()

# Initialize CLIs
credentials_cli = CredentialsCLI(credentials_repository)
instances_cli = InstanceCLI(instance_repository, credentials_repository)
workflow_cli = WorkflowCLI(workflow_repository)
projects_cli = ProjectCLI()
issues_cli = IssuesCLI(issue_repository)

@click.group(name="git-flow")
def gfl():
    """Git flow."""


@gfl.group(name="credentials")
def credentials():
    """Manage JIRA credentials."""
    pass

@credentials.command(name="add")
def add_credentials():
    """Add new credentials."""
    credentials_cli.new()

@credentials.command(name="list")
def list_credentials():
    """List available credentials."""
    credentials_cli.list()

@gfl.group(name="instance")
def instance():
    """Manage JIRA instances."""

@instance.command(name="add")
def add_instance():
    instances_cli.new()

@instance.command(name="list")
def list_instances():
    instances_cli.list()

@gfl.group(name="workflow")
def workflow():
    pass

@workflow.command(name="add")
def add_workflow():
    workflow_cli.new()

@gfl.group(name="project")
def project():
    pass

@project.command(name="add")
def add_project():
    projects_cli.new()


@gfl.command()
@click.option('-k', '--key', is_flag=True)
@click.argument('keyword', nargs=-1, type=str)
def workon(key, keyword):
    """Work on story/issue."""
    if not keyword:
        issue = work_on_task()
    else:
        issue = get_issue_from_jira(key, keyword, 'story')
        issue_repository.save(issue)
    click.echo('Working on {}'.format(issue))


@gfl.command()
def story():
    """Create a story"""
    create_issue('story', subtask=False)


@gfl.command()
def start():
    """Start story/task"""
    _change_status('start_progress')


@gfl.command()
def feature():
    """Create (work on) feature."""
    create_subtask('feature')


@gfl.command()
def bug():
    """Create (work on) bugfix."""
    create_subtask('bug')


@gfl.command()
@click.option('-s', '--skip-pr', is_flag=True, default=False)
def review(skip_pr):
    """Move issue to review"""
    action = 'review'
    issues = _get_issues_by_action(action)

    if config.CREATE_PULL_REQUEST:
        for issue in issues:
            skip_issue_pr = skip_pr or (issue.type == 'story')
            if not skip_issue_pr:
                branch = generate_branch_name(issue)
                git.push(branch)
                git.create_pull_request(branch)

    jira = connect()
    for issue in issues:
        _make_action(jira, issue, action)


@gfl.command()
def resolve():
    """Resolve issue"""
    _change_status('resolve')


@gfl.command()
@click.argument('message', type=str)
def commit(message):
    """Commit for issue"""
    issue_key = storage.get_current_issue().key
    git.commit('{} {}'.format(issue_key, message))


@gfl.command()
def publish():
    """Push branch to origin"""
    branch = generate_branch_name(storage.get_current_issue())
    git.push(branch)


@gfl.command()
def finish():
    """Finish story"""
    stories = cli.choose_by_types('story')
    for story in stories:
        storage.finish(story)

    if storage.get_current_story() is None and storage.get_stories():
        click.echo('Choose story to work on.')
        choices = cli.choose_by_types('story')
        if choices:
            story = choices[0]
            storage.work_on_story(story)


@gfl.command()
def status():
    """Get work status"""
    click.echo("You're working on story: {}".format(storage.get_current_story()))
    click.echo("You're working on issue: {}".format(storage.get_current_issue()))
    click.echo("Stories:")
    issues_cli.choose_interactive(filter_function=lambda issue: False)


@gfl.command()
def sync():
    """Sync stories between Jira and local storage"""
    jira = connect()
    remote_stories = [jira.get_issue_by_key(story.key) for story in storage.get_stories()]
    storage.sync(remote_stories)


def work_on_task():
    """Work on task from local storage."""
    issue = issues_cli.choose_issue()
    if not issue:
        exit('Select issue!')
    if issue.type == 'story':
        storage.work_on_story(issue)
    else:
        checkout_branch(issue)
        storage.work_on_issue(issue)
    return issue


def checkout_branch(issue):
    """Checkout issue Git branch."""
    branch = generate_branch_name(issue)
    git.checkout(branch)


def create_issue(type, subtask, start_progress=True):
    """Create Jira issue and return model."""
    try:
        fields = cli.get_issue_fields(type, subtask)

        jira = connect()
        issue = Issue.from_jira(jira.create_issue(fields))

        if start_progress:
            _make_action(jira, issue, 'start_progress')

        storage.add_issue(issue)

        return issue
    except Exception as e:
        raise click.ClickException(e)


def create_subtask(type):
    """Create subtask and checkout branch."""
    subtask = create_issue(type, True)
    checkout_branch(subtask)


def get_issue_from_jira(is_key, keyword, type):
    """
    Get issue from Jira.

    Issue can be searched by the keyword or specified via issue key.
    Return internal issue model.
    """
    try:
        jira = connect()
        keyword = ' '.join(keyword)
        if is_key:
            issue = jira.get_issue_by_key(keyword)
        else:
            issues = jira.search_issues(keyword, type=type)
            if not issues:
                exit('No issues found with selected keyword: {}!'.format(keyword))
            elif len(issues) > 1:
                issue = issues_cli.choose_issues_from_simple_view(issues)
            else:
                issue = issues[0]

        return Issue.from_jira(issue)
    except Exception as e:
        # raise click.ClickException(e)
        raise e



def _get_issues_by_action(action):
    status = _get_action_status(action)
    issues = cli.choose_by_status(status)
    return issues


def _change_status(action, issues=None):
    issues = _get_issues_by_action(action)
    jira = connect()
    for issue in issues:
        _make_action(jira, issue, action)


def _make_action(jira, issue, action_to_perform):
    action = _get_issue_actions(issue)[action_to_perform]
    issue.status = action['next_state']
    jira_issue = jira.get_issue_by_key(issue.key)
    for transition in action['transitions']:
        jira.transition_issue(jira_issue, transition)
    _assign_issue(jira, jira_issue, action)
    storage.update_issue(issue)


def _get_issue_actions(issue):
    default_actions = config.ACTIONS['default']
    if issue.type in config.ACTIONS:
        actions = default_actions
        for action, parameters in config.ACTIONS[issue.type].items():
            for parameter, value in parameters.items():
                actions[action][parameter] = value
        return {k: v for k, v in actions.items() if k in config.ACTIONS[issue.type]}
    return default_actions


def _get_action_status(action):
    return config.ACTIONS['default'][action]['current_state']


def _assign_issue(jira, jira_issue, action):
    if 'assign_to_user' in action and action['assign_to_user']:
        jira.assign_issue(jira_issue, config.USERNAME)
    else:
        jira.assign_issue(jira_issue, None)


def connect():
    """Connect to JIRA and return Jira instance."""
    user = config.USERNAME if config.USE_USERNAME else config.EMAIL
    return Jira(config.URL, user, config.TOKEN, config.PROJECT, config.MAX_RESULTS)


if __name__ == "__main__":
    pass
