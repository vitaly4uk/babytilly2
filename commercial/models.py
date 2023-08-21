import logging
import typing
from decimal import Decimal

from ckeditor_uploader.fields import RichTextUploadingField
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy
from django_countries.fields import CountryField
from mptt.models import MPTTModel, TreeForeignKey
from sorl.thumbnail import ImageField

logger = logging.getLogger(__name__)


class Departament(models.Model):
    country = CountryField(gettext_lazy('country'))
    email = models.EmailField(gettext_lazy('email'))
    delivery_price = models.DecimalField(gettext_lazy('delivery price'), max_digits=10, decimal_places=3, default=0)

    def __str__(self):
        return str(self.country)

    class Meta:
        verbose_name = gettext_lazy('departament')
        verbose_name_plural = gettext_lazy('departaments')
        constraints = [
            models.UniqueConstraint(fields=['country', 'email'], name='unique_departament')
        ]


class DepartamentSale(models.Model):
    departament = models.ForeignKey(
        Departament, verbose_name=gettext_lazy('departament'), on_delete=models.CASCADE
    )
    order_sum = models.DecimalField(
        gettext_lazy('order sum'), max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    sale = models.DecimalField(
        gettext_lazy('sale in %'), max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    @classmethod
    def get_sale_for_departament(cls, departament: Departament, order_sum: Decimal) -> Decimal:
        departament_sale = cls.objects.only('sale').filter(
            departament=departament, order_sum__lte=order_sum
        ).order_by('-order_sum').first()
        if departament_sale:
            return departament_sale.sale
        return Decimal('0.0')

    def __str__(self):
        return f"{self.order_sum} - {self.sale}%"

    class Meta:
        verbose_name = gettext_lazy('departament sale')
        verbose_name_plural = gettext_lazy('departament sales')
        ordering = ['-order_sum']
        constraints = [
            models.UniqueConstraint(fields=['departament', 'order_sum', 'sale'], name='unique_departament_order_sum_sale')
        ]


class StartPageImage(models.Model):
    image = ImageField(gettext_lazy('image'), upload_to='start_page/%Y/%m/%d/%H/%m/')
    order = models.PositiveIntegerField(gettext_lazy('order'), default=100)

    def __str__(self):
        return self.image.name

    class Meta:
        verbose_name = gettext_lazy('start page image')
        verbose_name_plural = gettext_lazy('start page images')
        ordering = ['order']
        indexes = [
            models.Index(fields=['order'], name='order')
        ]


class Category(MPTTModel):
    id = models.CharField(max_length=25, primary_key=True)
    parent = TreeForeignKey(
        'self', verbose_name=gettext_lazy('parent'), null=True, blank=True, related_name='children',
        on_delete=models.CASCADE
    )
    property = models.ManyToManyField(Departament, through='CategoryProperties', verbose_name=gettext_lazy('property'))

    def __str__(self):
        return self.id

    def get_absolute_url(self):
        return reverse('category_detail_url', kwargs={'id': self.id})

    def get_ancestors_include_self(self):
        return self.get_ancestors(include_self=True)

    def get_ancestors_ids(self):
        query = self.get_ancestors(include_self=True)
        query = query.values_list('id', flat=True)
        return list(query)

    class Meta:
        verbose_name = gettext_lazy('category')
        verbose_name_plural = gettext_lazy('categories')


class CategoryProperties(models.Model):
    departament = models.ForeignKey(Departament, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(gettext_lazy('name'), max_length=255)
    published = models.BooleanField(gettext_lazy('published'), default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = gettext_lazy('category property')
        verbose_name_plural = gettext_lazy('category properties')
        constraints = [
            models.UniqueConstraint(fields=['departament', 'category'], name='unique_category_property')
        ]


class Article(models.Model):
    id = models.CharField(max_length=25, primary_key=True)
    category = TreeForeignKey(
        Category, verbose_name=gettext_lazy('category'), null=True, blank=True, on_delete=models.CASCADE
    )
    vendor_code = models.CharField(gettext_lazy('vendor code'), max_length=255, null=True)
    property = models.ManyToManyField(Departament, through='ArticleProperties', verbose_name=gettext_lazy('property'))

    class Meta:
        verbose_name = gettext_lazy('article')
        verbose_name_plural = gettext_lazy('articles')
        indexes = [
            models.Index(fields=['vendor_code'], name='vendor_code')
        ]


class ArticleProperties(models.Model):
    departament = models.ForeignKey(Departament, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    name = models.CharField(gettext_lazy('name'), max_length=255)
    description = models.TextField(gettext_lazy('description'), null=True)
    published = models.BooleanField(gettext_lazy('published'), default=True)
    price = models.DecimalField(gettext_lazy('trade price'), max_digits=10, decimal_places=3, default=0)
    retail_price = models.DecimalField(gettext_lazy('retail price'), max_digits=10, decimal_places=3, default=0)
    is_new = models.BooleanField(gettext_lazy('is new'), default=False)
    is_special = models.BooleanField(gettext_lazy('is special'), default=False)
    main_image = ImageField(gettext_lazy('main image'), upload_to='photos/%Y/%m/%d/%H/%m/', null=True)
    presence = models.CharField(gettext_lazy('presence'), max_length=127, null=True, blank=True)

    length = models.DecimalField(gettext_lazy('length'), null=True, blank=True, decimal_places=2, max_digits=10)
    width = models.DecimalField(gettext_lazy('width'), null=True, blank=True, decimal_places=2, max_digits=10)
    height = models.DecimalField(gettext_lazy('height'), null=True, blank=True, decimal_places=2, max_digits=10)

    volume = models.DecimalField(gettext_lazy('volume'), default=0, blank=True, decimal_places=2, max_digits=10)
    weight = models.DecimalField(gettext_lazy('weight'), default=0, blank=True, decimal_places=2, max_digits=10)

    barcode = models.CharField(gettext_lazy('barcode'), max_length=255, null=True, blank=True)

    image_link = models.URLField(gettext_lazy('image link'), null=True, blank=True)
    video_link = models.URLField(gettext_lazy('video link'), null=True, blank=True)
    site_link = models.URLField(gettext_lazy('site link'), null=True, blank=True)

    company = models.CharField(gettext_lazy('company'), max_length=255, null=True, blank=True)
    order = models.PositiveSmallIntegerField(gettext_lazy('article order'), default=1000)

    @property
    def is_less_then_five(self):
        return self.presence.lower() == '1'

    def get_price_for_user(self, user):
        price = self.price
        if user.profile.sale:
            price -= price * user.profile.sale / 100
        return price

    class Meta:
        verbose_name = gettext_lazy('article property')
        verbose_name_plural = gettext_lazy('article properties')
        constraints = [
            models.UniqueConstraint(fields=['departament', 'article'], name='unique_article_property')
        ]
        ordering = ['order', 'name']


class ArticleImage(models.Model):
    article = models.ForeignKey(Article, verbose_name=gettext_lazy('article'), related_name='images',
                                on_delete=models.CASCADE)
    departament = models.ForeignKey(Departament, on_delete=models.CASCADE, null=True)
    image = ImageField(gettext_lazy('image'), upload_to='photos/%Y/%m/%d/%H/%m/')

    def __str__(self):
        return str(self.image)

    class Meta:
        verbose_name = gettext_lazy('image')
        verbose_name_plural = gettext_lazy('images')


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=gettext_lazy('user'), on_delete=models.CASCADE)
    date = models.DateTimeField(gettext_lazy('date'), auto_now_add=True)
    comment = models.TextField(default='', blank=True)
    is_closed = models.BooleanField(gettext_lazy('closed'), default=False)

    def __str__(self):
        return str(self.pk)

    def get_order_items(self) -> typing.List['OrderItem']:
        if getattr(self, '_items', None) is None:
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
            sale = DepartamentSale.get_sale_for_departament(self.user.profile.departament, order_sum)
            order_sum -= order_sum * sale / 100 if sale else 0
        return order_sum
    sum.short_description = gettext_lazy('Sum')

    def discount(self):
        if self.full_sum():
            discount_sum = self.full_sum() - self.sum()
            return {
                'sum': discount_sum,
                'percent': discount_sum * 100 / self.full_sum()
            }
        return {
            'sum': 0,
            'percent': 0
        }

    def total_sum_with_delivery(self) -> typing.Dict:
        delivery_price = self.user.profile.departament.delivery_price
        total_sum = self.full_sum()
        if delivery_price:
            delivery_full_price = delivery_price * self.full_count()
            return {
                'delivery_price': delivery_full_price,
                'total_sum': self.full_sum() - delivery_full_price
            }
        return {
            'delivery_price': 0,
            'total_sum': self.full_sum()
        }






    def volume(self):
        return sum(i.volume * i.count for i in self.get_order_items())

    def weight(self):
        return sum(i.weight * i.count for i in self.get_order_items())

    def get_absolute_url(self):
        return reverse('commercial_order_detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = gettext_lazy('order')
        verbose_name_plural = gettext_lazy('orders')
        constraints = [
            models.UniqueConstraint(fields=['user'], condition=models.Q(is_closed=False), name='unique_open_order')
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name=gettext_lazy('order'), related_name='items', on_delete=models.CASCADE)
    article = models.ForeignKey(Article, verbose_name=gettext_lazy('article'), on_delete=models.CASCADE)
    name = models.CharField(gettext_lazy('name'), max_length=255, null=True)
    count = models.PositiveIntegerField(gettext_lazy('count'), default=0)
    volume = models.DecimalField(gettext_lazy('volume'), default=0, blank=True, decimal_places=2, max_digits=10)
    weight = models.DecimalField(gettext_lazy('weight'), default=0, blank=True, decimal_places=2, max_digits=10)
    price = models.DecimalField(gettext_lazy('price'), max_digits=10, decimal_places=3, default=0)
    full_price = models.DecimalField(gettext_lazy('full price'), max_digits=10, decimal_places=3, default=0, editable=False)
    barcode = models.CharField(gettext_lazy('barcode'), max_length=255, null=True, blank=True)
    company = models.CharField(gettext_lazy('company'), max_length=255, null=True, blank=True)
    main_image_url = models.URLField(gettext_lazy('main image url'), null=True, blank=True, editable=False)

    def __str__(self):
        return self.name

    def sum(self):
        return self.count * self.price

    def full_sum(self):
        return self.count * self.full_price

    class Meta:
        verbose_name = gettext_lazy('order item')
        verbose_name_plural = gettext_lazy('order items')
        constraints = [
            models.UniqueConstraint(fields=['order', 'article'], name='unique_order_item')
        ]


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=gettext_lazy('user'), on_delete=models.CASCADE)
    departament = models.ForeignKey(Departament, verbose_name=gettext_lazy('departament'), on_delete=models.CASCADE)
    sale = models.DecimalField(
        gettext_lazy('sale in %'), max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    additional_emails = models.CharField(gettext_lazy('additional email addresses'), max_length=128, default='',
                                         help_text=gettext_lazy('Enter multiple mailboxes separated by commas'),
                                         blank=True)

    def __str__(self):
        return f"Profile for {self.user}"

    class Meta:
        verbose_name = gettext_lazy('profile')
        verbose_name_plural = gettext_lazy('profiles')


class ImportPrice(models.Model):
    file = models.FileField(gettext_lazy('file'), upload_to='import_price/%Y/%m/%d/%H/%m/')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=gettext_lazy('user'), on_delete=models.CASCADE)
    departament = models.ForeignKey(Departament, verbose_name=gettext_lazy('departament'), on_delete=models.CASCADE)
    imported_at = models.DateTimeField(gettext_lazy('imported at'), auto_now_add=True)

    def __str__(self):
        return f'ImportPrice by {self.user} at {self.imported_at.strftime("%Y-%m-%d %H:%M:%S")}'

    def save(self, *args, **kwargs):
        from commercial.tasks import import_price
        super(ImportPrice, self).save(*args, **kwargs)
        import_price.delay(self.id)

    class Meta:
        verbose_name = gettext_lazy('import price')
        verbose_name_plural = gettext_lazy('import prices')


class ImportNew(models.Model):
    file = models.FileField(gettext_lazy('file'), upload_to='import_new/%Y/%m/%d/%H/%m/')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=gettext_lazy('user'), on_delete=models.CASCADE)
    departament = models.ForeignKey(Departament, verbose_name=gettext_lazy('departament'), on_delete=models.CASCADE)
    imported_at = models.DateTimeField(gettext_lazy('imported at'), auto_now_add=True)

    def __str__(self):
        return f'ImportNew by {self.user} at {self.imported_at.strftime("%Y-%m-%d %H:%M:%S")}'

    def save(self, *args, **kwargs):
        from commercial.tasks import import_novelty
        super(ImportNew, self).save(*args, **kwargs)
        import_novelty.delay(self.id)

    class Meta:
        verbose_name = gettext_lazy('import new')
        verbose_name_plural = gettext_lazy('import news')


class ImportSpecial(models.Model):
    file = models.FileField(gettext_lazy('file'), upload_to='import_special/%Y/%m/%d/%H/%m/')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=gettext_lazy('user'), on_delete=models.CASCADE)
    departament = models.ForeignKey(Departament, verbose_name=gettext_lazy('departament'), on_delete=models.CASCADE)
    imported_at = models.DateTimeField(gettext_lazy('imported at'), auto_now_add=True)

    def __str__(self):
        return f'ImportSpecial by {self.user} at {self.imported_at.strftime("%Y-%m-%d %H:%M:%S")}'

    def save(self, *args, **kwargs):
        from commercial.tasks import import_special
        super(ImportSpecial, self).save(*args, **kwargs)
        import_special.delay(self.id)

    class Meta:
        verbose_name = gettext_lazy('import special')
        verbose_name_plural = gettext_lazy('import specials')


class Page(models.Model):
    ABOUT = 'about'
    CONTACTS = 'contacts'
    TYPE = (
        (ABOUT, gettext_lazy('about')),
        (CONTACTS, gettext_lazy('contacts')),
    )
    slug = models.SlugField(gettext_lazy('slug'), choices=TYPE, null=True)
    departament = models.ForeignKey(Departament, verbose_name=gettext_lazy('departament'), on_delete=models.CASCADE)
    text = RichTextUploadingField(gettext_lazy('text'))

    def __str__(self):
        return f'{self.slug}'

    def get_absolute_url(self):
        return reverse('page_detail_url', kwargs={'slug': self.slug})

    class Meta:
        verbose_name = gettext_lazy('page')
        verbose_name_plural = gettext_lazy('pages')
