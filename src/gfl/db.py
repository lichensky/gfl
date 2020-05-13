import os
import json

from marshmallow import fields
from tinydb import TinyDB, Query

from gfl import config


class EntityNotFound(Exception):
    pass


class ForeignEntity(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        return value.id

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            repository = self.repository()
            obj = repository.find_by_id(value)
            return obj
        except EntityNotFound:
            return None


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
            return self.schema.load(self.db.search(Entity.id == id)[0])
        except IndexError:
            raise EntityNotFound(f"Entity not found, ID: {id}")
