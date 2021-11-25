import logging

from ckeditor_uploader.fields import RichTextUploadingField
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import smart_text
from django.utils.translation import gettext_lazy
from django_countries.fields import CountryField
from mptt.models import MPTTModel, TreeForeignKey
from sorl.thumbnail import ImageField

from commercial.functions import get_thumbnail_url, export_to_csv

logger = logging.getLogger(__name__)


class Departament(models.Model):
    country = CountryField(gettext_lazy('country'))
    email = models.EmailField(gettext_lazy('email'))

    def __str__(self):
        return str(self.country)

    class Meta:
        verbose_name = gettext_lazy('departament')
        verbose_name_plural = gettext_lazy('departaments')
        constraints = [
            models.UniqueConstraint(fields=['country', 'email'], name='unique_departament')
        ]


class StartPageImage(models.Model):
    image = ImageField(gettext_lazy('image'), upload_to='start_page/')
    order = models.PositiveIntegerField(gettext_lazy('order'), default=100)

    def __str__(self):
        return self.image.name

    class Meta:
        verbose_name = gettext_lazy('start page image')
        verbose_name_plural = gettext_lazy('start page images')
        ordering = ['order']
        indexes = [
            models.Index(fields=['order'], include=['image'], name='order')
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
    image = ImageField(gettext_lazy('image'), upload_to='photos/')
    property = models.ManyToManyField(Departament, through='ArticleProperties', verbose_name=gettext_lazy('property'))

    def get_small_thumbnail_url(self):
        url = cache.get(f'small-thumb-url-{self.image.name}')
        if url is None:
            url = get_thumbnail_url(self.image, settings.THUMBNAIL_SIZE['small'])
            cache.set(f'small-thumb-url-{self.image.name}', url)
        return url

    def get_big_thumbnail_url(self):
        url = cache.get(f'big-thumb-url-{self.image.name}')
        if url is None:
            url = get_thumbnail_url(self.image, settings.THUMBNAIL_SIZE['big'])
            cache.set(f'big-thumb-url-{self.image.name}', url)
        return url

    def get_image_url(self):
        return self.image.url

    class Meta:
        verbose_name = gettext_lazy('article')
        verbose_name_plural = gettext_lazy('articles')


class ArticleProperties(models.Model):
    departament = models.ForeignKey(Departament, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    name = models.CharField(gettext_lazy('name'), max_length=255)
    published = models.BooleanField(gettext_lazy('published'), default=True)
    price = models.DecimalField(gettext_lazy('price'), max_digits=10, decimal_places=3, default=0)
    is_new = models.BooleanField(gettext_lazy('is new'), default=False)
    is_special = models.BooleanField(gettext_lazy('is special'), default=False)

    class Meta:
        verbose_name = gettext_lazy('article property')
        verbose_name_plural = gettext_lazy('article properties')
        constraints = [
            models.UniqueConstraint(fields=['departament', 'article'], name='unique_article_property')
        ]


class ArticleImage(models.Model):
    article = models.ForeignKey(Article, verbose_name=gettext_lazy('article'), related_name='images',
                                on_delete=models.CASCADE)
    image = ImageField(gettext_lazy('image'), upload_to='photos/')

    def get_small_thumbnail_url(self):
        url = cache.get(f'small-thumb-url-{self.image.name}')
        if url is None:
            url = get_thumbnail_url(self.image, settings.THUMBNAIL_SIZE['small'])
            cache.set(f'small-thumb-url-{self.image.name}', url)
        return url

    def get_big_thumbnail_url(self):
        url = cache.get(f'big-thumb-url-{self.image.name}')
        if url is None:
            url = get_thumbnail_url(self.image, settings.THUMBNAIL_SIZE['big'])
            cache.set(f'big-thumb-url-{self.image.name}', url)
        return url

    class Meta:
        verbose_name = gettext_lazy('image')
        verbose_name_plural = gettext_lazy('images')


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=gettext_lazy('user'), on_delete=models.CASCADE)
    date = models.DateTimeField(gettext_lazy('date'), auto_now_add=True)
    comment = models.TextField(default='')
    is_closed = models.BooleanField(gettext_lazy('closed'), default=False)

    def __str__(self):
        return str(self.pk)

    def get_order_items(self):
        if getattr(self, '_items', None) is None:
            self._items = list(self.items.all())
        return self._items

    def count(self):
        return sum(i.count for i in self.get_order_items())

    def sum(self):
        return sum(i.price * i.count for i in self.get_order_items())

    sum.short_description = gettext_lazy('Sum')

    def add_item(self, article: Article, count: int):
        cart_item, _ = OrderItem.objects.get_or_create(
            cart=self,
            article=article,
            price=article.price,
        )
        cart_item.count += count
        cart_item.save()
        self.items.add(cart_item)
        self.recalculate()

    def get_absolute_url(self):
        return reverse('commercial_order_detail', kwargs={'pk': self.pk})

    def send(self):
        context = {
            'cart': self.items.all(),
            'order': self,
            'profile': self.user
        }
        html_body = str(render_to_string('commercial/mail.html', context))
        text_body = str(render_to_string('commercial/mail_text.html', context))
        stuff_email = Departament.objects.get(id=self.user.profile.departament_id).email
        to_emails = [settings.DEFAULT_FROM_EMAIL, stuff_email]
        if self.user.email:
            to_emails.append(self.user.email)
        logger.debug('Sending order to: {}'.format(to_emails))
        msg = EmailMultiAlternatives(
            subject='Заказ {} {}'.format(self, self.user),
            body=text_body,
            to=to_emails
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.attach('zakaz{}.csv'.format(self.pk), export_to_csv(None, self, 'cp1251'), 'text/csv')
        msg.send()

    class Meta:
        verbose_name = gettext_lazy('order')
        verbose_name_plural = gettext_lazy('orders')
        constraints = [
            models.UniqueConstraint(fields=['user'], condition=models.Q(is_closed=False), name='unique_open_order')
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name=gettext_lazy('order'), related_name='items', on_delete=models.CASCADE)
    article = models.ForeignKey(Article, verbose_name=gettext_lazy('article'), on_delete=models.CASCADE)
    count = models.PositiveIntegerField(gettext_lazy('count'), default=0)
    price = models.DecimalField(gettext_lazy('price'), max_digits=10, decimal_places=3, default=0)

    def __str__(self):
        return smart_text(self.article.name)

    def sum(self):
        return self.count * self.price

    class Meta:
        verbose_name = gettext_lazy('order item')
        verbose_name_plural = gettext_lazy('order items')
        constraints = [
            models.UniqueConstraint(fields=['order', 'article'], name='unique_order_item')
        ]


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=gettext_lazy('user'), on_delete=models.CASCADE)
    departament = models.ForeignKey(Departament, verbose_name=gettext_lazy('departament'), on_delete=models.CASCADE)

    def __str__(self):
        return f"Profile for {self.user}"

    class Meta:
        verbose_name = gettext_lazy('profile')
        verbose_name_plural = gettext_lazy('profiles')


class ImportPrice(models.Model):
    file = models.FileField(gettext_lazy('file'), upload_to='import_price/%Y/%m/%d/')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=gettext_lazy('user'), on_delete=models.CASCADE)
    departament = models.ForeignKey(Departament, verbose_name=gettext_lazy('departament'), on_delete=models.CASCADE)
    imported_at = models.DateTimeField(gettext_lazy('imported at'), auto_now_add=True)

    def save(self, *args, **kwargs):
        from commercial.tasks import import_price
        super(ImportPrice, self).save(*args, **kwargs)
        import_price.delay(self.id)

    class Meta:
        verbose_name = gettext_lazy('import price')
        verbose_name_plural = gettext_lazy('import prices')


class ImportNew(models.Model):
    file = models.FileField(gettext_lazy('file'), upload_to='import_new/%Y/%m/%d/')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=gettext_lazy('user'), on_delete=models.CASCADE)
    departament = models.ForeignKey(Departament, verbose_name=gettext_lazy('departament'), on_delete=models.CASCADE)
    imported_at = models.DateTimeField(gettext_lazy('imported at'), auto_now_add=True)

    def save(self, *args, **kwargs):
        from commercial.tasks import import_novelty
        super(ImportPrice, self).save(*args, **kwargs)
        import_novelty.delay(self.id)

    class Meta:
        verbose_name = gettext_lazy('import new')
        verbose_name_plural = gettext_lazy('import news')


class ImportSpecial(models.Model):
    file = models.FileField(gettext_lazy('file'), upload_to='import_special/%Y/%m/%d/')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=gettext_lazy('user'), on_delete=models.CASCADE)
    departament = models.ForeignKey(Departament, verbose_name=gettext_lazy('departament'), on_delete=models.CASCADE)
    imported_at = models.DateTimeField(gettext_lazy('imported at'), auto_now_add=True)

    def save(self, *args, **kwargs):
        from commercial.tasks import import_special
        super(ImportPrice, self).save(*args, **kwargs)
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
