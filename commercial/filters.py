from django.contrib import admin
from django.utils.translation import gettext_lazy


class ArticlePublishedFilter(admin.SimpleListFilter):
    title = gettext_lazy('published')
    parameter_name = 'is_published'

    def lookups(self, request, model_admin):
        return (
            ('1', gettext_lazy('Yes')),
            ('0', gettext_lazy('No')),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            queryset = queryset.filter(articleproperties__published=True).distinct()
        elif self.value() == '0':
            queryset = queryset.filter(articleproperties__published=False).distinct()
        return queryset


class CategoryPublishedFilter(admin.SimpleListFilter):
    title = gettext_lazy('published')
    parameter_name = 'is_published'

    def lookups(self, request, model_admin):
        return (
            ('1', gettext_lazy('Yes')),
            ('0', gettext_lazy('No')),
        )

    def queryset(self, request, queryset):
        if self.value() == '1':
            queryset = queryset.filter(categoryproperties__published=True).distinct()
        elif self.value() == '0':
            queryset = queryset.filter(categoryproperties__published=False).distinct()
        return queryset
