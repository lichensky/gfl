"""Git related functionality."""
import re
import webbrowser
from urllib.parse import quote_plus

import click
import subprocess
from subprocess import check_output


def checkout(branch):
    """Checkout branch"""
    click.echo("Checkout on branch {}...".format(branch))
    if branch_exists(branch):
        check_output(["git", "checkout", branch])
        return
    check_output(["git", "checkout", "-b", branch])


def commit(issue_key, message, skip_add):
    """Commit."""
    try:
        commit_msg = f"{issue_key} {message}"
        if not skip_add:
            check_output(["git", "add", "."])
        cmd = ["git", "commit",  "-m", "{}".format(commit_msg)]
        check_output(cmd)
    except subprocess.CalledProcessError as e:
        print(e.output.decode())
        raise e


def push(branch, remote="origin"):
    """Push branch."""
    check_output(["git", "push", "-u", remote, branch])


def branch_exists(branch_name):
    """Check if branch exists eiither local or remote"""
    branches = check_output(["git", "branch", "-a"]).decode("utf-8").split("\n")
    return bool([branch for branch in branches if branch_name in branch])
