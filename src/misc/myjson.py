import datetime

import bson
from bson import json_util
from flask import json


def default(obj, json_options=bson.json_util.DEFAULT_JSON_OPTIONS):
    if isinstance(obj, datetime.datetime):
        return obj.strftime('%Y%m%dT%H%M%S.%f')[:-3]+'Z'
    if isinstance(obj, bson.Timestamp):
        return obj.as_datetime().strftime('%Y%m%dT%H%M%S.%f')[:-3] + 'Z'
    if isinstance(obj, bson.ObjectId):
        return str(obj)
    return json_util.default(obj, json_options)


class CustomEncoder(json.JSONEncoder):
    """A C{json.JSONEncoder} subclass to encode documents that have fields of
    type C{bson.objectid.ObjectId}, C{datetime.datetime}
    """

    def default(self, obj):
        if isinstance(obj, bson.objectid.ObjectId):
            return str(obj)
        elif isinstance(obj, datetime.datetime):
            return default(obj)
        elif isinstance(obj, bson.Timestamp):
            return obj.as_datetime().isoformat()
        elif isinstance(obj, float) and (obj == 0.0):
            return int(0)
        return json.JSONEncoder.default(self, obj)
