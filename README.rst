=================
Django API
=================

Django API is a way to cleanly specify and validate your Django_ APIs in a single block of code.
It provides a method to keep your API documentation and implementation consistent.

.. _Django: https://www.djangoproject.com/

------------
Dependencies
------------

None

------------
Installation
------------

To use ``django_api`` in your Django project it needs to be accessible by your 
Python installation::

	$ pip install django-api

(or simply place the ``django_api`` directory in your $PYTHON_PATH)

------------
Django Setup
------------

Add ``django_api`` to ``INSTALLED_APPS`` in your project's ``settings.py``.

Example::

	INSTALLED_APPS = (
		'django.contrib.auth',
		'django.contrib.contenttypes',
		'django.contrib.sessions',
		'django.contrib.sites',
		'django.contrib.admin',
		'django_api',
	)


-----
Usage
-----

Specify your API by using the ``@api`` decorator. The ``@api`` decorator takes a dictionary with two keys: ``accepts`` and ``returns``.

::

    from django_api.decorators import api
    @api({
        'accepts': {
        },
        'returns': {
        }
    })
    def add(request, *args, **kwargs):


accepts
-------

Describe the query parameters your API accepts by listing them out in the ``accepts`` dictionary. Each entry in the ``accepts`` section
maps a name to a Django_ form type.
Received query parameters are automatically converted to the specified type. If the parameter does not conform to the specification
the query fails to validate (see below).
Once validated, the variables will be placed in the ``request`` dictionary for use within the view.

::

    'accepts': {
        'x': forms.IntegerField(min_value=0),
        'y': forms.IntegerField(max_value=10, required=False),
        'u': User(),
    }
 

returns
-------

By default, the ``@api`` decorator checks that the returned response is of JSON type.

Specify the valid returned HTTP codes by listing them out in the ``returns`` dictionary.
Each entry in the dictionary maps a HTTP response code to a helpful message, explaining the outcome
of the action. The helpful message is for documentation purposes only.
If the response does not conform to the specification, the query will fail to validate (see below).

::

    'returns': {
        200: 'Addition successful',
        403: 'User does not have permission',
        404: 'Resource not found',
        404: 'User not found',
    }

Putting it all together, we have

::

    from django_api.decorators import api
    @api({
        'accepts': {
            'x': forms.IntegerField(min_value=0),
            'y': forms.IntegerField(max_value=10, required=False),
        },
        'returns': {
            200: 'Addition successful',
            403: 'User does not have permission',
            404: 'Resource not found',
            404: 'User not found',
        }
    })
    def add(request, *args, **kwargs):
        if not request.GET['x'] == 10:
            return JsonResponseForbidden()  # 403

        return HttpResponse()  # 200


Validation
----------
If validation fails, a ``HTTP 400 - Bad request`` is returned to the client. For safety, ``django_api`` will perform validation only if ``settings.DEBUG = True``.
This ensures that production code always remains unaffected. 


--------------
Advanced usage
--------------

Django Models
--------------

`@accepts` can be used to also accept your Django models through the object's `id`. For a Model `Model`, Django expects the query parameter to be name `model-id`.

::

    'accepts': {
        'x': forms.IntegerField(min_value=0),
        'y': forms.IntegerField(max_value=10, required=False),
        'u': User(),
    }

You can also simply choose to validate either only the parameters the
API accepts, or the return values of the API.

Example::

    from django_api.decorators import api_accepts
    @api_accepts({
        'x': forms.IntegerField(min_value=0),
        'y': forms.IntegerField(min_value=0),
    })
    def add(request, *args, **kwargs):
        x = request.POST['x']
        y = request.POST['y']

        # x and y are integers already.
        return HttpResponse('%d' % (x + y))


    from django_api.decorators import api_returns
    @api_returns({
        200: 'Operation successful',
        403: 'User does not have permission',
        404: 'Resource not found',
        404: 'User not found',
    })
    def add(request, *args, **kwargs):
        if not request.user.is_superuser:
            return JsonResponseForbidden()  # 403

        return HttpResponse()  # 200
