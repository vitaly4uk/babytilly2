# Generated by Django 3.2.9 on 2021-12-06 09:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commercial', '0028_auto_20211202_2129'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='comment',
            field=models.TextField(blank=True, default=''),
        ),
    ]
