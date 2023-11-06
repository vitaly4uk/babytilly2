from django.contrib import admin
from django.utils.translation import gettext_lazy


class CarrelloAdminSite(admin.AdminSite):
    site_title = gettext_lazy("B2B Carrello")
    site_header = gettext_lazy("B2B Carrello")
