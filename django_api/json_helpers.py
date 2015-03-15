from django.core import serializers
from django.db import models
from django.forms.models import model_to_dict
from django.http import HttpResponse


class JsonResponseEncoder(serializers.json.DjangoJSONEncoder):
    """
    JSON encoder that converts Django types to JSON.
    """
    def default(self, obj):
        """
        Convert QuerySet objects to their list counter-parts
        """
        if isinstance(obj, models.Model):
            return self.encode(model_to_dict(obj))
        elif isinstance(obj, models.query.QuerySet):
            return serializers.serialize('json', obj)
        else:
            return super(JsonResponseEncoder, self).default(obj)


class JsonResponse(HttpResponse):
    def __init__(self, data={}):
        super(JsonResponse, self).__init__(content_type='application/json')
        self.set_content(data)

    def set_content(self, data):
        json_encoder = JsonResponseEncoder(separators=(',', ':'))
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
