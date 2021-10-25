import csv
import logging
import typing
from io import BytesIO
from django.template import loader
from PIL import Image
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

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


def do_import_csv(csv_file: typing.IO, country: str):
    from commercial.models import Departament, Category, CategoryProperties, Article, ArticleProperties

    field_names = [
        'id', 'name', 'article', 'is_category', 'parent_id',
        '5', '6', '7', 'price', '9', '10', '11', '12', '13', '14', '15', '16', '17',
        'image', '19', 'description', '21', '22'
    ]
    reader = csv.DictReader(csv_file, fieldnames=field_names, delimiter=';')
    department = Departament.objects.get(country=country)
    CategoryProperties.objects.filter(department=department).update(published=False)
    ArticleProperties.objects.filter(department=department).update(published=False)
    for row in reader:
        is_category = row['is_category'] == '1'

        if is_category:
            # print(row)
            category_id = row['id'].strip().rjust(5, '0')

            category, created = Category.objects.get_or_create(pk=category_id)
            category_property, created = CategoryProperties.objects.get_or_create(
                category=category,
                department=department
            )
            category_property.name = row['name']
            category_property.published = True
            category_property.save()

            parent_category_id = row['parent_id']
            if parent_category_id:
                parent_category_id = parent_category_id.strip().rjust(5, '0')
                parent = Category.objects.get(pk=parent_category_id)
                category.parent = parent
                category.level = parent.level + 1
                category.save()
        else:
            # print(row)
            parent_category_id = row['parent_id']
            if parent_category_id:
                parent_category_id = parent_category_id.strip().rjust(5, '0')
                category, created = Category.objects.get_or_create(pk=parent_category_id)
                article_id = row['id'].strip().rjust(5, '0')
                article, created = Article.objects.get_or_create(pk=article_id)
                article.category = category
                article.image.name = 'upload/{}'.format(row['image'][3:].replace("\\", "/"))
                article.save()
                article_property, created = ArticleProperties.objects.get_or_create(
                    article=article,
                    department=department
                )
                article_property.name = row['name']
                article_property.description = row['description']
                article_property.price = row['price']
                article_property.published = True
                article_property.save()

    Category.objects.rebuild()
