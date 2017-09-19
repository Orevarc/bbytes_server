from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_api.helpers import GitHubRepoFetcher
from rest_api.models import App, Repo, Article, BaseIngredient, IngredientMapping
from rest_api import serializers

import json

from rest_api.constants import IngredientCategories
from rest_api.parsers import SiteParser


class ShoppingListApi(APIView):
    """
    Shopping list endpoints
    """
    def post(self, request):
        '''
        Posting a list of urls to obtain a shopping list
        '''
        ingredient_parser = SiteParser(urls=request.data.get('recipeUrls'))
        ingredient_parser.parse_urls()
        if ingredient_parser.has_errors():
            return Response(ingredient_parser.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'recipes': ingredient_parser.recipes,
            'shopping_list': ingredient_parser.shopping_list,
            'review_list': ingredient_parser.review_list
        })


class BaseIngredientApi(APIView):
    """
    Base Ingredient Endpoints
    """
    def get(self, request, *args, **kwargs):
        base_ingredients = BaseIngredient.objects.all()
        serializer = serializers.BaseIngredientSerializer(base_ingredients, many=True, context={'request': request})
        return Response({
            'baseIngredients': serializer.data
        })

    def post(self, request, *args, **kwargs):
        serializer = serializers.BaseIngredientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IngredientMappingApi(APIView):
    """
    Ingredient Mapping Endpoints
    """
    def post(self, request, *args, **kwargs):
        serializer = serializers.IngredientMappingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IngredientCategoryApi(APIView):

    def get(self, request, *args, **kwargs):
        categories = dict(IngredientCategories.choices)
        return Response({
            'categories': json.dumps(categories)
        })
