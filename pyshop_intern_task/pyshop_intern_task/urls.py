from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from django.contrib import admin
from django.urls import path
from rest_framework.permissions import AllowAny

from users.views import (
    LogoutView,
    MeView,
    CustomTokenObtainPairView,
    TokenRefreshView,
    RegisterView,
)

schema_view = get_schema_view(
    openapi.Info(
        title="JWT_Auth_API",
        default_version="v1",
        description="User management and authentication api",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@myapi.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(AllowAny,),
)


urlpatterns = [
    path("api/register/", RegisterView.as_view(), name="register"),
    path(
        "api/login/",
        CustomTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path("api/logout/", LogoutView.as_view(), name="logout"),
    path("api/me/", MeView.as_view(), name="me"),
    path("admin/", admin.site.urls),
    path(
        "docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="swagger-ui",
    ),
]
