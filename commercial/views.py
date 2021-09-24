from django.core.files.storage import get_storage_class
from django.shortcuts import render
from django.views.generic import TemplateView
from django.core.cache import cache


class HomePage(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(HomePage, self).get_context_data()
        file_list = cache.get('home-page-file-list')
        if not file_list:
            file_list = []
            storage = get_storage_class()()
            try:
                dirs, files = storage.listdir('upload/startpage')
            except Exception:
                files = []
            for filename in files:
                if filename == '.':
                    continue
                file_list.append(storage.url('{}/{}'.format('upload/startpage', filename)))
            cache.set('home-page-file-list', file_list)
        context.update({
            'file_list': file_list,
        })
        return context
