import os
from tinydb import TinyDB, Query
from prompt_toolkit import prompt, print_formatted_text, HTML

db_path = os.path.expanduser('~') + '/.config/jira-git-flow/credentials.db'
db = TinyDB(db_path)

class Credentials(object):
    """Credentials object"""
    def __init__(self, name, username, email, token):
        self.name = name
        self.username = username
        self.email = email
        self.token = token

    def save(self):
        db.insert(self.__dict__)

    @classmethod
    def from_db(cls, db):
        return cls(db['name'], db['username'], db['email'], db['token'])


class CredentialsRepository(object):
    """Credentials manager"""
    def add(self):
        """Add new credentials."""
        name = prompt("Credentials name: ")
        email = prompt("Email: ")
        username = prompt("Username: ")
        token = prompt("Token/password: ", is_password=True)

        credentials = Credentials(name, username, email, token)
        credentials.save()

    def list_credentials(self):
        """List all credentials."""
        for cred in db:
            print_formatted_text(HTML("<b>Credentials:</b> %s" % cred['name']))
            print_formatted_text(HTML("  <b>Username:</b> %s" % cred['username']))
            print_formatted_text(HTML("  <b>Email:</b> %s" % cred['email']))

    def get_names(self):
        return [c['name'] for c in db.all()]