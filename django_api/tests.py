# -*- coding: utf-8 -*-
import logging
from django.utils import simplejson
from django import forms
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django_api.decorators import api
from django_api.decorators import api_accepts
from django_api.decorators import api_returns
from django_api.json import JsonResponse
from django_api.json import JsonResponseForbidden
from django_api.json import JsonResponseAccepted
from django_api.json import JsonResponseWithStatus
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class SimpleTest(TestCase):

    def test_api_accepts_decorator_debug(self):
        """
        Test the @api_accepts decorator (with DEBUG=True).
        """
        rf = RequestFactory()

        # Test that POSTs are validated.
        @api_accepts({
            'im_required': forms.IntegerField(),
        })
        def my_post_view(request, *args, **kwargs):
            self.assertIsInstance(request.POST['im_required'], int)
            return JsonResponseWithStatus('post called')

        request = rf.post('/post_success', data={'im_required': '10'})
        response = my_post_view(request)
        self.assertEquals(response.status_code, 200)
        response_json = simplejson.loads(response.content)
        self.assertEquals(response_json['error_message'], 'post called')

        # Test that GETs are validated.
        @api_accepts({
            'im_required': forms.IntegerField(),
        })
        def my_get_view(request, *args, **kwargs):
            self.assertIsInstance(request.GET['im_required'], int)
            return JsonResponseWithStatus('get called')

        request = rf.get('/get_success', data={'im_required': '10'})
        response = my_get_view(request)
        self.assertEquals(response.status_code, 200)
        response_json = simplejson.loads(response.content)
        self.assertEquals(response_json['error_message'], 'get called')

        # Test that POSTs are validated.
        @api_accepts({
            'im_required': forms.IntegerField(),
        })
        def my_failed_post_view(request, *args, **kwargs):
            return JsonResponseWithStatus('not called on failure')

        # Test that failed validation results in a 400 Bad Request when DEBUG
        # == True.
        request = rf.post('/post_failure', data={'hello': 'world'})
        response = my_failed_post_view(request)
        self.assertEquals(response.status_code, 400)

        # Test that Django models can be accepted by @api
        user = User.objects.create()
        @api_accepts({
            'im_required': forms.IntegerField(),
            'user': User(),
        })
        def model_view(request, *args, **kwargs):
            self.assertTrue(request.GET['user'].id == user.id)
            return JsonResponse()

        request = rf.get('/model_failure', data={'im_required': 10, 'user-id': 99999})
        response = model_view(request)
        self.assertEquals(response.status_code, 404)

        request = rf.get('/model_success', data={'im_required': 10, 'user-id': user.id})
        response = model_view(request)
        self.assertEquals(response.status_code, 200)


    @override_settings(TESTING=False)
    @override_settings(DEBUG=False)
    def test_api_accepts_decorator(self):
        """
        Test that failures to validate with the @api_accepts decorator do not result in
        400 Bad Requests in production.

        This is a temporary measure to avoid breaking production as we apply
        this decorator to existing APIs.
        """
        original_log_level = logger.level
        logger.setLevel(1000)

        # Test that POSTs are validated.
        @api_accepts({
            'im_required': forms.IntegerField(),
        })
        def my_failed_post_view(request, *args, **kwargs):
            return JsonResponseWithStatus('still called on failure')

        rf = RequestFactory()
        request = rf.post('/post_failure', data={'hello': 'world'})
        response = my_failed_post_view(request)
        self.assertEquals(response.status_code, 200)
        response_json = simplejson.loads(response.content)
        self.assertEquals(response_json['error_message'], 'still called on failure')
        logger.setLevel(original_log_level)

    def test_api_returns_decorator_debug(self):
        """
        Test that the @api_returns decorator (in debug mode)
        """
        @api_returns({
            200: 'OK',
            403: 'Permission denied',
        })
        def simple_view(request):
            if 'ok' in request.GET:
                return JsonResponse()
            elif 'noperm' in request.GET:
                return JsonResponseForbidden()
            else:
                return JsonResponseAccepted()  # Not declared in @api_returns

        rf = RequestFactory()
        request = rf.get('/simple_view', data={'ok': '1'})
        response = simple_view(request)
        self.assertEquals(response.status_code, 200)

        request = rf.get('/simple_view', data={'noperm': '1'})
        response = simple_view(request)
        self.assertEquals(response.status_code, 403)

        request = rf.get('/simple_view', data={'bad': '1'})
        response = simple_view(request)
        self.assertEquals(response.status_code, 400)

    @override_settings(DEBUG=False)
    @override_settings(TESTING=False)
    def test_api_returns_decorator(self):
        """
        Test that the @api_returns decorator does not result in a 400
        in production.

        This is a temporary measure to avoid breaking production as we apply
        this decorator to existing APIs.
        """
        original_log_level = logger.level
        logger.setLevel(1000)

        @api_returns({
            200: 'OK',
            403: 'Permission denied',
        })
        def simple_view(request):
            if 'ok' in request.GET:
                return JsonResponse()
            elif 'noperm' in request.GET:
                return JsonResponseForbidden()
            else:
                return JsonResponseAccepted()  # Not declared in @api_returns

        rf = RequestFactory()
        request = rf.get('/simple_view', data={'bad': '1'})
        response = simple_view(request)
        self.assertEquals(response.status_code, 202)
        logger.setLevel(original_log_level)

    def test_api_decorator_debug(self):
        """
        Test that the @api decorator (in debug mode)
        """
        @api({
            'accepts': {
                'im_required': forms.IntegerField(),
                'ok': forms.IntegerField(required=False),
            },
            'returns': {
                200: 'OK',
                403: 'Permission denied',
            },
        })
        def simple_view(request):
            if request.GET['ok']:
                return JsonResponse()
            else:
                return JsonResponseAccepted()  # Not declared in @api_returns

        rf = RequestFactory()
        request = rf.get('/simple_view', data={'im_required': '1', 'ok': '1'})
        response = simple_view(request)
        self.assertEquals(response.status_code, 200)

        # fail accepts
        request = rf.get('/simple_view', data={'ok': '1'})
        response = simple_view(request)
        self.assertEquals(response.status_code, 400)

        # fail returns
        request = rf.get('/simple_view', data={'im_required': '1'})
        response = simple_view(request)
        self.assertEquals(response.status_code, 400)
