from rest_framework import serializers
from rest_api.models import App, Repo, Article, BaseIngredient, IngredientMapping


class BaseIngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = BaseIngredient
        fields = ('id', 'name', 'category',)


class BaseIngredientSerializerNested(BaseIngredientSerializer):
    """
    Extension of BaseIngredienteSerializer that enables one level of nested objects.
    """
    class Meta(BaseIngredientSerializer.Meta):
        # Extends Meta of BaseIngredientSerializer, hence will use same model and fields
        depth = 1


class IngredientMappingSerializer(serializers.ModelSerializer):

    class Meta:
        model = IngredientMapping
        fields = ('id', 'name', 'ingredient',)
