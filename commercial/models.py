import logging
import typing
from decimal import Decimal

from ckeditor_uploader.fields import RichTextUploadingField
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.indexes import GistIndex
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    FileExtensionValidator,
)
from django.db import models
from django.urls import reverse
from django.utils import formats
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from mptt.models import MPTTModel, TreeForeignKey
from sorl.thumbnail import ImageField

logger = logging.getLogger(__name__)


class Departament(models.Model):
    country = CountryField(_("country"))
    email = models.EmailField(_("email"))

    def __str__(self):
        return str(self.country)

    class Meta:
        verbose_name = _("departament")
        verbose_name_plural = _("departaments")
        constraints = [
            models.UniqueConstraint(
                fields=["country", "email"], name="unique_departament"
            )
        ]


class DepartamentSale(models.Model):
    departament = models.ForeignKey(
        Departament, verbose_name=_("departament"), on_delete=models.CASCADE
    )
    order_sum = models.DecimalField(
        _("order sum"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    sale = models.DecimalField(
        _("sale in %"),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    @classmethod
    def get_sale_for_departament(
        cls, departament: Departament, order_sum: Decimal
    ) -> Decimal:
        departament_sale = (
            cls.objects.only("sale")
            .filter(departament=departament, order_sum__lte=order_sum)
            .order_by("-order_sum")
            .first()
        )
        if departament_sale:
            return departament_sale.sale
        return Decimal("0.0")

    def __str__(self):
        return f"{self.order_sum} - {self.sale}%"

    class Meta:
        verbose_name = _("departament sale")
        verbose_name_plural = _("departament sales")
        ordering = ["-order_sum"]
        constraints = [
            models.UniqueConstraint(
                fields=["departament", "order_sum", "sale"],
                name="unique_departament_order_sum_sale",
            )
        ]


class Delivery(models.Model):
    country = CountryField(_("country"))
    price = models.DecimalField(
        _("delivery price"), max_digits=10, decimal_places=3, default=0
    )

    def __str__(self):
        return self.country.name

    class Meta:
        verbose_name = _("delivery price")
        verbose_name_plural = _("delivery prices")
        constraints = [
            models.UniqueConstraint(
                fields=["country", "price"], name="unique_delivery_price"
            )
        ]


class StartPageImage(models.Model):
    image = ImageField(_("image"), upload_to="start_page/%Y/%m/%d/%H/%m/")
    order = models.PositiveIntegerField(_("order"), default=100)

    def __str__(self):
        return self.image.name

    class Meta:
        verbose_name = _("start page image")
        verbose_name_plural = _("start page images")
        ordering = ["order"]
        indexes = [models.Index(fields=["order"], name="order")]


class Category(MPTTModel):
    id = models.CharField(max_length=25, primary_key=True)
    parent = TreeForeignKey(
        "self",
        verbose_name=_("parent"),
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
    )
    property = models.ManyToManyField(
        Departament, through="CategoryProperties", verbose_name=_("property")
    )

    def __str__(self):
        return self.id

    def get_absolute_url(self):
        return reverse("category_detail_url", kwargs={"id": self.id})

    def get_ancestors_include_self(self):
        return self.get_ancestors(include_self=True)

    def get_ancestors_ids(self):
        query = self.get_ancestors(include_self=True)
        query = query.values_list("id", flat=True)
        return list(query)

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")


class CategoryProperties(models.Model):
    departament = models.ForeignKey(Departament, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(_("name"), max_length=255)
    published = models.BooleanField(_("published"), default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("category property")
        verbose_name_plural = _("category properties")
        constraints = [
            models.UniqueConstraint(
                fields=["departament", "category"], name="unique_category_property"
            )
        ]


class Article(models.Model):
    id = models.CharField(max_length=25, primary_key=True)
    category = TreeForeignKey(
        Category,
        verbose_name=_("category"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    vendor_code = models.CharField(_("vendor code"), max_length=255, null=True)
    property = models.ManyToManyField(
        Departament, through="ArticleProperties", verbose_name=_("property")
    )

    class Meta:
        verbose_name = _("article")
        verbose_name_plural = _("articles")
        indexes = [models.Index(fields=["vendor_code"], name="vendor_code")]


class ArticleProperties(models.Model):
    departament = models.ForeignKey(Departament, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    name = models.CharField(_("name"), max_length=255)
    description = models.TextField(_("description"), null=True)
    published = models.BooleanField(_("published"), default=True)
    price = models.DecimalField(
        _("trade price"), max_digits=10, decimal_places=3, default=0
    )
    retail_price = models.DecimalField(
        _("retail price"), max_digits=10, decimal_places=3, default=0
    )
    is_new = models.BooleanField(_("is new"), default=False)
    is_special = models.BooleanField(_("is special"), default=False)
    main_image = ImageField(
        _("main image"), upload_to="photos/%Y/%m/%d/%H/%m/", null=True
    )
    presence = models.CharField(_("presence"), max_length=127, null=True, blank=True)

    length = models.DecimalField(
        _("length"), null=True, blank=True, decimal_places=2, max_digits=10
    )
    width = models.DecimalField(
        _("width"), null=True, blank=True, decimal_places=2, max_digits=10
    )
    height = models.DecimalField(
        _("height"), null=True, blank=True, decimal_places=2, max_digits=10
    )

    volume = models.DecimalField(
        _("volume"), default=0, blank=True, decimal_places=2, max_digits=10
    )
    weight = models.DecimalField(
        _("weight"), default=0, blank=True, decimal_places=2, max_digits=10
    )

    barcode = models.CharField(_("barcode"), max_length=255, null=True, blank=True)

    image_link = models.URLField(_("image link"), null=True, blank=True)
    video_link = models.URLField(_("video link"), null=True, blank=True)
    site_link = models.URLField(_("site link"), null=True, blank=True)

    company = models.CharField(_("company"), max_length=255, null=True, blank=True)
    order = models.PositiveSmallIntegerField(_("article order"), default=1000)

    @property
    def is_less_then_five(self):
        if self.presence:
            return self.presence.lower() == "1"
        return False

    def get_price_for_user(self, user):
        price = self.price
        if user.profile.sale:
            price -= price * user.profile.sale / 100
        return price

    class Meta:
        verbose_name = _("article property")
        verbose_name_plural = _("article properties")
        constraints = [
            models.UniqueConstraint(
                fields=["departament", "article"], name="unique_article_property"
            ),
            GistIndex(
                name="gist_trgm_idx", fields=["name"], opclasses=["gist_trgm_ops"]
            ),
        ]
        ordering = ["order", "name"]


class ArticleImage(models.Model):
    article = models.ForeignKey(
        Article,
        verbose_name=_("article"),
        related_name="images",
        on_delete=models.CASCADE,
    )
    departament = models.ForeignKey(Departament, on_delete=models.CASCADE, null=True)
    image = ImageField(_("image"), upload_to="photos/%Y/%m/%d/%H/%m/")

    def __str__(self):
        return str(self.image)

    class Meta:
        verbose_name = _("image")
        verbose_name_plural = _("images")


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("user"), on_delete=models.CASCADE
    )
    date = models.DateTimeField(_("date"), auto_now_add=True)
    delivery = models.ForeignKey(
        Delivery, verbose_name=_("delivery"), on_delete=models.SET_NULL, null=True
    )
    comment = models.TextField(default="", blank=True)
    is_closed = models.BooleanField(_("closed"), default=False)

    def __str__(self):
        return str(self.pk)

    def get_order_items(self) -> typing.List["OrderItem"]:
        if getattr(self, "_items", None) is None:
            self._items = list(self.items.all())
        return self._items

    def get_order_article_ids(self):
        return list(i.article_id for i in self.get_order_items())

    def full_count(self) -> int:
        return sum(i.count for i in self.get_order_items())

    def full_sum(self):
        return sum(i.full_price * i.count for i in self.get_order_items())

    def sum(self) -> Decimal:
        order_sum = sum(i.price * i.count for i in self.get_order_items())
        if not self.user.profile.sale:
            sale = DepartamentSale.get_sale_for_departament(
                self.user.profile.departament, order_sum
            )
            order_sum -= order_sum * sale / 100 if sale else 0
        return order_sum

    sum.short_description = _("Sum")

    def discount(self):
        if self.full_sum():
            discount_sum = self.full_sum() - self.sum()
            return {
                "sum": discount_sum,
                "percent": discount_sum * 100 / self.full_sum(),
            }
        return {"sum": 0, "percent": 0}

    def total_sum_with_delivery(self) -> typing.Dict:
        try:
            delivery_price = self.delivery.price
        except (ValueError, AttributeError):
            delivery_price = 0
        if delivery_price:
            delivery_full_price = delivery_price * self.full_count()
            return {
                "delivery_price": delivery_full_price,
                "total_sum": self.sum() + delivery_full_price,
            }
        return {"delivery_price": 0, "total_sum": self.sum()}

    def volume(self):
        return sum(i.volume * i.count for i in self.get_order_items())

    def weight(self):
        return sum(i.weight * i.count for i in self.get_order_items())

    def get_absolute_url(self):
        return reverse("commercial_order_detail", kwargs={"pk": self.pk})

    class Meta:
        verbose_name = _("order")
        verbose_name_plural = _("orders")
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(is_closed=False),
                name="unique_open_order",
            )
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, verbose_name=_("order"), related_name="items", on_delete=models.CASCADE
    )
    article = models.ForeignKey(
        Article, verbose_name=_("article"), on_delete=models.CASCADE
    )
    name = models.CharField(_("name"), max_length=255, null=True)
    count = models.PositiveIntegerField(_("count"), default=0)
    volume = models.DecimalField(
        _("volume"), default=0, blank=True, decimal_places=2, max_digits=10
    )
    weight = models.DecimalField(
        _("weight"), default=0, blank=True, decimal_places=2, max_digits=10
    )
    price = models.DecimalField(_("price"), max_digits=10, decimal_places=3, default=0)
    full_price = models.DecimalField(
        _("full price"), max_digits=10, decimal_places=3, default=0, editable=False
    )
    barcode = models.CharField(_("barcode"), max_length=255, null=True, blank=True)
    company = models.CharField(_("company"), max_length=255, null=True, blank=True)
    main_image_url = models.URLField(
        _("main image url"), null=True, blank=True, editable=False
    )

    def __str__(self):
        return self.name

    def sum(self):
        return self.count * self.price

    def full_sum(self):
        return self.count * self.full_price

    class Meta:
        verbose_name = _("order item")
        verbose_name_plural = _("order items")
        constraints = [
            models.UniqueConstraint(
                fields=["order", "article"], name="unique_order_item"
            )
        ]


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name=_("user"), on_delete=models.CASCADE
    )
    departament = models.ForeignKey(
        Departament, verbose_name=_("departament"), on_delete=models.CASCADE
    )
    sale = models.DecimalField(
        _("sale in %"),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    additional_emails = models.CharField(
        _("additional email addresses"),
        max_length=128,
        default="",
        help_text=_("Enter multiple mailboxes separated by commas"),
        blank=True,
    )
    inn = models.CharField(_("inn"), max_length=127, null=True, blank=True)

    def __str__(self):
        return f"Profile for {self.user}"

    class Meta:
        verbose_name = _("profile")
        verbose_name_plural = _("profiles")


class UserDebs(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("user"), on_delete=models.CASCADE
    )
    document = models.CharField(_("document"), max_length=127)
    date_of_sale = models.DateField(_("date of sale"))
    amount = models.DecimalField(
        _("amount"), max_digits=10, decimal_places=3, default=0
    )

    def __str__(self):
        return f"{self.user} {self.document}"

    class Meta:
        verbose_name = _("debt")
        verbose_name_plural = _("debts")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "document"], name="unique_user_document"
            )
        ]


class ImportPrice(models.Model):
    file = models.FileField(_("file"), upload_to="import_price/%Y/%m/%d/%H/%m/")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": True},
    )
    departament = models.ForeignKey(
        Departament, verbose_name=_("departament"), on_delete=models.CASCADE
    )
    imported_at = models.DateTimeField(_("imported at"), auto_now_add=True)

    def __str__(self):
        return f'ImportPrice by {self.user} at {self.imported_at.strftime("%Y-%m-%d %H:%M:%S")}'

    def save(self, *args, **kwargs):
        from commercial.tasks import import_price

        super(ImportPrice, self).save(*args, **kwargs)
        import_price.apply_async(kwargs={"import_id": self.id}, countdown=30)

    class Meta:
        verbose_name = _("import price")
        verbose_name_plural = _("import prices")


class ImportNew(models.Model):
    file = models.FileField(_("file"), upload_to="import_new/%Y/%m/%d/%H/%m/")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": True},
    )
    departament = models.ForeignKey(
        Departament, verbose_name=_("departament"), on_delete=models.CASCADE
    )
    imported_at = models.DateTimeField(_("imported at"), auto_now_add=True)

    def __str__(self):
        return f'ImportNew by {self.user} at {self.imported_at.strftime("%Y-%m-%d %H:%M:%S")}'

    def save(self, *args, **kwargs):
        from commercial.tasks import import_novelty

        super(ImportNew, self).save(*args, **kwargs)
        import_novelty.apply_async(kwargs={"import_id": self.id}, countdown=30)

    class Meta:
        verbose_name = _("import new")
        verbose_name_plural = _("import news")


