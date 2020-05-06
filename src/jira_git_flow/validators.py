from prompt_toolkit.validation import Validator, ValidationError

class NameValidator(Validator):
    def __init__(self, resource, repository):
        self.repository = repository
        self.resource = resource

    def validate(self, document):
        if self.repository.find_by_name(document.text):
            raise ValidationError(message='%s name already exists' % self.resource)


class ExistenceValidator(Validator):
    def __init__(self, resource, repository):
        self.resource = resource
        self.repository = repository

    def validate(self, document):
        name = document.text
        if not self.repository.exists(name):
            raise ValidationError(message="%s: %s not exists" % (self.resource, name))
