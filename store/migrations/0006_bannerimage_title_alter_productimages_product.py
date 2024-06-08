# Generated by Django 5.0.6 on 2024-06-08 13:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_order_zarinpal_authority_order_zarinpal_data_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='bannerimage',
            name='title',
            field=models.CharField(default=1, max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='productimages',
            name='product',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='images', to='store.product'),
        ),
    ]
