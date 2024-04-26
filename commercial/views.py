import io
import logging
import sys
import zipfile
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.mixins import UserPassesTestMixin
from django.forms import modelformset_factory
from django.http import HttpResponseRedirect, FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy
from django.views import View
from django.views.generic import (
    TemplateView,
    ListView,
    DetailView,
    CreateView,
    FormView,
)
from django.views.generic.base import TemplateResponseMixin

from commercial.forms import EditOrderForm, OrderItemForm, MessageForm, ComplaintForm
from commercial.functions import export_department_to_xml
from commercial.models import (
    StartPageImage,
    Category,
    ArticleProperties,
    Order,
    OrderItem,
    Page,
    UserDebs,
    ArticleImage,
    Departament,
    Complaint,
    Message,
    MessageAttachment,
)
from commercial.tasks import send_order_email, send_complaint_mail

logger = logging.getLogger(__name__)


class ActiveRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_active


def get_digits(string):
    pos = 0
    while pos < len(string):
        if not string[pos].isdigit():
            return string[:pos]
        pos += 1
    return string if string else "0"


class HomePage(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super(HomePage, self).get_context_data()
        queryset = StartPageImage.objects.only("image")
        context.update(
            {
                "file_list": [sp.image.url for sp in queryset],
            }
        )
        return context


class PageDetailView(ActiveRequiredMixin, DetailView):
    template_name = "flatpages/default.html"
    context_object_name = "page"

    def get_queryset(self):
        user_departament_id = self.request.user.profile.departament_id
        queryset = Page.objects.filter(departament_id=user_departament_id)
        return queryset


class ArticleListView(ActiveRequiredMixin, ListView):
    template_name = "commercial/articleprice_list.html"
    context_object_name = "object_list"

    def get_paginate_by(self, queryset):
        return int(self.request.GET.get("per_page", settings.PAGINATOR[2]))

    def get_queryset(self):
        sort = self.request.GET.get("sort", None)
        user_departament_id = self.request.user.profile.departament_id
        queryset = ArticleProperties.objects.filter(
            published=True,
            departament_id=user_departament_id,
            article__category__id=self.kwargs["id"],
        ).select_related("article")

        if sort == "price":
            queryset = queryset.order_by("price")
        if sort == "-price":
            queryset = queryset.order_by("-price")

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ArticleListView, self).get_context_data(**kwargs)
        params = self.request.GET.copy()
        if "page" in params:
            del params["page"]
        category = get_object_or_404(Category, id=self.kwargs["id"])
        property = category.categoryproperties_set.filter(
            departament_id=self.request.user.profile.departament_id
        ).first()
        page_title = property.name if property else ""
        context.update(
            {
                "category": category,
                "sort": self.request.GET.get("sort", None),
                "per_page": self.get_paginate_by(None),
                "paginator_list": settings.PAGINATOR,
                "link": urlencode(params),
                "page_title": page_title,
            }
        )
        return context


class ArticleSearchListView(ActiveRequiredMixin, ListView):
    template_name = "commercial/articleprice_list.html"
    context_object_name = "object_list"

    def get_paginate_by(self, queryset):
        return int(self.request.GET.get("per_page", settings.PAGINATOR[2]))

    def get_queryset(self):
        sort = self.request.GET.get("sort", None)
        search_str = self.request.GET.get("query", "").strip()
        user_departament_id = self.request.user.profile.departament_id
        if search_str:
            queryset = ArticleProperties.objects.filter(
                published=True,
                name__icontains=search_str,
                departament_id=user_departament_id,
            )
        else:
            queryset = ArticleProperties.objects.none()

        if sort == "price":
            queryset = queryset.order_by("price")
        if sort == "-price":
            queryset = queryset.order_by("-price")

        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super(ArticleSearchListView, self).get_context_data(*args, **kwargs)
        params = self.request.GET.copy()
        if "page" in params:
            del params["page"]
        context.update(
            {
                "page_title": self.request.GET.get("query", "").strip(),
                "sort": self.request.GET.get("sort", None),
                "per_page": self.get_paginate_by(None),
                "paginator_list": settings.PAGINATOR,
                "link": urlencode(params),
            }
        )
        return context


class ArticleNewListView(ActiveRequiredMixin, ListView):
    template_name = "commercial/articleprice_list.html"
    context_object_name = "object_list"

    def get_paginate_by(self, queryset):
        return int(self.request.GET.get("per_page", settings.PAGINATOR[2]))

    def get_queryset(self):
        sort = self.request.GET.get("sort", None)
        user_departament_id = self.request.user.profile.departament_id
        queryset = ArticleProperties.objects.filter(
            published=True, departament_id=user_departament_id, is_new=True
        ).select_related("article")

        if sort == "price":
            queryset = queryset.order_by("price")
        if sort == "-price":
            queryset = queryset.order_by("-price")

        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super(ArticleNewListView, self).get_context_data(*args, **kwargs)
        params = self.request.GET.copy()
        if "page" in params:
            del params["page"]
        context.update(
            {
                "page_title": gettext_lazy("New"),
                "sort": self.request.GET.get("sort", None),
                "per_page": self.get_paginate_by(None),
                "paginator_list": settings.PAGINATOR,
                "link": urlencode(params),
            }
        )
        return context


