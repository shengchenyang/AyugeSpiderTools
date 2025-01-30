# Define your exception here
class FieldAlreadyExistsError(Exception):
    def __init__(self, field_name: str):
        self.field_name = field_name
        self.message = f"字段 {field_name} 已存在！"
        super().__init__(self.message)


class EmptyKeyError(Exception):
    def __init__(self):
        self.message = "字段名不能为空！"
        super().__init__(self.message)


class NotConfigured(Exception):
    """Indicates a missing configuration situation"""

    ...


class AyugeSpiderToolsDeprecationWarning(Warning):
    """Warning category for deprecated features"""

    ...
