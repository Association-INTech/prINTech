from django.contrib import admin
from .models import Operation,User
# Register your models here.
admin.site.register(User)
admin.site.register(Operation)