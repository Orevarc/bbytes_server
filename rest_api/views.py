from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_api.helpers import GitHubRepoFetcher
from rest_api.models import App, Repo, Article, BaseIngredient, IngredientMapping
from rest_api import serializers

import json
import logging

from rest_api.constants import IngredientCategories
from rest_api.utils import get_shopping_list_from_urls


class AppList(APIView):
    """
    List all apps or create a new one.
    """

    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request, *args, **kwargs):
        apps = App.objects.all()
        serializer = serializers.AppSerializerNested(apps, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = serializers.AppSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RepoList(APIView):
    """
    List all repositories or create a new one.
    """

    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request, *args, **kwargs):
        apps = Repo.objects.all()
        serializer = serializers.RepoSerializerNested(apps, many=True, context={'request': request})

        fetcher = GitHubRepoFetcher()
        [self._populate_github_stars(repo, fetcher) for repo in serializer.data]
        # Sort repos by stars desdending
        sorted_data = sorted(serializer.data, key=lambda repo: repo['stars'], reverse=True)
        return Response(sorted_data)

    def post(self, request, *args, **kwargs):
        serializer = serializers.RepoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _populate_github_stars(self, repo, fetcher):
        try:
            stars = fetcher.fetch(repo['url'])['stargazers_count']
        except Exception as e:
            stars = None
            logging.error('Could not get repo stars due to ' + str(e))

        repo['stars'] = stars


class ArticleList(APIView):
    """
    List all articles or create a new one.
    """

    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request, *args, **kwargs):
        articles = Article.objects.all()
        serializer = serializers.ArticleSerializerNested(articles,
                                                         many=True,
                                                         context={'request': request})
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = serializers.ArticleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShoppingListApi(APIView):
    """
    Shopping list endpoints
    """
    def post(self, request):
        '''
        Posting a list of urls to obtain a shopping list
        '''
        shopping_list = get_shopping_list_from_urls(request.data.get('recipeUrls'))
        return Response(shopping_list)


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
        print("IN IM API")
        print(request.data)
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
