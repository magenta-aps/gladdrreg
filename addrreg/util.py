from datetime import datetime

from jsonview.decorators import _dump_json

# Our standard JSON output formats, when a non-primitive type is serialized


def json_serialize_object(obj):
    if isinstance(obj, datetime):
        return obj.strftime(format='%Y-%m-%dT%H:%M:%S%z')
    return None


def dump_json(data):
    return _dump_json(data)
