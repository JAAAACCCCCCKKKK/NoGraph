from django.db import IntegrityError
from django.test import TestCase
from pydantic import ValidationError
from NoGraph import settings
import os
import django
from django.conf import settings
from Register.models import User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NoGraph.settings')
django.setup()

class UserTestCase(TestCase):
    user = None
    def setUp(self):
        User.objects.create(username='testuser', email='12345@gmail.com')
        self.user = User.objects.get(username='testuser')

    def test_user_creation(self):
        self.assertEqual(self.user.email, '12345@gmail.com')
        self.assertTrue(self.user.active)
        self.assertFalse(self.user.is_admin)

    def test_validate(self):
        try:
            self.user.full_clean()
        except ValidationError:
            self.fail("ValidationError raised")

    def test_duplicated_username_invalid(self):
        with self.assertRaises(IntegrityError):
            User.objects.create(username='testuser', email='12345@1')

    def test_duplicated_email_invalid(self):
        with self.assertRaises(IntegrityError):
            User.objects.create(username='testuser2', email='12345@gmail.com')


class SendCodeTestCase(TestCase):
    def test_send_code(self):
        from Register.views import SendCode
        from django.http import JsonResponse
        from django.test import Client
        client = Client()
        response = client.post('', {'email': '12345@gmail.com'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})
