=================
Django API
=================

Django API is a way to cleanly specify and validate your Django_ APIs in a single block of code.

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

::

    from django_api.decorators import api
    @api({
        'accepts': {
            'x': forms.IntegerField(min_value=0),
            'y': forms.IntegerField(max_value=10, required=False),
            'u': User(),
        },
        'returns': [
            (200, 'Operation successful', ),
            (403, 'User does not have permission', ),
            (404, 'Resource not found', ),
            (404, 'User not found', ),
        ]
    })
    def add(request, *args, **kwargs):
        if not request.GET['x'] == 10:
            return JsonResponseForbidden()  # 403

        return HttpResponse()  # 200




If validation fails, a ``HTTP 400 - Bad request`` is returned to the client. For safety, ``django_api`` will perform validation only if ``settings.DEBUG = True`` i.e. production code remains unaffected. 


Advanced usage
--------------

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
    @api_returns([
        (200, 'Operation successful', ),
        (403, 'User does not have permission', ),
        (404, 'Resource not found', ),
        (404, 'User not found', ),
    )
    def add(request, *args, **kwargs):
        if not request.user.is_superuser:
            return JsonResponseForbidden()  # 403

        return HttpResponse()  # 200
