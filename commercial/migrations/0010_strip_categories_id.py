# Generated by Django 3.2.8 on 2021-10-25 16:29

from django.db import migrations


def strip_categories_id(apps, schema_migration):
    Category = apps.get_model('commercial', 'Category')

    for category in Category.objects.all():
        category.id = category.id.strip().rjust(5, '0')
        if category.parent_id:
            category.parent_id = category.parent_id.strip().rjust(5, '0')
        category.save()

class Migration(migrations.Migration):

    dependencies = [
        ('commercial', '0009_alter_importprice_file'),
    ]

    operations = [
        migrations.RunPython(strip_categories_id, reverse_code=migrations.RunPython.noop)
    ]