class ArticleSaleListView(ActiveRequiredMixin, ListView):
    template_name = "commercial/articleprice_list.html"
    context_object_name = "object_list"

    def get_paginate_by(self, queryset):
        return int(self.request.GET.get("per_page", settings.PAGINATOR[2]))

    def get_queryset(self):
        sort = self.request.GET.get("sort", None)
        user_departament_id = self.request.user.profile.departament_id
        queryset = ArticleProperties.objects.filter(published=True, departament_id=user_departament_id, is_special=True)

        if sort == "price":
            queryset = queryset.order_by("price")
        if sort == "-price":
            queryset = queryset.order_by("-price")

        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super(ArticleSaleListView, self).get_context_data(*args, **kwargs)
        params = self.request.GET.copy()
        if "page" in params:
            del params["page"]
        context.update(
            {
                "page_title": gettext_lazy("Sale"),
                "sort": self.request.GET.get("sort", None),
                "per_page": self.get_paginate_by(None),
                "paginator_list": settings.PAGINATOR,
                "link": urlencode(params),
            }
        )
        return context


class OrderListView(ActiveRequiredMixin, ListView):
    template_name = "commercial/order_list.html"
    context_object_name = "order_list"
    model = Order
    paginate_by = 25

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user, is_closed=True).order_by("-date")


class OrderDetailView(ActiveRequiredMixin, DetailView):
    template_name = "commercial/order_detail.html"
    context_object_name = "order"
    model = Order

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user, is_closed=True)


class ComplaintListView(ActiveRequiredMixin, ListView):
    template_name = "commercial/complaint_list.html"
    context_object_name = "complaint_list"
    model = Complaint
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)
        return queryset


class ComplaintCreateView(ActiveRequiredMixin, CreateView):
    template_name = "commercial/complaint_create.html"
    model = Complaint
    form_class = ComplaintForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        msg = Message.objects.create(
            complaint=self.object,
            user=self.request.user,
            text=form.cleaned_data["description"],
        )
        attachments = form.cleaned_data["attachments"]
        if attachments:
            for attach in attachments:
                MessageAttachment.objects.create(
                    message=msg,
                    file=attach,
                )
        send_complaint_mail.delay(self.object.id)
        return response


class ComplaintDetailView(ActiveRequiredMixin, FormView):
    template_name = "commercial/complaint_detail.html"
    form_class = MessageForm

    def get_success_url(self):
        return reverse("commercial_complaint_list")

    def get_object(self) -> Complaint:
        complaint = get_object_or_404(
            Complaint,
            pk=self.kwargs.get("pk"),
            user=self.request.user,
        )
        Message.objects.filter(complaint=complaint).update(is_read=True)
        return complaint

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "complaint": self.get_object(),
                "message_list": Message.objects.filter(complaint_id=self.kwargs.get("pk")),
            }
        )
        return context

    def form_valid(self, form):
        complaint = self.get_object()
        form.instance.user = self.request.user
        form.instance.complaint = complaint
        form.instance.is_read = True
        msg = form.save()
        attachments = form.cleaned_data["attachments"]
        if attachments:
            for attach in attachments:
                MessageAttachment.objects.create(
                    message=msg,
                    file=attach,
                )
        return super().form_valid(form)


class AddToCartView(ActiveRequiredMixin, TemplateView):
    template_name = "commercial/cart.html"

    def get_context_data(self, **kwargs):
        context = super(AddToCartView, self).get_context_data(**kwargs)
        user_departament_id = self.request.user.profile.departament_id
        order = getattr(self.request, "order", None)
        article_id = self.kwargs.get("id", None)
        try:
            count = int(self.kwargs.get("count", "1"))
        except ValueError:
            count = 1
        count = max(min(count, sys.maxsize), 1)
        logger.debug("add to cart: %s", order)
        if article_id:
            if not order:
                order = Order(user=self.request.user)
                order.save()
                self.request.session["order_id"] = order.pk
                self.request.order = order
            article_property = get_object_or_404(
                ArticleProperties,
                article_id=article_id,
                departament_id=user_departament_id,
            )
            order_item, _ = OrderItem.objects.get_or_create(order=order, article_id=article_id)
            order_item.count = count
            order_item.name = article_property.name
            order_item.volume = article_property.volume
            order_item.weight = article_property.weight
            order_item.barcode = article_property.barcode
            order_item.company = article_property.company
            order_item.price = article_property.get_price_for_user(self.request.user)
            order_item.full_price = article_property.price
            if article_property.main_image:
                order_item.main_image_url = article_property.main_image.url
            order_item.save()
        context.update({"order": self.request.order})
        return context


