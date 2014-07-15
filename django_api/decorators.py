import logging
from functools import wraps
from django import forms
from django.conf import settings
from django.db import models
from django.utils import simplejson
from django_api.json import JsonResponse
from django_api.json import JsonResponseBadRequest
from django_api.json import JsonResponseNotFound


logger = logging.getLogger(__name__)


class ValidatedRequest(object):
    """
    A wrapper for Request objects that behaves like a Request in every way
    except that GET/POST data is replaced with a cleaned version (per Django
    forms).

    See the @api decorator for more details.
    """

    def __init__(self, orig_request, form):
        self._orig_request = orig_request
        self._form = form

    def __getattr__(self, name):
        if name in ['GET', 'POST']:
            return self._form.cleaned_data
        else:
            return object.__getattribute__(self._orig_request, name)


def api_accepts(fields):
    """
    Define the accept schema of an API (GET or POST).

    'fields' is a dict of Django form fields keyed by field name that specifies
    the form-urlencoded fields that the API accepts*.

    The view function is then called with GET/POST data that has been cleaned
    by the Django form.

    In debug and test modes, failure to validate the fields will result in a
    400 Bad Request response.
    In production mode, failure to validate will just log a
    warning, unless overwritten by a 'strict' setting.

    For example:

    @api_accepts({
        'x': forms.IntegerField(min_value=0),
        'y': forms.IntegerField(min_value=0),
    })
    def add(request, *args, **kwargs):
        x = request.POST['x']
        y = request.POST['y']

        # x and y are integers already.
        return HttpResponse('%d' % (x + y))


    *: 'fields' can also include Django models as {'key': Model()}. If present,
    api_accepts will look for the field keyed by '<key>-id'
    and pick the object that has that primary key. For example, if the entry is
    {'course': Course()}, it will search for the key course_id='course-id' in
    the request object, and find the object Course.objects.get(pk=course_id)
    """
    def decorator(func):
        @wraps(func)
        def wrapped_func(request, *args, **kwargs):
            if request.method not in ['GET', 'POST']:
                return func(request, *args, **kwargs)

            # The fields dict passed into the type() function is modified, so
            # send in a copy instead.
            form_class = type('ApiForm', (forms.Form,), fields.copy())
            form = form_class(getattr(request, request.method))

            if not form.is_valid():
                if settings.DEBUG:
                    return JsonResponseBadRequest(
                        'failed to validate: %s' % dict(form.errors)
                    )
                else:
                    logger.warn(
                        'input to \'%s\' failed to validate: %s',
                        request.path,
                        dict(form.errors)
                    )
                    return func(request, *args, **kwargs)

            # Clean any models.Model fields, by looking up object based on
            # primary key in request.
            for (field_name, field_instance) in fields.items():
                if isinstance(field_instance, models.Model):
                    field_type = type(field_instance)
                    # TODO: irregular, should we remove?
                    field_id = '%s-id' % field_name
                    if field_id not in request.REQUEST:
                        return JsonResponseBadRequest(
                            'field %s not present' % field_name
                        )
                    field_pk = int(request.REQUEST[field_id])
                    try:
                        field_value = field_type.objects.get(pk=field_pk)
                    except field_type.DoesNotExist:
                        return JsonResponseNotFound(
                            '%s with pk=%d does not exist' % (
                                field_type, field_pk
                            )
                        )
                    form.cleaned_data[field_name] = field_value

            validated_request = ValidatedRequest(request, form)
            return func(validated_request, *args, **kwargs)
        return wrapped_func
    return decorator


def api_returns(return_values):
    """
    Define the return schema of an API.

    'return_values' is a dictionary mapping
    HTTP return code => documentation
    In addition to validating that the status code of the response belongs to
    one of the accepted status codes, it also validates that the returned
    object is JSON (derived from JsonResponse)

    In debug and test modes, failure to validate the fields will result in a
    400 Bad Request response.
    In production mode, failure to validate will just log a
    warning, unless overwritten by a 'strict' setting.

    For example:

    @api_returns({
        200: 'Operation successful',
        403: 'User does not have persion',
        404: 'Resource not found',
        404: 'User not found',
    })
    def add(request, *args, **kwargs):
        if not request.user.is_superuser:
            return JsonResponseForbidden()  # 403

        return HttpResponse()  # 200
    """
    def decorator(func):
        @wraps(func)
        def wrapped_func(request, *args, **kwargs):
            return_value = func(request, *args, **kwargs)

            if not isinstance(return_value, JsonResponse):
                if settings.DEBUG:
                    return JsonResponseBadRequest('API did not return JSON')
                else:
                    logger.warn('API did not return JSON')

            accepted_return_codes = return_values.keys()
            # Never block 500s - these should be handled by other
            # reporting mechanisms
            accepted_return_codes.append(500)

            if return_value.status_code not in accepted_return_codes:
                if settings.DEBUG:
                    return JsonResponseBadRequest(
                        'API returned %d instead of acceptable values %s' %
                        (return_value.status_code, accepted_return_codes)
                    )
                else:
                    logger.warn(
                        'API returned %d instead of acceptable values %s',
                        return_value.status_code,
                        accepted_return_codes,
                    )

            return return_value
        return wrapped_func
    return decorator


def api(accept_return_dict):
    """
    Wrapper that calls @api_accepts and @api_returns in sequence.
    For example:

    @api({
        'accepts': {
            'x': forms.IntegerField(min_value=0),
            'y': forms.IntegerField(min_value=0),
        },
        'returns': [
            200: 'Operation successful',
            403: 'User does not have persion',
            404: 'Resource not found',
            404: 'User not found',
        ]
    })
    def add(request, *args, **kwargs):
        if not request.GET['x'] == 10:
            return JsonResponseForbidden()  # 403

        return HttpResponse()  # 200
    """
    def decorator(func):
        @wraps(func)
        def wrapped_func(request, *args, **kwargs):
            @api_accepts(accept_return_dict['accepts'])
            @api_returns(accept_return_dict['returns'])
            def apid_fnc(request, *args, **kwargs):
                return func(request, *args, **kwargs)

            return apid_fnc(request, *args, **kwargs)
        return wrapped_func
    return decorator


def validate_json_request(required_fields):
    """
    Return a decorator that ensures that the request passed to the view
    function/method has a valid JSON request body with the given required
    fields.  The dict parsed from the JSON is then passed as the second
    argument to the decorated function/method.  For example:

    @json_request({'name', 'date'})
    def view_func(request, request_dict):
        ...
    """
    def decorator(func):
        @wraps(func)
        def wrapped_func(request, *args, **kwargs):
            try:
                request_dict = simplejson.loads(request.raw_post_data)
            except ValueError as e:
                return JsonResponseBadRequest('invalid POST JSON: %s' % e)

            for k in required_fields:
                if k not in request_dict:
                    return JsonResponseBadRequest(
                        'POST JSON must contain property \'%s\'' % k)

            return func(request, request_dict, *args, **kwargs)
        return wrapped_func
    return decorator
