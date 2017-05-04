# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2017-05-04 17:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rest_api', '0003_auto_20160317_2258'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseIngredient',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('category', models.CharField(choices=[('BREAD', 'BREAD'), ('CANNED', 'CANNED'), ('DAIRY', 'DAIRY'), ('HERB', 'HERB'), ('FROZEN', 'FROZEN'), ('FRUIT', 'FRUIT'), ('MEAT', 'MEAT'), ('OTHER', 'OTHER'), ('SPICE', 'SPICE'), ('VEGETABLE', 'VEGETABLE')], default='OTHER', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'base_ingredient',
            },
        ),
        migrations.CreateModel(
            name='IngredientMapping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ingredient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredient_mapping', to='rest_api.BaseIngredient')),
            ],
            options={
                'db_table': 'ingredient_mapping',
            },
        ),
    ]
