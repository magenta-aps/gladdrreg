from django.core.serializers import python
from django.utils.encoding import is_protected_type


class Serializer(python.Serializer):
    def handle_fk_field(self, obj, field):
        if hasattr(field.remote_field.model, 'natural_key'):
            related = getattr(obj, field.name)
            if related:
                value = related.natural_key()
            else:
                value = None
        else:
            value = getattr(obj, field.get_attname())
            if not is_protected_type(value):
                value = field.value_to_string(obj)

        self._current[field.name] = value


def Deserializer(*args, **kwargs):
    python.Deserializer(*args, **kwargs)
