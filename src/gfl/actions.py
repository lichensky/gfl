from marshmallow import Schema, fields, post_load

from gfl import statuses

START = "start"
REVIEW = "review"
RESOLVE = "resolve"

ACTION_NAMES = [START, REVIEW, RESOLVE]


class Action:
    def __init__(self, name, initial_state, next_state):
        self.name = name
        self.initial_state = initial_state
        self.transitions = []
        self.next_state = next_state
        self.assign_to_user = False


class ActionSchema(Schema):
    name = fields.Str()
    initial_state = fields.Str()
    transitions = fields.List(fields.Str(), allow_none=True)
    next_state = fields.Str()
    assign_to_user = fields.Bool()

    @post_load
    def deserialize(self, data, **kwargs):
        a = Action(data["name"], data["initial_state"], data["next_state"])
        a.transitions = data["transitions"]
        a.assign_to_user = data["assign_to_user"]
        return a


class Start(Action):
    def __init__(self):
        super().__init__(START, statuses.OPEN, statuses.IN_PROGRESS)


class Review(Action):
    def __init__(self):
        super().__init__(REVIEW, statuses.IN_PROGRESS, statuses.REVIEW)


class Resolve(Action):
    def __init__(self):
        super().__init__(RESOLVE, statuses.REVIEW, statuses.DONE)


ACTIONS = [Start, Review, Resolve]
