import os
import json

from tinydb import TinyDB, Query

from jira_git_flow import config


class Repository:
    def __init__(self, model, schema, path):
        self.db = TinyDB(os.path.join(config.DATA_DIR, path))
        self.schema = schema
        self.model = model

    def save(self, model):
        self.db.insert(self.schema.dump(model))

    def all(self):
        return [self.schema.load(entity) for entity in self.db.all()]


class EntityRepository(Repository):
    def update(self, model):
        serialized = self.schema.dump(model)
        self.db.update(serialized, Query().id == model.id)

    def remove(self, model):
        self.db.remove(Query().id == model.id)

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
