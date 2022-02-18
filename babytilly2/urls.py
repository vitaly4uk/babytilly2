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
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include

from commercial.views import HomePage, ArticleSearchListView, PageDetailView

# from django_ses.views import SESEventWebhookView
# from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    # path('ses/event-webhook/', csrf_exempt(SESEventWebhookView.as_view()), name='handle-event-webhook'),
    path('admin/', admin.site.urls),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('search/', ArticleSearchListView.as_view(), name='search'),
    path('commerce/', include('commercial.urls')),
    path('<slug:slug>/', PageDetailView.as_view(), name='page_detail_url'),
    path('', HomePage.as_view(), name='home_page'),
    path('__debug__/', include('debug_toolbar.urls')),
] + staticfiles_urlpatterns()
