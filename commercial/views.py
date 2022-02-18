import logging
import sys
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils.translation import gettext_lazy
from django.views.generic import TemplateView, ListView, DetailView

from commercial.models import StartPageImage, Category, ArticleProperties, Order, OrderItem, Page
from commonutils.views import ActiveRequiredMixin, is_active

logger = logging.getLogger(__name__)


def get_digits(string):
    pos = 0
    while pos < len(string):
        if not string[pos].isdigit():
            return string[:pos]
        pos += 1
    return string if string else '0'


class HomePage(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super(HomePage, self).get_context_data()
        queryset = StartPageImage.objects.only('image')
        context.update({
            'file_list': [sp.image.url for sp in queryset],
        })
        return context


class PageDetailView(ActiveRequiredMixin, DetailView):
    template_name = 'flatpages/default.html'
    context_object_name = 'page'

    def get_queryset(self):
        user_departament_id = self.request.user.profile.departament_id
        queryset = Page.objects.filter(departament_id=user_departament_id)
        return queryset


class ArticleListView(ActiveRequiredMixin, ListView):
    template_name = 'commercial/articleprice_list.html'
    context_object_name = 'object_list'

    def get_paginate_by(self, queryset):
        return int(self.request.GET.get('per_page', settings.PAGINATOR[2]))

    def get_queryset(self):
        sort = self.request.GET.get('sort', None)
        user_departament_id = self.request.user.profile.departament_id
        queryset = ArticleProperties.objects.filter(
            published=True, departament_id=user_departament_id,
            article__category__id=self.kwargs['id']
        ).select_related('article')

        if sort == 'price':
            queryset = queryset.order_by('price')
        if sort == '-price':
            queryset = queryset.order_by('-price')

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ArticleListView, self).get_context_data(**kwargs)
        params = self.request.GET.copy()
        if 'page' in params:
            del params['page']
        category = get_object_or_404(Category, id=self.kwargs['id'])
        property = category.categoryproperties_set.filter(
            departament_id=self.request.user.profile.departament_id
        ).first()
        page_title = property.name if property else ''
        context.update({
            'category': category,
            'sort': self.request.GET.get('sort', None),
            'per_page': self.get_paginate_by(None),
            'paginator_list': settings.PAGINATOR,
            'link': urlencode(params),
            'page_title': page_title
        })
        return context


class ArticleSearchListView(ActiveRequiredMixin, ListView):
    template_name = 'commercial/articleprice_list.html'
    context_object_name = 'object_list'

    def get_paginate_by(self, queryset):
        return int(self.request.GET.get('per_page', settings.PAGINATOR[2]))

    def get_queryset(self):
        sort = self.request.GET.get('sort', None)
        search_str = self.request.GET.get('query', '').strip()
        user_departament_id = self.request.user.profile.departament_id
        if search_str:
            queryset = ArticleProperties.objects.filter(published=True,
                name__icontains=search_str, departament_id=user_departament_id)
        else:
            queryset = ArticleProperties.objects.none()

        if sort == 'price':
            queryset = queryset.order_by('price')
        if sort == '-price':
            queryset = queryset.order_by('-price')

        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super(ArticleSearchListView, self).get_context_data(*args, **kwargs)
        params = self.request.GET.copy()
        if 'page' in params:
            del params['page']
        context.update({
            'page_title': self.request.GET.get('query', '').strip(),
            'sort': self.request.GET.get('sort', None),
            'per_page': self.get_paginate_by(None),
            'paginator_list': settings.PAGINATOR,
            'link': urlencode(params),
        })
        return context


class ArticleNewListView(ActiveRequiredMixin, ListView):
    template_name = 'commercial/articleprice_list.html'
    context_object_name = 'object_list'

    def get_paginate_by(self, queryset):
        return int(self.request.GET.get('per_page', settings.PAGINATOR[2]))

    def get_queryset(self):
        sort = self.request.GET.get('sort', None)
        user_departament_id = self.request.user.profile.departament_id
        queryset = ArticleProperties.objects.filter(
            published=True, departament_id=user_departament_id, is_new=True
        ).select_related('article')

        if sort == 'price':
            queryset = queryset.order_by('price')
        if sort == '-price':
            queryset = queryset.order_by('-price')

        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super(ArticleNewListView, self).get_context_data(*args, **kwargs)
        params = self.request.GET.copy()
        if 'page' in params:
            del params['page']
        context.update({
            'page_title': gettext_lazy('New'),
            'sort': self.request.GET.get('sort', None),
            'per_page': self.get_paginate_by(None),
            'paginator_list': settings.PAGINATOR,
            'link': urlencode(params),
        })
        return context


