import csv
import logging
import typing
from io import BytesIO

from PIL import Image
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.template import loader

from commercial.models import Departament, Category, CategoryProperties, Article, ArticleProperties

logger = logging.getLogger(__name__)


def export_to_csv(request, order, encode):
    return loader.render_to_string('commercial/csv.html', {'order': order})


def get_thumbnail_url(image, size):
    thumb_name = image.name.replace('upload/foto', 'thumb/{}'.format(size))
    logger.debug('get_thumbnail_url: %s %s', image.name, thumb_name)
    image_bytes = BytesIO()

    if not default_storage.exists(image.name):
        logger.debug('%s does not exit', image.name)
        return '#'

    if not default_storage.exists(thumb_name):
        logger.debug('%s does not exit', thumb_name)
        thumb = Image.open(default_storage.open(image.name))
        try:
            thumb.thumbnail((int(size), int(size)), Image.ANTIALIAS)
        except IOError:
            thumb = Image.new("RGB", (1, 1), (255, 255, 255))
        finally:
            thumb = thumb.convert('RGB')
            thumb.save(image_bytes, "JPEG")
            thumb_name = default_storage.save(thumb_name, ContentFile(image_bytes.getvalue()))
    elif default_storage.modified_time(image.name) > default_storage.modified_time(thumb_name):
        default_storage.delete(thumb_name)
        thumb = Image.open(default_storage.open(image.name))
        thumb.thumbnail((int(size), int(size)), Image.ANTIALIAS)
        thumb = thumb.convert('RGB')
        thumb.save(image_bytes, "JPEG")
        thumb_name = default_storage.save(thumb_name, ContentFile(image_bytes.getvalue()))
    thumb_url = default_storage.url(thumb_name)
    logger.debug('Thumb url: %s', thumb_url)
    return thumb_url


def get_or_create_category(
        category_id: str, category_name: str, departament: Departament, parent: Category = None
) -> Category:
    category, created = Category.objects.get_or_create(pk=category_id)
    category_property, created = CategoryProperties.objects.get_or_create(
        category=category,
        departament=departament
    )
    category_property.name = category_name
    category_property.published = True
    category_property.save()
    if parent:
        category.parent = parent
        category.save()
    return category


def do_import_price(csv_file: typing.IO, country: str):
    field_names = [
        'id', 'name', 'vendor_code', 'is_category', 'parent_id',
        'parent_name', 'trade_price', 'retail_price', 'length', 'width', 'height',
        'volume', 'weight', None, None, 'barcode', 'description', 'image_link',
        'video_link', 'presence', 'site_link', 'company'
    ]
    reader = csv.DictReader(csv_file, fieldnames=field_names, delimiter=';')
    departament = Departament.objects.get(country=country)
    CategoryProperties.objects.filter(departament=departament).update(published=False)
    ArticleProperties.objects.filter(departament=departament).update(published=False)
    for row in reader:
        is_category = row['is_category'] == '1'

        if is_category:
            # print(row)
            parent = get_or_create_category(row['parent_id'], row['parent_name'], departament)
            get_or_create_category(row['id'], row['name'], departament, parent=parent)
        else:
            # print(row)
            parent = get_or_create_category(row['parent_id'], row['parent_name'], departament)
            article_id = row['id']
            article, created = Article.objects.get_or_create(pk=article_id)
            article.category = parent
            article.save()
            article_property, created = ArticleProperties.objects.get_or_create(
                article=article,
                departament=departament
            )
            article_property.name = row['name']
            article_property.description = row['description']
            article_property.price = row['retail_price']
            article_property.published = True
            article_property.save()

    Category.objects.rebuild()


def do_import_novelty(csv_file: typing.IO, departament_id: int):
    _perform_update_articles(csv_file, departament_id, 'is_new')


def do_import_special(csv_file: typing.IO, departament_id: int):
    _perform_update_articles(csv_file, departament_id, 'is_special')


def _perform_update_articles(csv_file: typing.IO, departament_id: int, field_name: str):
    ArticleProperties.objects.filter(departament_id=departament_id).update(**{field_name: False})
    reader = csv.reader(csv_file, delimiter=';')

    for row in reader:
        ArticleProperties.objects.filter(
            departament_id=departament_id,
            article_id=row[0]
        ).update(**{field_name: True})
