from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AdminActionLog, Operation, User


@admin.register(User)
class AppUserAdmin(UserAdmin):
    readonly_fields = UserAdmin.readonly_fields + ('credit',)
    fieldsets = UserAdmin.fieldsets + (
        ('PrINTech', {'fields': ('credit', 'role', 'profile_picture')}),
    )
    list_display = ('email', 'username', 'role', 'credit', 'is_staff', 'is_active')
    ordering = ('email',)


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'beneficiary', 'agent', 'created_at', 'operation_type', 'comment', 'amount', 'request')
    list_display = ('id', 'beneficiary', 'agent', 'amount', 'operation_type', 'request', 'created_at')
    list_filter = ('operation_type', 'created_at')
    search_fields = ('beneficiary__email', 'agent__email', 'request__id', 'comment')

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    readonly_fields = ('id', 'actor', 'action', 'target_type', 'target_id', 'before', 'after', 'comment', 'created_at')
    list_display = ('created_at', 'actor', 'action', 'target_type', 'target_id')
    list_filter = ('action', 'target_type', 'created_at')
    search_fields = ('actor__email', 'action', 'target_type', 'target_id')

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
