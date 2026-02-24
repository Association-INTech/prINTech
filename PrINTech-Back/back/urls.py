from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers, permissions
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .apps.api.views import CreateUserView, UserMeView, ChangePasswordView, \
    RequestViewSet, CreateFileView, FileViewSet
from .views import home

admin.autodiscover()

router = routers.DefaultRouter()
router.register(r'requests', RequestViewSet, basename='request')
router.register(r'files', FileViewSet, basename='file')

urlpatterns = [
    path('', home, name='home'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    path("api/v1/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    path("api/v1/user/", CreateUserView.as_view(), name="create_user"),
    path("api/v1/user/me/", UserMeView.as_view(), name="user_info"),
    path(
        "api/v1/user/me/change-password/",
        ChangePasswordView.as_view(),
        name="change-password",
    ),

    path("api/v1/file/", CreateFileView.as_view(), name="create_file"),

    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('admin/', admin.site.urls),
    path("api/v1/", include(router.urls)),
]

# debug toolbar for dev
if settings.DEBUG and 'debug_toolbar'in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
