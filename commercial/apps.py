from django.apps import AppConfig
from django.contrib import admin
from django.contrib.auth import get_user_model


class CommercialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'commercial'

    def ready(self):
        from .admin import (
            DepartamentAdmin, CategoryAdmin, UserAdmin, ImportPriceAdmin
        )

        Departament = self.get_model('Departament')
        Category = self.get_model('Category')
        ImportPrice = self.get_model('ImportPrice')
        User = get_user_model()

        admin.site.unregister(User)

        admin.site.register(Departament, DepartamentAdmin)
        admin.site.register(Category, CategoryAdmin)
        admin.site.register(User, UserAdmin)
        admin.site.register(ImportPrice, ImportPriceAdmin)
