=================
Django API
=================

Django API is a way to cleanly specify and validate your Django_ APIs in a single block of code.
It provides a method to keep your API documentation and implementation consistent.

::

    from django import forms
    from django_api.decorators import api
    from django_api.json_helpers import JsonResponse
    from django_api.json_helpers import JsonResponseForbidden


    @api({
        'accepts': {
            'x': forms.IntegerField(min_value=0),
            'y': forms.IntegerField(max_value=10),
        },
        'returns': {
            200: 'Addition successful',
        }
    })
    def add(request, *args, **kwargs):
        # `x` and `y` have been validated, and are integers
        # so we can safely perform arithmetic operations on them
        return JsonResponse({
            'sum': request.GET['x'] + request.GET['y']
        })


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
maps a name to a `Django form field
<https://docs.djangoproject.com/en/1.7/ref/forms/fields/>`_ type.
Received query parameters are automatically converted to the specified type. If the parameter does not conform to the specification
the query fails to validate (see below).
Once validated, the variables will be placed in the ``request`` dictionary for use within the view.


::

    'accepts': {
        'x': forms.IntegerField(min_value=0),
        'y': forms.IntegerField(max_value=10, required=False),
        'u': User(),
    }
 
Since each parameter is specified using a Django form field, any argument that its  class constructor takes can be used. Examples include 

* ``required``
* ``initial``
* ``max_length`` for ``CharField``
* ``min_value`` for ``IntegerField``

For a full reference, please `see here <https://docs.djangoproject.com/en/1.7/ref/forms/fields/>`_.

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


Validation
----------
If validation fails, a ``HTTP 400 - Bad request`` is returned to the client. For safety, ``django_api`` will perform validation only if ``settings.DEBUG = True``.
This ensures that production code always remains unaffected. 


Testing
----------
Run the tests with the folllowing command

::

    python manage.py test django_api


--------------
Advanced usage
--------------

Django Models
--------------

``@accepts`` can be used to also accept your Django models through the object's ``id``. For a Model ``Model``, Django expects the query parameter to be name ``model-id``.

::

    'accepts': {
        'x': forms.IntegerField(min_value=0),
        'y': forms.IntegerField(max_value=10, required=False),
        'u': User(),
    }

You can also simply choose to validate either only the parameters the
API accepts, or the return values of the API.

Example::


    from django import forms
    from django_api.decorators import api_accepts
    from django_api.json_helpers import JsonResponse
    from django_api.json_helpers import JsonResponseForbidden


    @api_accepts({
        'x': forms.IntegerField(min_value=0),
        'y': forms.IntegerField(min_value=0),
    })
    def add(request, *args, **kwargs):
        return JsonResponse({
            'sum': request.GET['x'] + request.GET['y']
        })




    from django import forms
    from django_api.decorators import api_returns
    from django_api.json_helpers import JsonResponse
    from django_api.json_helpers import JsonResponseForbidden


    @api_returns({
        200: 'Operation successful',
        403: 'User does not have permission',
        404: 'Resource not found',
        404: 'User not found',
    })
    def add(request, *args, **kwargs):
        return JsonResponse({
            'sum': request.GET['x'] + request.GET['y']
        })
