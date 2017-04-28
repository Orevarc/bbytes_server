# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-17 22:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rest_api', '0002_article'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='app',
            options={'ordering': ('-start_date',)},
        ),
        migrations.AlterModelOptions(
            name='article',
            options={'ordering': ('-publish_date',)},
        ),
        migrations.AlterField(
            model_name='app',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='app',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='images/'),
        ),
        migrations.AlterField(
            model_name='app',
            name='platform',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='rest_api.Platform'),
        ),
        migrations.AlterField(
            model_name='app',
            name='store_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='article',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='images/'),
        ),
        migrations.AlterField(
            model_name='article',
            name='platform',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='rest_api.Platform'),
        ),
        migrations.AlterField(
            model_name='repo',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='repo',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='images/'),
        ),
        migrations.AlterField(
            model_name='repo',
            name='platform',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='rest_api.Platform'),
        ),
    ]
