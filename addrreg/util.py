from datetime import datetime


# Our standard JSON output formats, when a non-primitive type is serialized
def json_serialize_object(obj):
    if isinstance(obj, datetime):
        return obj.strftime(format='%Y-%m-%dT%H:%M:%S%z')
    return None
