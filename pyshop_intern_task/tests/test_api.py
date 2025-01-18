import jwt
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from users.models import RefreshTokenModel
from django.contrib.auth import get_user_model

from datetime import timedelta
from django.conf import settings

from constance import config


User = get_user_model()


class AuthenticationAPITest(TestCase):
    def setUp(self):
        self.register_url = reverse("register")
        self.login_url = reverse("token_obtain_pair")
        self.logout_url = reverse("logout")
        self.refresh_url = reverse("token_refresh")
        self.user_email = "testuser@example.com"
        self.user_password = "strongpassword123"

        self.user = User.objects.create_user(
            email=self.user_email,
            password=self.user_password,
        )

    def test_registration(self):
        """Test user creation api endpoint."""
        User.objects.all().delete()
        response = self.client.post(
            self.register_url,
            {
                "email": "newuser@example.com",
                "password": "newpassword123",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("email", response.data)
        self.assertEqual(response.data["email"], "newuser@example.com")
        self.assertEqual(User.objects.all().count(), 1)

    def test_login(self):
        """Test login/token creation api endpoint."""
        initial_count = RefreshTokenModel.objects.all().count()
        response = self.client.post(
            self.login_url,
            {
                "email": self.user_email,
                "password": self.user_password,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(
            RefreshTokenModel.objects.all().count(), initial_count + 1
        )

    def test_token_deletion_on_logout(self):
        """Test refresh token invalidation."""
        login_response = self.client.post(
            self.login_url,
            {
                "email": self.user_email,
                "password": self.user_password,
            },
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        refresh_token = login_response.data["refresh"]

        self.assertTrue(
            RefreshTokenModel.objects.filter(token=refresh_token).exists()
        )

        logout_response = self.client.post(
            self.logout_url,
            {
                "refresh": refresh_token,
            },
            content_type="application/json",
        )
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        self.assertFalse(
            RefreshTokenModel.objects.filter(token=refresh_token).exists()
        )

    def tearDown(self):
        User.objects.all().delete()
        RefreshTokenModel.objects.all().delete()


class TokenLifetimeTest(TestCase):
    def setUp(self):
        self.login_url = reverse("token_obtain_pair")
        self.user_email = "testuser@example.com"
        self.user_password = "strongpassword123"

        self.user = User.objects.create_user(
            email=self.user_email,
            password=self.user_password,
        )

        self.default_access_token_lifetime = config.ACCESS_TOKEN_LIFETIME
        self.default_refresh_token_lifetime = config.REFRESH_TOKEN_LIFETIME

    def test_access_token_lifetime(self):
        """Access token lifetime is correctly set from the config"""
        response = self.client.post(
            self.login_url,
            {
                "email": self.user_email,
                "password": self.user_password,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.data["access"]

        decoded_token = jwt.decode(
            access_token, settings.SECRET_KEY, algorithms=["HS256"]
        )

        token_create_time = timedelta(seconds=decoded_token["iat"])
        expected_expiration = token_create_time + timedelta(
            seconds=self.default_access_token_lifetime
        )

        token_expiration = timedelta(seconds=decoded_token["exp"])

        self.assertTrue(
            abs((token_expiration - expected_expiration).total_seconds()) < 5
        )

    def test_refresh_token_lifetime(self):
        """Refresh token lifetime is correctly set from the config"""
        response = self.client.post(
            self.login_url,
            {
                "email": self.user_email,
                "password": self.user_password,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refresh_token = response.data["refresh"]

        decoded_token = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=["HS256"]
        )

        token_create_time = timedelta(seconds=decoded_token["iat"])
        expected_expiration = token_create_time + timedelta(
            days=self.default_refresh_token_lifetime
        )

        token_expiration = timedelta(seconds=decoded_token["exp"])

        self.assertTrue(
            abs((token_expiration - expected_expiration).total_seconds()) < 5
        )

    def tearDown(self):
        User.objects.all().delete()
        RefreshTokenModel.objects.all().delete()
