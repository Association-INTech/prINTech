from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .apps.api.views import (
    CreateUserView,
    UserMeView,
    ChangePasswordView,
    OperationView,
    AdminOperationView,
    RequestView,
    AdminRequestView,
    AdminUserView,
    FilamentView,
    AdminFilamentView,
    PrinterView,
    AdminPrinterView,
)
from .views import home

router = DefaultRouter()
router.register(r'requests', RequestView, basename='request')
router.register(r'admin/requests', AdminRequestView, basename='admin-request')
router.register(r'admin/users', AdminUserView, basename='admin-user')
router.register(r'operations', OperationView, basename='operation')
router.register(r'admin/operations', AdminOperationView, basename='admin-operation')
router.register(r'filaments', FilamentView, basename='filament')
router.register(r'admin/filaments', AdminFilamentView, basename='filament-admin')
router.register(r'printers', PrinterView, basename='printer')
router.register(r'admin/printers', AdminPrinterView, basename='admin-printer')

urlpatterns = [
    # Examples:
    path('', home, name='home'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # path('app/', include('apps.app.urls')),
    path("api/v1/", include(router.urls)),
    path("api/v1/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/user/", CreateUserView.as_view(), name="create_user"),
    path("api/v1/user/me/", UserMeView.as_view(), name="user_info"),
    path(
        "api/v1/user/me/change-password/",
        ChangePasswordView.as_view(),
        name="change-password",
    ),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('admin/', admin.site.urls),
]

if settings.DEBUG and 'debug_toolbar' in settings.INSTALLED_APPS:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)