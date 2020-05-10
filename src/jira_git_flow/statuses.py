from marshmallow import Schema, fields, post_load
OPEN = 'open'
IN_PROGRESS = 'in_progress'
REVIEW = 'review'
DONE = 'done'

STATUSES = [
    OPEN, IN_PROGRESS, REVIEW, DONE
]

class IssueStatusMapping():
    def __init__(self, status, mapping):
        self.status = status
        self.mapping = mapping

class IssueStatusMappingSchema(Schema):
    status = fields.Str()
    mapping = fields.Str()

    @post_load
    def deserialize(self, data, **kwargs):
        return IssueStatusMapping(**data)