class ImportSpecial(models.Model):
    file = models.FileField(_("file"), upload_to="import_special/%Y/%m/%d/%H/%m/")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": True},
    )
    departament = models.ForeignKey(
        Departament, verbose_name=_("departament"), on_delete=models.CASCADE
    )
    imported_at = models.DateTimeField(_("imported at"), auto_now_add=True)

    def __str__(self):
        return f'ImportSpecial by {self.user} at {self.imported_at.strftime("%Y-%m-%d %H:%M:%S")}'

    def save(self, *args, **kwargs):
        from commercial.tasks import import_special

        super(ImportSpecial, self).save(*args, **kwargs)
        import_special.apply_async(kwargs={"import_id": self.id}, countdown=30)

    class Meta:
        verbose_name = _("import special")
        verbose_name_plural = _("import specials")


class ImportDebs(models.Model):
    file = models.FileField(_("file"), upload_to="import_debs/%Y/%m/%d/%H/%m/")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": True},
    )
    imported_at = models.DateTimeField(_("imported at"), auto_now_add=True)

    def __str__(self):
        return f'ImportSpecial by {self.user} at {self.imported_at.strftime("%Y-%m-%d %H:%M:%S")}'

    def save(self, *args, **kwargs):
        from commercial.tasks import import_debs

        super(ImportDebs, self).save(*args, **kwargs)
        import_debs.apply_async(kwargs={"import_id": self.id}, countdown=30)

    class Meta:
        verbose_name = _("import debt")
        verbose_name_plural = _("import debts")


