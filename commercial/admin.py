from django.contrib import admin
from mptt.admin import MPTTModelAdmin


class DepartamentAdmin(admin.ModelAdmin):
    list_display = ['country', 'email']


class CategoryAdmin(MPTTModelAdmin):
    list_display = ['id']
