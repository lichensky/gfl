from marshmallow import Schema, fields, post_load

STORY = 'story'
SUBTASK = 'subtask'
TASK = 'task'
BUG = 'bug'

TYPES = [STORY, SUBTASK, TASK, BUG]

class IssueTypeMapping():
    def __init__(self, issue_type, mapping, prefix):
        self.issue_type = issue_type
        self.mapping = mapping
        self.prefix = prefix

class IssueTypeMappingSchema(Schema):
    issue_type = fields.Str()
    mapping = fields.Str()
    prefix = fields.Str()

    @post_load
    def deserialize(self, data, **kwargs):
        return IssueTypeMapping(**data)
