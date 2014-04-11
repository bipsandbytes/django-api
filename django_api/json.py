import datetime
import decimal

from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.utils import simplejson


class JsonEncoder(simplejson.JSONEncoder):
    """
    JSON encoder that converts additional Python types to JSON.
    """
    def default(self, obj):
        """
        Converts datetime objects to ISO-compatible strings.
        Converts Decimal objects to floats during json serialization.
        """
        if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
            return obj.isoformat()
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        elif isinstance(obj, QuerySet):
            return list(obj)
        else:
            return None


class JsonResponse(HttpResponse):
    def __init__(self, data={}):
        super(JsonResponse, self).__init__(content_type='application/json')
        self.set_content(data)

    def set_content(self, data):
        json_encoder = JsonEncoder(separators=(',', ':'))
        content = json_encoder.encode(data)
        self.content = content


class JsonResponseCreated(JsonResponse):
    status_code = 201


class JsonResponseAccepted(JsonResponse):
    status_code = 202


class JsonResponseBadRequest(JsonResponse):
    status_code = 400


class JsonResponseWithStatus(JsonResponse):
    def __init__(self, error_message='', error_type=None, field_errors=None):
        data = {
            'error_type': error_type or self.status_code,
            'error_message': error_message
        }
        if field_errors:
            data['field_errors'] = field_errors
        super(JsonResponseWithStatus, self).__init__(data)


class JsonResponseSeeOther(JsonResponseWithStatus):
    status_code = 302


class JsonResponseForbidden(JsonResponseWithStatus):
    status_code = 403


class JsonResponseConflict(JsonResponseWithStatus):
    status_code = 409


class JsonResponseError(JsonResponseWithStatus):
    status_code = 500


class JsonResponseUnauthorized(JsonResponseWithStatus):
    status_code = 401


class JsonResponseNotFound(JsonResponseWithStatus):
    status_code = 404


class JsonResponseNotSupported(JsonResponseWithStatus):
    status_code = 400
