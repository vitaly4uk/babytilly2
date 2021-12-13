# Generated by Django 3.2.9 on 2021-12-13 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commercial', '0029_alter_order_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='full_price',
            field=models.DecimalField(decimal_places=3, default=0, editable=False, max_digits=10, verbose_name='full price'),
        ),
    ]
