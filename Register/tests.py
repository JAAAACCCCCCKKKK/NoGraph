import json
import os
import re

import django
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, Client
from django.core import mail
from django.utils import timezone

from Register.models import CustomUser as User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NoGraph.settings')
django.setup()
test_code = None
token = None

class UserTestCase(TestCase):
    user = None
    def setUp(self):
        User.objects.create(username='testuser', email='12345@gmail.com', password='testpassword')
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
    def setUp(self):
        self.client = Client()
        self.email = "user@example.com"
        self.username = "original_user"
        self.new_username = "updated_user"

    def test_full_register_flow(self):
        response = self.client.post(
            '/auth/sendcode/',
            data=json.dumps({"email": self.email}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        print(mail.outbox)
        self.assertGreaterEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[-1]
        match = re.search(r"Your verification code is:\s*(\d{6})", sent_mail.body)
        self.assertIsNotNone(match)
        code = match.group(1)
        print(f"[Test] Captured code = {code}")

        response = self.client.post(
            '/auth/verify/',
            data=json.dumps({
                "username": self.username,
                "email": self.email,
                "code": code
            }),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        token = data.get("token")
        print(f"[Test] Token received = {token[:10]}...")

        response = self.client.post(
            '/auth/changename/',
            data=json.dumps({
                "email": self.email,
                "new_username": self.new_username
            }),
            content_type="application/json",
            **{"HTTP_AUTH": f"Bearer {token}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

        response = self.client.post(
            '/auth/logout/',
            data=json.dumps({"email": self.email}),
            content_type="application/json",
            **{"HTTP_AUTH": f"Bearer {token}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

        response = self.client.post(
            '/auth/changename/',
            data=json.dumps({
                "email": self.email,
                "new_username": "should_fail"
            }),
            content_type="application/json",
            **{"HTTP_AUTH": f"Bearer {token}"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("please log in", response.json()["message"])

