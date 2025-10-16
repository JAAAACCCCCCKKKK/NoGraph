import os
import re

import django
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, Client
from django.core import mail

from Register.models import CustomUser as User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NoGraph.settings')
django.setup()

class UserTestCase(TestCase):
    user = None
    def setUp(self):
        User.objects.create(username='testuser', email='12345@gmail.com')
        self.user = User.objects.get(username='testuser')

    def test_user_creation(self):
        self.assertEqual(self.user.email, '12345@gmail.com')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)

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

    def test_misformatted_email_invalid(self):
        with self.assertRaises(ValidationError):
            user = User(username='testuser3', email='not-an-email')
            user.full_clean()


class RegisterTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.test_code = None
        cls.test_token =  None

    def test_health(self):
        client = Client()
        response = client.post('')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_sendcode_no_email(self):
        client = Client()
        response = client.post('/auth/sendcode/', content_type='application/json', data={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'status': 'error', 'message': 'Email is missing or invalid'} )

    def test_sendcode_invalid_email(self):
        client = Client()
        response = client.post('/auth/sendcode/', content_type='application/json', data={
            'email': 'not-an-email'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'status': 'error', 'message': 'Email is missing or invalid'} )


    def test_sendcode(self):
        client = Client()
        response = client.post('/auth/sendcode/', content_type='application/json', data={
            'email': '12345@gmail.com'
        })
        sent_email = mail.outbox[0]
        match = re.search(r'Your verification code is:\s*(\d{6})', sent_email.body)
        self.assertIsNotNone(match, "Verification code not found in email body")
        self.test_code = match.group(1)
        self.assertEqual(sent_email.subject, 'Your Verification Code')
        self.assertIn('Your verification code is:', sent_email.body)
        self.assertIn('12345@gmail.com', sent_email.to)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'success', 'message': 'Verification code sent successfully.'} )


    def test_verify(self):
        client = Client()
        response = client.post('/auth/verify/', content_type='application/json', data={
            'username': 'testuser',
            'email': '12345@gmail.com',
            'code': self.test_code
        })
        print(response.json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('status'), 'success')
        self.assertIn('token', response.json())
        token = response.json().get('token')

