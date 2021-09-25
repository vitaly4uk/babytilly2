from django.core.files.storage import get_storage_class
from django.shortcuts import render
from django.views.generic import TemplateView
from django.core.cache import cache

from commercial.models import StartPageImage


class HomePage(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(HomePage, self).get_context_data()
        if self.request.user.is_authenticated:
            department = self.request.user.profile.department_id
            file_list = cache.get(f'home-page-file-list-{department}')
            if not file_list:
                file_list = []
                storage = get_storage_class()()
                for image in StartPageImage.objects.filter(departament_id=department):
                    file_list.append(storage.url(image.image.url))
                cache.set(f'home-page-file-list-{department}', file_list)
        else:
            file_list = cache.get(f'home-page-file-list-free')
            if not file_list:
                file_list = []
                storage = get_storage_class()()
                for image in StartPageImage.objects.filter(departament__isnull=True):
                    file_list.append(storage.url(image.image.url))
                cache.set(f'home-page-file-list-free', file_list)
        context.update({
            'file_list': file_list,
        })
        return context
