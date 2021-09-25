from django.core.files.storage import get_storage_class
from django.shortcuts import render
from django.views.generic import TemplateView
from django.core.cache import cache

from commercial.models import StartPageImage


class HomePage(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(HomePage, self).get_context_data()
        queryset = StartPageImage.objects.only('image')
        if self.request.user.is_authenticated:
            queryset = queryset.filter(departament_id=self.request.user.profile.department_id)
        else:
            queryset = queryset.filter(departament__isnull=True)
        context.update({
            'file_list': [sp.image.url for sp in queryset],
        })
        return context
