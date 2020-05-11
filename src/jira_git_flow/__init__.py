import click
from prompt_toolkit import prompt
from jira_git_flow import config
from jira_git_flow import actions
from jira_git_flow.credentials import CredentialsRepository, CredentialsCLI
from jira_git_flow.instances import InstanceCLI, InstanceRepository
from jira_git_flow.workflow import WorkflowRepository, WorkflowCLI
from jira_git_flow.projects import ProjectCLI, ProjectRepository
from jira_git_flow.workspaces import WorkspaceCLI, WorkspaceRepository, WorkspaceSchema
from jira_git_flow import git
from jira_git_flow.jira import Jira
from jira_git_flow import cli
from jira_git_flow import types
from jira_git_flow.issues import Issue, IssueRepository, IssuesCLI
from jira_git_flow.util import generate_branch_name

# Initialize repositories
credentials_repository = CredentialsRepository()
instance_repository = InstanceRepository()
workflow_repository = WorkflowRepository()
issue_repository = IssueRepository()
project_repository = ProjectRepository()
workspace_repository = WorkspaceRepository()

# Initialize workspace
workspace = workspace_repository.get_current_workspace()

# Initialize CLIs
credentials_cli = CredentialsCLI(credentials_repository)
instances_cli = InstanceCLI(instance_repository, credentials_repository)
workflow_cli = WorkflowCLI(workflow_repository)
issues_cli = IssuesCLI(issue_repository, workspace)
projects_cli = ProjectCLI(project_repository, instance_repository, workflow_repository)
workspace_cli = WorkspaceCLI(workspace_repository, project_repository)


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


@gfl.group(name="instances")
def instances():
    """Manage JIRA instances."""


@instances.command(name="add")
def add_instance():
    instances_cli.new()


@instances.command(name="list")
def list_instances():
    instances_cli.list()


@gfl.group(name="workflows")
def workflows():
    pass


@workflows.command(name="add")
def add_workflow():
    workflow_cli.new()


@workflows.command(name="list")
def list_workflows():
    workflow_cli.list()


@gfl.group(name="projects")
def projects():
    pass


@projects.command(name="add")
def add_project():
    projects_cli.new()


@projects.command(name="list")
def list_projects():
    projects_cli.list()


@gfl.group()
def workspaces():
    pass


@workspaces.command(name="list")
def list_workspaces():
    workspace_cli.list()


@gfl.command()
def init():
    workspace_cli.init()


@gfl.command()
@click.option("-k", "--key", is_flag=True)
@click.argument("keyword", nargs=-1, type=str)
def workon(key, keyword):
    """Work on story/issue."""
    require_workspace()
    if not keyword:
        issue = work_on_task()
    else:
        issue = get_issue_from_jira(key, keyword, types.STORY)
        issue_repository.save(issue)
    click.echo("Working on {}".format(issue))


@gfl.command()
def story():
    """Create a story"""
    create_issue(types.STORY)


@gfl.command()
def start():
    """Start story/task"""
    make_action(actions.START)


@gfl.command()
def subtask():
    """Create (work on) subtask."""
    create_issue(types.SUBTASK)


@gfl.command()
def task():
    """Create (work on) task"""
    create_issue(types.TASK)


@gfl.command()
def bug():
    """Create (work on) bugfix."""
    create_issue(types.BUG)


@gfl.command()
@click.option("-s", "--skip-pr", is_flag=True, default=False)
def review(skip_pr):
    """Move issue to review"""
    action = workspace.get_action(actions.REVIEW)
    issues = issues_cli.choose_by_status(action.initial_state)
    if not issues:
        return

    if config.CREATE_PULL_REQUEST:
        for issue in issues:
            skip_issue_pr = skip_pr or (issue.type == types.STORY)
            if not skip_issue_pr:
                branch = generate_branch_name(issue)
                try:
                    git.push(branch)
                except:
                    raise click.ClickException("Failed to push branch!")
                git.create_pull_request(branch)

    jira = workspace.get_jira_connection()
    for issue in issues:
        issue = jira.make_action(action, issue)
        issue_repository.update(issue)


@gfl.command()
def resolve():
    """Resolve issue"""
    make_action(actions.RESOLVE)


@gfl.command()
@click.argument("message", type=str)
def commit(message):
    """Commit for issue"""
    issue_key = workspace.current_issue
    git.commit("{} {}".format(issue_key, message))


@gfl.command()
def publish():
    """Push branch to origin"""
    issue = issue_repository.find_by_key(workspace.current_issue)
    branch = generate_branch_name(issue)
    git.push(branch)


@gfl.command()
def finish():
    """Finish story"""
    print(workspace.current_story)
    stories = issues_cli.choose_by_types(types.STORY)

    for story in stories:
        issue_repository.remove(story)

    print(workspace.current_story)
    if workspace.current_story is None:
        click.echo("Choose story to work on.")
        choices = issues_cli.choose_by_types(types.STORY)
        if choices:
            story = choices[0]
            workspace.current_story = story.key
            workspace_repository.update(workspace)


@gfl.command()
def status():
    """Get work status"""
    click.echo("Status:")
    issues_cli.choose_interactive(filter_function=lambda issue: False, show_only=True)


# @gfl.command()
# def sync():
#     """Sync stories between Jira and local storage"""
#     jira = workspace.get_jira_connection()
#     remote_stories = [
#         jira.get_issue_by_key(story.key) for story in storage.get_stories()
#     ]
#     storage.sync(remote_stories)


def work_on_task():
    """Work on task from local storage."""
    issue = issues_cli.choose_issue()
    if not issue:
        exit("Select issue!")
    if issue.type == "story":
        workspace.current_story = issue.key
    else:
        checkout_branch(issue)
        workspace.current_issue = issue.key
    workspace_repository.update(workspace)
    return issue


def checkout_branch(issue):
    """Checkout issue Git branch."""
    branch = generate_branch_name(issue)
    git.checkout(branch)


def create_issue(type, start_progress=True):
    """Create Jira issue and return model."""
    try:
        fields = issues_cli.new(type)

        jira = workspace.get_jira_connection()
        issue = jira.create_issue(fields)

        if start_progress:
            action = workspace.get_action(actions.START)
            jira.make_action(action, issue)

        issue_repository.save(issue)

        workspace.set_current_issue(issue)
        workspace_repository.update(workspace)

        return issue
    except Exception as e:
        raise click.ClickException(e)


def get_issue_from_jira(is_key, keyword, type):
    """
    Get issue from Jira.

    Issue can be searched by the keyword or specified via issue key.
    Return internal issue model.
    """
    try:
        jira = workspace.get_jira_connection()
        keyword = " ".join(keyword)
        if is_key:
            return jira.get_issue_by_key(keyword)

        issues = jira.search_issues(keyword, type=type)
        if not issues:
            exit("No issues found with selected keyword: {}!".format(keyword))
        elif len(issues) > 1:
            return issues_cli.choose_issues_from_simple_view(issues)
        else:
            return issues[0]

    except Exception as e:
        # raise click.ClickException(e)
        raise e


def make_action(action):
    action = workspace.get_action(action)
    issues = issues_cli.choose_by_status(action.initial_state)
    jira = workspace.get_jira_connection()
    for issue in issues:
        issue = jira.make_action(action, issue)
        issue_repository.update(issue)


def require_workspace():
    if not workspace:
        print("Cannot run outside of workspace")
        print("Run 'gfl init' to initialize workspace")
        exit(1)


if __name__ == "__main__":
    pass
