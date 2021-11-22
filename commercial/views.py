from urllib.parse import urlencode

from django.contrib.auth import logout
from django.core.files.storage import get_storage_class
from django.db.models import F, Q
from django.conf import settings
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.core.cache import cache
from braces.views import CsrfExemptMixin, JSONRequestResponseMixin, AjaxResponseMixin
from commercial.models import StartPageImage, Category, Article, ArticleProperties, Order, OrderItem
from django.utils.decorators import method_decorator
import logging

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

class ArticleListView(ActiveRequiredMixin, ListView):
    template_name = 'commercial/articleprice_list.html'
    context_object_name = 'object_list'

    def get_paginate_by(self, queryset):
        return int(self.request.GET.get('per_page', settings.PAGINATOR[2]))

    def get_queryset(self):
        sort = self.request.GET.get('sort', None)
        user_departament_id = self.request.user.profile.departament_id
        queryset = ArticleProperties.objects.filter(published=True, departament_id=user_departament_id, article__category__id=self.kwargs['id']).order_by('name')

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
        context.update({
            'category': get_object_or_404(Category, id=self.kwargs['id']),
            'sort': self.request.GET.get('sort', None),
            'per_page': self.get_paginate_by(None),
            'paginator_list': settings.PAGINATOR,
            'link': urlencode(params),
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
            queryset = ArticleProperties.objects.filter(name__icontains=search_str, departament_id=user_departament_id)
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

@method_decorator(is_active('/'), 'dispatch')
class AddToCartView(TemplateView):
    template_name = 'commercial/cart.html'

    def get_context_data(self, **kwargs):
        context = super(AddToCartView, self).get_context_data(**kwargs)
        user_departament_id = self.request.user.profile.departament_id
        order = getattr(self.request, 'order', None)
        id = self.kwargs.get('id', None)
        count = self.kwargs.get('count', 1)
        logger.debug('add to cart: %s', order)
        if id:
            if not order:
                order = Order(user=self.request.user)
                order.save()
                self.request.session['order_id'] = order.pk
                self.request.order = order
            article = get_object_or_404(ArticleProperties, article_id=id, departament_id=user_departament_id)
            (orderitem, _) = OrderItem.objects.get_or_create(order=order, article_id=article.article.id)
            orderitem.count = int(count)
            orderitem.price = str(article.price)
            orderitem.save()
        context.update({
            'order': self.request.order
        })
        return context

@is_active('/')
def edit_cart(request):
    if request.method == "POST":
        if request.POST.get('submit') == 'Очистить':
            if hasattr(request, 'order'):
                order = request.order
                OrderItem.objects.filter(order=order).delete()
        if request.POST.get('submit') == 'Пересчитать':
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
                    count = int(get_digits(request.POST.get(item, 0)))
                    if count == 0:
                        elem.delete()
                    else:
                        elem.count = count
                        elem.save()
        elif request.POST.get('submit') == 'Отправить':
            if hasattr(request, 'order'):
                order = request.order
                order.comment = request.POST.get('comment')
                order.is_closed = True
                order.save()
                order.send()
            logout(request)
            return HttpResponseRedirect("/")

    return render(request, 'commercial/editcart.html', {'order': request.order})