class ArticleSaleListView(ActiveRequiredMixin, ListView):
    template_name = 'commercial/articleprice_list.html'
    context_object_name = 'object_list'

    def get_paginate_by(self, queryset):
        return int(self.request.GET.get('per_page', settings.PAGINATOR[2]))

    def get_queryset(self):
        sort = self.request.GET.get('sort', None)
        user_departament_id = self.request.user.profile.departament_id
        queryset = ArticleProperties.objects.filter(published=True, departament_id=user_departament_id,
                                                    is_special=True)

        if sort == 'price':
            queryset = queryset.order_by('price')
        if sort == '-price':
            queryset = queryset.order_by('-price')

        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super(ArticleSaleListView, self).get_context_data(*args, **kwargs)
        params = self.request.GET.copy()
        if 'page' in params:
            del params['page']
        context.update({
            'page_title': gettext_lazy('Sale'),
            'sort': self.request.GET.get('sort', None),
            'per_page': self.get_paginate_by(None),
            'paginator_list': settings.PAGINATOR,
            'link': urlencode(params),
        })
        return context


class OrderListView(ActiveRequiredMixin, ListView):
    template_name = 'commercial/order_list.html'
    context_object_name = 'order_list'
    model = Order

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user, is_closed=True)


class OrderDetailView(ActiveRequiredMixin, DetailView):
    template_name = 'commercial/editcart.html'
    context_object_name = 'order'
    model = Order

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user, is_closed=True)


class AddToCartView(ActiveRequiredMixin, TemplateView):
    template_name = 'commercial/cart.html'

    def get_context_data(self, **kwargs):
        context = super(AddToCartView, self).get_context_data(**kwargs)
        user_departament_id = self.request.user.profile.departament_id
        order = getattr(self.request, 'order', None)
        article_id = self.kwargs.get('id', None)
        try:
            count = int(self.kwargs.get('count', '1'))
        except ValueError:
            count = 1
        count = max(min(count, sys.maxsize), 1)
        logger.debug('add to cart: %s', order)
        if article_id:
            if not order:
                order = Order(user=self.request.user)
                order.save()
                self.request.session['order_id'] = order.pk
                self.request.order = order
            article_property = get_object_or_404(ArticleProperties, article_id=article_id,
                                                 departament_id=user_departament_id)
            order_item, _ = OrderItem.objects.get_or_create(order=order, article_id=article_id)
            order_item.count = count
            order_item.name = article_property.name
            order_item.volume = article_property.volume
            order_item.weight = article_property.weight
            order_item.barcode = article_property.barcode
            order_item.company = article_property.company
            order_item.price = article_property.get_price_for_user(self.request.user)
            order_item.full_price = article_property.price
            order_item.main_image_url = article_property.main_image.url
            order_item.save()
        context.update({
            'order': self.request.order
        })
        return context


@is_active('/')
def edit_cart(request):
    if request.method == "POST":
        if request.POST.get('submit') == 'Clear':
            if hasattr(request, 'order'):
                order = request.order
                OrderItem.objects.filter(order=order).delete()
        if request.POST.get('submit') == 'Recalculate':
            for item in request.POST:
                if item.startswith('del_'):
                    i = item.split('_')
                    try:
                        elem = OrderItem.objects.get(pk=i[1])
                        elem.delete()
                    except OrderItem.DoesNotExist:
                        continue
                else:
                    try:
                        obj_id = int(item)
                    except ValueError:
                        continue
                    try:
                        elem = OrderItem.objects.get(pk=obj_id)
                    except OrderItem.DoesNotExist:
                        continue
                    try:
                        count = int(get_digits(request.POST.get(item, 0)))
                    except ValueError:
                        count = 0
                    if count == 0:
                        elem.delete()
                    else:
                        elem.count = count
                        elem.save()
        elif request.POST.get('submit') == 'Send':
            if hasattr(request, 'order'):
                order = request.order
                order.comment = request.POST.get('comment')
                order.is_closed = True
                order.save()
                order.send()
            logout(request)
            return HttpResponseRedirect("/")

    return render(request, 'commercial/editcart.html', {'order': request.order})
