from django.conf.urls import url
from rest_api import views

urlpatterns = [
    url(r'^shopping_list/$', views.ShoppingListApi.as_view(), name='shopping_list'),
    url(r'^base_ingredients/$', views.BaseIngredientApi.as_view(), name='base_ingredients'),
    url(r'^ingredient_mappings/$', views.IngredientMappingApi.as_view(), name='ingredient_mappings'),
    url(r'^ingredient_categories/$', views.IngredientCategoryApi.as_view(), name='ingredient_categories'),
]
