import os
import json

from tinydb import TinyDB, Query

from jira_git_flow import config

class Model():
    def to_db(self):
        """Convert model to DB representation."""
        return json.loads(json.dumps(self, default=lambda o: o.__dict__))

    @classmethod
    def from_db(cls, db):
        return cls(**db)


class Repository():
    def __init__(self, model, path):
        self.db = TinyDB(os.path.join(config.DATA_DIR, path))
        self.model = model

    def save(self, model):
        self.db.insert(model.to_db())

    def all(self):
        return [self.model.from_db(entity) for entity in self.db.all()]


class EntityRepository(Repository):
    def ids(self):
        return [entity.id for entity in self.all()]

    def exists(self, id):
        Entity = Query()
        return bool(self.db.search(Entity.id.matches(id)))

    def find_by_id(self, id):
        Entity = Query()
        try:
            return self.db.search(Entity.id == id)[0]
        except IndexError:
            return None
