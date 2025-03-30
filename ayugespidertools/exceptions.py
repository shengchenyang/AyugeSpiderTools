# Define your exception here
class FieldAlreadyExistsError(Exception):
    def __init__(self, field_name: str):
        self.field_name = field_name
        self.message = f"Field {field_name} already exists"
        super().__init__(self.message)


class EmptyKeyError(Exception):
    def __init__(self):
        self.message = "The field name cannot be empty"
        super().__init__(self.message)


class NotConfigured(Exception):
    """Indicates a missing configuration situation"""

    ...


class UnsupportedError(Exception):
    """Unsupported operation or configuration"""

    ...


class AyugeSpiderToolsDeprecationWarning(Warning):
    """Warning category for deprecated features"""

    ...