class EditCartView(ActiveRequiredMixin, TemplateResponseMixin, View):
    template_name = "commercial/editcart.html"

    def get(self, request, *args, **kwargs):
        OrderItemFormSet = modelformset_factory(OrderItem, form=OrderItemForm, can_delete=True, extra=0)
        order_form = EditOrderForm(instance=self.request.order)
        order_items_formset = OrderItemFormSet(queryset=OrderItem.objects.filter(order=self.request.order))
        context = {
            "order": request.order,
            "form": order_form,
            "order_items_formset": order_items_formset,
            "debts": UserDebs.objects.filter(user=request.user),
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        OrderItemFormSet = modelformset_factory(OrderItem, form=OrderItemForm, can_delete=True, extra=0)
        order_form = EditOrderForm(request.POST, instance=request.order)
        order_items_formset = OrderItemFormSet(request.POST, queryset=OrderItem.objects.filter(order=request.order))
        if order_form.is_valid() and order_items_formset.is_valid():
            order_form.save()
            order_items_formset.save()
            if order_items_formset.deleted_objects:
                order_items_formset = OrderItemFormSet(queryset=OrderItem.objects.filter(order=request.order))
            if request.POST.get("send") == "true":
                if hasattr(request, "order"):
                    order = request.order
                    order.is_closed = True
                    order.save()
                    send_order_email.delay(order.id)
                logout(request)
                return HttpResponseRedirect(reverse("commercial_order_complite"))
        context = {
            "order": request.order,
            "form": order_form,
            "order_items_formset": order_items_formset,
            "debts": UserDebs.objects.filter(user=request.user),
        }
        return self.render_to_response(context)


class DownloadArticleImages(ActiveRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        article_id = self.kwargs.get("id")
        user_departament_id = self.request.user.profile.departament
        article_property = get_object_or_404(
            ArticleProperties, article_id=article_id, departament_id=user_departament_id
        )
        images = ArticleImage.objects.filter(
            departament=user_departament_id,
            article_id=article_id,
        )
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zip_file:
            zip_file.writestr(
                article_property.main_image.name.rsplit("/", 1)[-1],
                article_property.main_image.read(),
            )
            for image in images:
                zip_file.writestr(image.image.name.rsplit("/", 1)[-1], image.image.read())
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=f"{article_id}.zip")


class ExportToXML(View):
    def get(self, request, *args, **kwargs):
        country = self.kwargs.get("country").upper() if "country" in self.kwargs else None
        departament = get_object_or_404(Departament, country=country)
        buffer = io.BytesIO()
        tree = export_department_to_xml(departament)

        tree.write(buffer, encoding="utf-8")
        buffer.seek(0)
        return HttpResponse(buffer, content_type="text/xml")


class ArticleNameAutocompleteView(ActiveRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # queryset = ArticleProperties.objects.annotate(
        #     similarity=TrigramSimilarity('name', request.GET.get('term'))
        # ).filter(similarity__gt=0.1, departament=request.user.profile.departament).only('name').order_by('-similarity')
        queryset = (
            ArticleProperties.objects.filter(
                name__search=request.GET.get("term"),
                departament=request.user.profile.departament,
            )
            .only("name", "article_id")
            .distinct()
        )
        return JsonResponse(
            [{"label": i.name, "value": i.article_id} for i in queryset],
            safe=False,
        )


class LatestComplaintsJSONView(ListView):
    queryset = Complaint.objects.all()
    ordering = ["-id"]

    def get_queryset(self):
        queryset = super().get_queryset().select_related("user__profile")
        return queryset[:10]

    def get(self, request, *args, **kwargs):
        data = []
        for complaint in self.get_queryset():  # type: Complaint
            msg = complaint.message_set.all().order_by("created_date").first()  # type: Message
            data.append(
                {
                    "id": complaint.id,
                    "inn": complaint.user.profile.inn,
                    "date_of_purchase": complaint.date_of_purchase,
                    "product": complaint.article_id,
                    "invoice": complaint.invoice,
                    "receipt": complaint.receipt.url if complaint.receipt else "",
                    "text": msg.text if msg else "",
                    "attachments": [i.file.url for i in msg.messageattachment_set.all()] if msg else [],
                }
            )
        return JsonResponse(data=data, status=200, safe=False)
