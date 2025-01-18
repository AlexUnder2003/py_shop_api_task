import os
from datetime import timedelta

import jwt
from constance import config
from dotenv import load_dotenv
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.serializers import UserUpdateSerializer, CustomUserCreateSerializer
from users.models import RefreshTokenModel

User = get_user_model()

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRATION = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRATION = timedelta(days=7)


def create_token(data, expiration):
    """
    Create a JWT token.

    Parameters:
        data (dict): The data to include in the token's payload.
        expiration (timedelta): The expiration time for the token.

    Returns:
        str: The generated JWT token.
    """
    payload = {
        **data,
        "exp": timezone.now() + expiration,
        "iat": timezone.now(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def decode_token(token):
    """
    Decode a JWT token.

    Parameters:
        token (str): The JWT token to decode.

    Returns:
        dict or None: The decoded token data if valid, otherwise None.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Register a new user",
        request_body=CustomUserCreateSerializer,
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                "User created", CustomUserCreateSerializer
            ),
            status.HTTP_400_BAD_REQUEST: "Invalid input",
        },
        manual_parameters=[
            openapi.Parameter(
                "param_name",
                openapi.IN_QUERY,
                description="Description of the parameter",
                type=openapi.TYPE_STRING,
                default="default_value",
            )
        ],
    )
    def post(self, request):
        """
        Register a new user.

        Parameters:
            email (str): The user's email address.
            password (str): The user's password.

        Returns:
            Response: The response with user data (id and email).
        """
        serializer = CustomUserCreateSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            user_response_serializer = CustomUserCreateSerializer(user)

            return Response(
                user_response_serializer.data,
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(APIView):
    """
    View to obtain JWT tokens (access and refresh).

    Accepts: email and password, generates and returns tokens.
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Get user tokens",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING, description="User Email"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING, description="User Password"
                ),
            },
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                "Токены получены",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Access token",
                        ),
                        "refresh": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Refresh token",
                        ),
                    },
                ),
            ),
            status.HTTP_401_UNAUTHORIZED: "Invalid credentials",
            status.HTTP_404_NOT_FOUND: "User does not exist",
        },
    )
    def post(self, request):
        """
        Create access and refresh tokens for the user.

        Parameters:
            email (str): The user's email address.
            password (str): The user's password.

        Returns:
            Response: A response with access and refresh tokens or an error.
        """
        email = request.data.get("email")
        password = request.data.get("password")
        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                return Response(
                    {"detail": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        except User.DoesNotExist:
            return Response(
                {"detail": "User does not exist"},
                status=status.HTTP_404_NOT_FOUND,
            )

        access_token_lifetime = timedelta(seconds=config.ACCESS_TOKEN_LIFETIME)
        refresh_token_lifetime = timedelta(days=config.REFRESH_TOKEN_LIFETIME)

        access_token = create_token(
            {"user_id": user.id, "email": user.email}, access_token_lifetime
        )
        refresh_token = create_token(
            {"user_id": user.id, "email": user.email}, refresh_token_lifetime
        )

        self.save_refresh_token(user, refresh_token)

        return Response(
            {"access": access_token, "refresh": refresh_token},
            status=status.HTTP_200_OK,
        )

    def save_refresh_token(self, user, refresh_token):
        """
        Save the refresh token to the database.

        Parameters:
            user (User): The user to whom the token belongs.
            refresh_token (str): The refresh token to be saved.
        """
        expires_at = timezone.now() + timedelta(
            days=config.REFRESH_TOKEN_LIFETIME
        )
        RefreshTokenModel.objects.update_or_create(
            user=user,
            defaults={"token": refresh_token, "expires_at": expires_at},
        )


class MeView(APIView):
    """
    View to get and update the current user's information.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get authenticated user information",
        responses={
            status.HTTP_200_OK: openapi.Response(
                "User info",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(
                            type=openapi.TYPE_INTEGER,
                            description="User ID",
                        ),
                        "username": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Username",
                        ),
                        "email": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="User Email",
                        ),
                    },
                ),
            ),
        },
    )
    def get(self, request):
        """
        Get information about the current user.

        Returns:
            Response: A response with the user's data.
        """

        user = request.user
        return Response(
            {"id": user.id, "username": user.username, "email": user.email}
        )

    @swagger_auto_schema(
        operation_description="Upadte user data",
        request_body=UserUpdateSerializer,
        responses={
            status.HTTP_200_OK: openapi.Response(
                "User updated", UserUpdateSerializer
            ),
            status.HTTP_400_BAD_REQUEST: "Invalid data",
        },
    )
    def put(self, request):
        """
        Update the current user's information.

        Parameters:
            username (str): New username (optional).
            email (str): New email address (optional).

        Returns:
            Response: A response with the updated user data.
        """
        user = request.user
        serializer = UserUpdateSerializer(
            user, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"id": user.id, "username": user.username, "email": user.email}
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TokenRefreshView(APIView):
    """
    View to refresh the access token using a refresh token.
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Update access by using refresh token.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "refresh": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Refresh token"
                )
            },
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                "New access token",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="New access token",
                        )
                    },
                ),
            ),
            status.HTTP_400_BAD_REQUEST: "Refresh token required",
            status.HTTP_401_UNAUTHORIZED: "Invalid or expired refresh token",
        },
    )
    def post(self, request):
        """
        Refresh the access token using the refresh token.

        Parameters:
            refresh (str): The refresh token to get a new access token.

        Returns:
            Response: A response with the new access token or an error.
        """
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        decoded_token = decode_token(refresh_token)
        if not decoded_token:
            return Response(
                {"detail": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            user = User.objects.get(id=decoded_token["user_id"])
            access_token = create_token(
                {"user_id": user.id, "email": user.email},
                ACCESS_TOKEN_EXPIRATION,
            )

            return Response(
                {"access": access_token}, status=status.HTTP_200_OK
            )

        except RefreshTokenModel.DoesNotExist:
            return Response(
                {"detail": "Refresh token not found in database"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class LogoutView(APIView):
    """
    View to log the user out by deleting their refresh token.
    """

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="User logout and refresh token invalidation.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "refresh": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Refresh token",
                )
            },
        ),
        responses={
            status.HTTP_200_OK: openapi.Response("User logged out."),
            status.HTTP_400_BAD_REQUEST: "Invalid refresh token",
        },
    )
    def post(self, request):
        """
        Log the user out by deleting their refresh token.

        Parameters:
            refresh (str): The refresh token to delete.

        Returns:
            Response: A response indicating successful logout or an error.
        """
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token_obj = RefreshTokenModel.objects.get(token=refresh_token)
            token_obj.delete()
            return Response(
                {"success": "User logged out."}, status=status.HTTP_200_OK
            )
        except RefreshTokenModel.DoesNotExist:
            return Response(
                {"detail": "Invalid refresh token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
