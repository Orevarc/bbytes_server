from django.conf.urls import url
from rest_api import views

urlpatterns = [
    url(r'^apps/$', views.AppList.as_view(), name='apps'),
    url(r'^repos/$', views.RepoList.as_view(), name='repos'),
    url(r'^articles/$', views.ArticleList.as_view(), name='articles'),
    url(r'^shopping_list/$', views.ShoppingListApi.as_view(), name='shopping_list'),
    url(r'^base_ingredients/$', views.BaseIngredientApi.as_view(), name='base_ingredients'),
    url(r'^ingredient_mappings/$', views.IngredientMappingApi.as_view(), name='ingredient_mappings'),
]
