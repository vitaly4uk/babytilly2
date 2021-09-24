from django.core.files.storage import get_storage_class
from django.shortcuts import render
from django.views.generic import TemplateView
from django.core.cache import cache

from commercial.models import StartPageImage


class HomePage(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(HomePage, self).get_context_data()
        department = self.request.user.profile.department_id
        file_list = cache.get('{}_{}'.format('home-page-file-list', department), )
        if not file_list:
            file_list = StartPageImage.objects.filter(departament_id=department)
            cache.set('{}_{}'.format('home-page-file-list', department), file_list)
        context.update({
            'file_list': file_list,
        })
        return context
