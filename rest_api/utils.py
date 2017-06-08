import unicodedata

from rest_api.constants import CONVERSION_MAP
from rest_api.models import (
    BaseIngredient,
    IngredientMapping
)


def find_index(item_list, key, value):
    for i, dic in enumerate(item_list):
        if dic[key] == value:
            return i
    return -1


class BaseIngredientFinder(object):

    @classmethod
    def find(cls, name):
        '''
        Returns the BaseIngredient if one is found directly or through the
        IngredientMapping. Returns None if neither are matched.

        Checks to see if the name string or a substring of the name string
        is a BaseIngredient. If no BaseIngredient is matched, the name is
        checked to see if an IngredientMapping is found.
        '''
        base_ingredient = None
        base_ingredient_found = False
        base_ingredient_filter = name
        while not base_ingredient_found:
            try:
                base_ingredient = BaseIngredient.objects.get(
                    name=base_ingredient_filter)
            except BaseIngredient.DoesNotExist:
                base_ingredient = None
            if base_ingredient:
                base_ingredient_found = True
            else:
                if ' ' in base_ingredient_filter:
                    base_ingredient_filter = base_ingredient_filter.split(
                        ' ', 1)[1]
                else:
                    base_ingredient_found = True
                    base_ingredient = cls.find_by_mapping(name)
        return base_ingredient

    @classmethod
    def find_by_mapping(cls, mapping_name):
        '''
        Returns the BaseIngredient object if one is found. Returns None if not.

        If the item is not found in BaseIngredient, try to see if there is already
        a mapping for the the item. Mappings are common alternatives to standard
        base ingredients (ie cayenne is also cayenne powder)
        '''
        base_ingredient = None
        ingredient_mapping_found = False
        ingredient_mapping_filter = mapping_name
        while not ingredient_mapping_found:
            try:
                ingredient_mapping = IngredientMapping.objects.get(
                    name=ingredient_mapping_filter)
            except IngredientMapping.DoesNotExist:
                ingredient_mapping = None
            if ingredient_mapping:
                ingredient_mapping_found = True
                base_ingredient = BaseIngredient.objects.get(
                    pk=ingredient_mapping.ingredient_id)
            else:
                if ' ' in ingredient_mapping_filter:
                    ingredient_mapping_filter = ingredient_mapping_filter.split(
                        ' ', 1)[1]
                else:
                    return None
        return base_ingredient


class AmountConverter(object):
    '''
        Class to help convert ingredient amounts between different
        weights/amounts. All conversions are going to be 1:1
    '''

    @classmethod
    def convert_measurable_amount(self, from_unit, to_unit, amount):
        if from_unit == to_unit or from_unit not in CONVERSION_MAP or to_unit not in CONVERSION_MAP:
            return float(amount), from_unit
        multiplier = CONVERSION_MAP.get(from_unit).get(to_unit)
        converted_amount = 0
        try:
            converted_amount = float(amount) * multiplier
        except ValueError:
            if '/' in amount:
                numerator, denominator = amount.rsplit('/')
                amount = float(numerator) / float(denominator)
            else:
                amount = unicodedata.numeric(amount.rstrip())
            converted_amount = float(amount) * multiplier
        return converted_amount, to_unit
