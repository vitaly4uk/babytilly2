from django.apps import AppConfig
from django.contrib import admin
from django.contrib.auth import get_user_model


class CommercialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'commercial'

    def ready(self):
        from .admin import (
            DepartamentAdmin, CategoryAdmin, UserAdmin, ImportPriceAdmin, ArticleAdmin, OrderAdmin, StartPageImageAdmin
        )

        Departament = self.get_model('Departament')
        Category = self.get_model('Category')
        Article = self.get_model('Article')
        Order = self.get_model('Order')
        StartPageImage = self.get_model('StartPageImage')
        ImportPrice = self.get_model('ImportPrice')
        ImportNew = self.get_model('ImportNew')
        ImportSpecial = self.get_model('ImportSpecial')
        User = get_user_model()

        admin.site.unregister(User)

        admin.site.register(Departament, DepartamentAdmin)
        admin.site.register(Category, CategoryAdmin)
        admin.site.register(Article, ArticleAdmin)
        admin.site.register(User, UserAdmin)
        admin.site.register(Order, OrderAdmin)
        admin.site.register(StartPageImage, StartPageImageAdmin)
        admin.site.register(ImportPrice, ImportPriceAdmin)
        admin.site.register(ImportNew, ImportPriceAdmin)
        admin.site.register(ImportSpecial, ImportPriceAdmin)
