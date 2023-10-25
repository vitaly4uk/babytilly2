"""babytilly2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path
from django.views.generic import TemplateView

from commercial.views import (
    ArticleListView, AddToCartView, OrderListView, OrderDetailView,
    ArticleNewListView, ArticleSaleListView, EditCartView, DownloadArticleImages, ExportToXML,
)

urlpatterns = [
    path('cart/', EditCartView.as_view(), name='commercial_edit_cart'),
    path('showcart/', AddToCartView.as_view(), name='commercial_show_cart'),
    path('getimages/<str:id>/', DownloadArticleImages.as_view(),
         name='commercial_download_images_url'),
    path('addtocart/<str:id>/', AddToCartView.as_view(),
         name='commercial_addto_cart_one'),
    path('addtocart/<str:id>/<int:count>/', AddToCartView.as_view(),
         name='commercial_addto_cart'),
    path('dashboard/order/', OrderListView.as_view(),
         name='commercial_order_list'),
    path('dashboard/order/<int:pk>/', OrderDetailView.as_view(),
         name='commercial_order_detail'),
    path('category/<str:id>/', ArticleListView.as_view(),
         name='category_detail_url'),
    path('new/', ArticleNewListView.as_view(), name='new_list_url'),
    path('sale/', ArticleSaleListView.as_view(), name='sale_list_url'),
    path('<str:country>/xml/', ExportToXML.as_view()),
    path('', login_required(TemplateView.as_view(template_name='index.html'))),
] + staticfiles_urlpatterns()
