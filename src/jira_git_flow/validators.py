from prompt_toolkit.validation import Validator, ValidationError

class UniqueID(Validator):
    def __init__(self, resource, repository):
        self.repository = repository
        self.resource = resource

    def validate(self, document):
        id = document.text
        if self.repository.find_by_id(id):
            raise ValidationError(message=f"{self.resource} {id} already exists")


class ExistenceValidator(Validator):
    def __init__(self, resource, repository):
        self.resource = resource
        self.repository = repository

    def validate(self, document):
        id = document.text
        if not self.repository.exists(id):
            raise ValidationError(message="%s: %s not exists" % (self.resource, id))
