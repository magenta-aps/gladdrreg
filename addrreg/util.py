import logging

from datetime import datetime

from django.core import urlresolvers
from django.template import loader
from django.utils.translation import ugettext_lazy as _
from jsonview.decorators import _dump_json

# Our standard JSON output formats, when a non-primitive type is serialized

logger = logging.getLogger(__name__)


def json_serialize_object(obj):
    if isinstance(obj, datetime):
        return obj.strftime(format='%Y-%m-%dT%H:%M:%S%z')
    return None


def dump_json(data):
    return _dump_json(data)


def render_list(items):
    try:
        return loader.render_to_string('item_list.html', {
            'items': {
                item: urlresolvers.reverse(
                    ("admin:%s_%s_change" % (item._meta.app_label,
                                             item._meta.model_name)),
                    args=(item.id,)
                )
                for item in items
            }
        })
    except Exception:
        logger.exception('List rendering failed')
        return _('Error')
