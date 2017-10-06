from __future__ import unicode_literals

from django.db import models

from rest_api.constants import IngredientCategories


class BaseIngredient(models.Model):

    name = models.CharField(max_length=255, unique=True)
    category = models.CharField(
        max_length=255,
        choices=IngredientCategories.choices,
        default=IngredientCategories.OTHER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'base_ingredient'


class IngredientMapping(models.Model):

    name = models.CharField(max_length=255)
    ingredient = models.ForeignKey(
        'BaseIngredient',
        related_name='ingredient_mapping',
        on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ingredient_mapping'