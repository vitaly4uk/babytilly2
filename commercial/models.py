from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils.translation import gettext_lazy
from django_countries.fields import CountryField
from mptt.models import MPTTModel, TreeForeignKey
from sorl.thumbnail import ImageField

from commercial.functions import get_thumbnail_url


class Departament(models.Model):
    country = CountryField(gettext_lazy('country'))
    email = models.EmailField(gettext_lazy('email'))

    def __str__(self):
        return str(self.country)

    class Meta:
        verbose_name = gettext_lazy('departament')
        verbose_name_plural = gettext_lazy('departments')
        constraints = [
            models.UniqueConstraint(fields=['country', 'email'], name='unique_department')
        ]


class Category(MPTTModel):
    id = models.CharField(max_length=25, primary_key=True)
    parent = TreeForeignKey(
        'self', verbose_name=gettext_lazy('parent'), null=True, blank=True, related_name='children', on_delete=models.CASCADE
    )
    property = models.ManyToManyField(Departament, through='CategoryProperties', verbose_name=gettext_lazy('property'))

    class Meta:
        verbose_name = gettext_lazy('category')
        verbose_name_plural = gettext_lazy('categories')


class CategoryProperties(models.Model):
    department = models.ForeignKey(Departament, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(gettext_lazy('name'), max_length=255)
    published = models.BooleanField(gettext_lazy('published'), default=True)

    class Meta:
        verbose_name = gettext_lazy('category property')
        verbose_name_plural = gettext_lazy('category properties')
        constraints = [
            models.UniqueConstraint(fields=['department', 'category'], name='unique_category_property')
        ]


class Article(models.Model):
    id = models.CharField(max_length=25, primary_key=True)
    category = TreeForeignKey(
        Category, verbose_name=gettext_lazy('category'), null=True, blank=True, on_delete=models.CASCADE
    )
    image = ImageField(gettext_lazy('image'), upload_to='upload/foto/')
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

    class Meta:
        verbose_name = gettext_lazy('article')
        verbose_name_plural = gettext_lazy('articles')


class ArticleProperties(models.Model):
    department = models.ForeignKey(Departament, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    name = models.CharField(gettext_lazy('name'), max_length=255)
    published = models.BooleanField(gettext_lazy('published'), default=True)
    price = models.DecimalField(gettext_lazy('price'), max_digits=10, decimal_places=3, default=0)

    class Meta:
        verbose_name = gettext_lazy('category property')
        verbose_name_plural = gettext_lazy('category properties')
        constraints = [
            models.UniqueConstraint(fields=['department', 'article'], name='unique_article_property')
        ]


class ArticleImage(models.Model):
    article = models.ForeignKey(Article, verbose_name=gettext_lazy('article'), related_name='images', on_delete=models.CASCADE)
    image = ImageField(gettext_lazy('image'), upload_to='upload/foto/')

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

    class Meta:
        verbose_name = gettext_lazy('order item')
        verbose_name_plural = gettext_lazy('order items')
        constraints = [
            models.UniqueConstraint(fields=['order', 'article'], name='unique_order_item')
        ]


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=gettext_lazy('user'), on_delete=models.CASCADE)
    department = models.ForeignKey(Departament, verbose_name=gettext_lazy('department'), on_delete=models.CASCADE)

    class Meta:
        verbose_name = gettext_lazy('profile')
        verbose_name_plural = gettext_lazy('profiles')


class ImportPrice(models.Model):
    file = models.FileField(gettext_lazy('file'), upload_to='upload/import/')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=gettext_lazy('user'), on_delete=models.CASCADE)
    department = models.ForeignKey(Departament, verbose_name=gettext_lazy('department'), on_delete=models.CASCADE)
    imported_at = models.DateTimeField(gettext_lazy('imported at'), auto_now_add=True)

    class Meta:
        verbose_name = gettext_lazy('import')
        verbose_name_plural = gettext_lazy('imports')