class Page(models.Model):
    ABOUT = "about"
    CONTACTS = "contacts"
    TYPE = (
        (ABOUT, _("about")),
        (CONTACTS, _("contacts")),
    )
    slug = models.SlugField(_("slug"), choices=TYPE, null=True)
    departament = models.ForeignKey(
        Departament, verbose_name=_("departament"), on_delete=models.CASCADE
    )
    text = RichTextUploadingField(_("text"))

    def __str__(self):
        return f"{self.slug}"

    def get_absolute_url(self):
        return reverse("page_detail_url", kwargs={"slug": self.slug})

    class Meta:
        verbose_name = _("page")
        verbose_name_plural = _("pages")


class Complaint(models.Model):
    class ComplaintStatus(models.IntegerChoices):
        OPENED = 0, _("opened")
        CLOSED = 1, _("closed")
        IN_PROGRESS = 2, _("in progress")
        NO_ANSWER = 3, _('no answer')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("user"), on_delete=models.CASCADE
    )
    date_of_purchase = models.DateField(
        _("date of purchase"),
        help_text=_("Please, fill date in format %s")
        % formats.get_format("SHORT_DATE_FORMAT"),
    )
    article = models.ForeignKey(
        Article, verbose_name=_("article"), on_delete=models.CASCADE, null=True
    )
    invoice = models.CharField(_("invoice No"), max_length=127)
    receipt = ImageField(
        _("receipt"), null=True, upload_to="attachment/%Y/%m/%d/%H/%m/"
    )
    status = models.IntegerField(
        _("status"), choices=ComplaintStatus.choices, default=ComplaintStatus.OPENED
    )
    created_date = models.DateField(_("date of create"), auto_now_add=True)

    def image(self):
        msg: Message = self.message_set.first()
        if msg:
            attach: MessageAttachment = msg.messageattachment_set.first()
            if attach:
                return attach.file

    def product_name(self):
        article_property = (
            ArticleProperties.objects.filter(
                departament=self.user.profile.departament, article=self.article
            )
            .only("name")
            .first()
        )
        if article_property:
            return article_property.name

    def __str__(self):
        return f"{self.user} {self.product_name()}"

    def get_absolute_url(self):
        return reverse("commercial_complaint_detail", kwargs={"pk": self.pk})

    def has_answer(self):
        msg = (
            Message.objects.filter(complaint=self)
            .select_related("user")
            .only("user")
            .order_by("-created_date")
            .first()
        )
        if msg:
            return msg.user.is_staff
        return False

    def has_unread(self):
        return (
            Message.objects.filter(complaint=self, is_read=False)
            .exclude(complaint__status=Complaint.ComplaintStatus.CLOSED)
            .exists()
        )

    class Meta:
        verbose_name = _("complaint")
        verbose_name_plural = _("complaints")
        ordering = ["-id"]


class Message(models.Model):
    complaint = models.ForeignKey(
        Complaint, verbose_name=_("complaint"), on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("user"), on_delete=models.CASCADE
    )
    text = models.TextField(_("text"))
    created_date = models.DateTimeField(_("created date"), auto_now_add=True)
    is_read = models.BooleanField(_("is read"), default=False, editable=False)

    def __str__(self):
        return f"{formats.date_format(self.created_date)} {formats.time_format(self.created_date)}"

    class Meta:
        verbose_name = _("message")
        verbose_name_plural = _("messages")
        ordering = ["created_date"]


class MessageAttachment(models.Model):
    message = models.ForeignKey(
        Message, verbose_name=_("message"), on_delete=models.CASCADE
    )
    file = models.FileField(
        _("file"),
        blank=True,
        null=True,
        upload_to="attachment/%Y/%m/%d/%H/%m/",
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "mov",
                    "avi",
                    "mp4",
                    "webm",
                    "mkv",
                    "jpg",
                    "jpeg",
                    "png",
                ]
            )
        ],
    )

    def file_name(self):
        return self.file.name.rsplit("/")[-1]

    def __str__(self):
        return self.file.name

    class Meta:
        verbose_name = _("attachment")
        verbose_name_plural = _("attachments")
