import re


CHOICE_NAME_PATTERN = r'^[A-Z]'


def convert_camel_to_snake(name):
    # convert all non alphabets to underscore
    s = re.sub('\W+', '_', name)
    s1 = re.sub('([^_])([A-Z][a-z]+)', r'\1_\2', s.strip('_'))
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)


class ChoiceMeta(type):
    '''
    Meta class for choices

    When defining new choice class with choices specified, class attribute
    can be created dynamically by the choices fields.

    for example:

    class DynamicTemplateTypes(Choices):
        choices = (
            ('GRID', 'GridType'),
            ('CAROUSEL', 'CarouselType'),
        )

    Then this can be used

    DynamicTemplateTypes.GRID_TYPE == 'GRID'
    DynamicTemplateTypes.CAROUSEL_TYPE == 'CAROUSEL'

    The second value (choice name) is converted to upper and snake case and used
    as Class property name
    '''
    def __new__(mcs, name, bases, dict):
        if dict.get('choices'):
            keys = dict.keys()
            for tup in dict['choices']:
                val = tup[0]
                # class property name
                key = convert_camel_to_snake(tup[1]).upper()
                if re.match(CHOICE_NAME_PATTERN, key) and key not in keys:
                    dict[key] = val
        return type.__new__(mcs, name, bases, dict)


class Choices(object):
    __metaclass__ = ChoiceMeta
    '''
        Uses class attribute 'choices' and creates a class that provides
        access to the choice and value.

        This allows us to use the choice format but ensure that invalid choices
        cannot be used.

        Example:
            Class MyChoices(Choices):
                FOO = 1
                BAZ = 2

                choices = (
                    (FOO, 'foo bar!'),
                    (BAZ, '2 baz'),
                )

            >>> MyChoices.FOO
            1
            >>> MyChoices.BAZ
            2
            >>> MyChoices.choices
            ((1, 'foo bar!'), (2, '2 baz'))
            >>> MyChoices.name(MyChoices.FOO)
            'foo bar!'
    '''
    choices = ()

    @classmethod
    def name(cls, value):
        '''
            Returns the frontend display name for this choice
        '''
        for choice, choice_label in cls.choices:
            if value == choice:
                return choice_label

    @classmethod
    def valid_value(cls, value):
        '''
            Checks if given value is a valid choice
        '''
        for choice, choice_label in cls.choices:
            if value == choice:
                return True
        return False

    @classmethod
    def from_label(cls, label):
        '''
            Returns the value based on the given label
        '''
        for choice, choice_label in cls.choices:
            if label == choice_label:
                return choice

    @classmethod
    def keys_list(cls):
        '''
            Returns a list of all allowed values.
        '''
        return [choice[0] for choice in cls.choices]


class IngredientCategories(Choices):
    BREAD = 'BREAD'
    CANNED = 'CANNED'
    DAIRY = 'DAIRY'
    HERB = 'HERB'
    FROZEN = 'FROZEN'
    FRUIT = 'FRUIT'
    MEAT = 'MEAT'
    OTHER = 'OTHER'
    SPICE = 'SPICE'
    VEGETABLE = 'VEGETABLE'

    choices = (
        (BREAD, 'BREAD'),
        (CANNED, 'CANNED'),
        (DAIRY, 'DAIRY'),
        (HERB, 'HERB'),
        (FROZEN, 'FROZEN'),
        (FRUIT, 'FRUIT'),
        (MEAT, 'MEAT'),
        (OTHER, 'OTHER'),
        (SPICE, 'SPICE'),
        (VEGETABLE, 'VEGETABLE'),
    )

DEFAULT_MEASURABLE_UNIT = 'g'

MEASURABLE = 'MEASURABLE'
NON_MEASURABLE = 'NON_MEASURABLE'

INGREDIENT_CATEGORIES = [
    'bread',
    'canned',
    'dairy',
    'herb',
    'frozen',
    'fruit',
    'meat',
    'other',
    'spice',
    'vegetable',
]

INGREDIENT_AMOUNTS = [
    ('bunch', NON_MEASURABLE),# 1/2 bunch of cilantro
    ('can', NON_MEASURABLE),
    ('clove', NON_MEASURABLE),
    ('cloves', NON_MEASURABLE),
    ('cup', MEASURABLE),
    ('cups', MEASURABLE),
    ('fresh', NON_MEASURABLE), # 1 fresh lemon
    ('inch', NON_MEASURABLE),
    ('inches', NON_MEASURABLE),
    ('kg', MEASURABLE),
    ('ml', MEASURABLE),
    ('large', NON_MEASURABLE),
    ('lb.', MEASURABLE),
    ('lbs', MEASURABLE),
    ('oz.', MEASURABLE),
    ('small', NON_MEASURABLE),
    ('tbsp', MEASURABLE),
    ('tsp', MEASURABLE),
    ('whole', NON_MEASURABLE)
]

CONVERSION_MAP = {
        'L': {
            'ml': 1000,
            'tsp': 202.884,
            'tbsp': 67.628,
            'cup': 4.1667,
            'oz': 33.814,
            'lb': 2.20,
            'g': 1000,
            'kg': 1,
        },
        'ml': {
            'L': 0.001,
            'tsp': 0.202884,
            'tbsp': 0.067628,
            'cup': 0.0041667,
            'oz': 0.033814,
            'lb': 0.00220,
            'g': 1,
            'kg': 0.001,
        },
        'tsp': {
            'L': 0.00492892,
            'ml': 4.92892,
            'tbsp': 0.333333,
            'cup': 0.02053715,
            'oz': 0.1666665,
            'lb': 0, #
            'g': 5,
            'kg': 0.005,
        },
        'tbsp': {
            'L': 0.0147868,
            'ml': 14.7868,
            'tsp': 3,
            'cup': 0.06161,
            'oz': 0.5,
            'lb': 0, #
            'g': 14.7868,
            'kg': 0.0147868,
        },
        'cup': {
            'L': 0.24,
            'ml': 240,
            'tsp': 48.6922,
            'tbsp': 16.2307,
            'oz': 8.11536,
            'lb': 2.20,
            'g': 240,
            'kg': 0.24,
        },
        'oz': {
            'L': 0.0295735,
            'ml': 29.5735,
            'tsp': 6,
            'tbsp': 2,
            'cup': 0.123223,
            'lb': 2.20,
            'g': 29.5735,
            'kg': 0.0295735,
        },
        'lb': {
            'L': 67.628,
            'ml': 1000,
            'tsp': 202.884,
            'tbsp': 67.628,
            'cup': 4.1667,
            'oz': 33.814,
            'g': 1000,
            'kg': 1,
        },
        'g': {
            'L': 0.001,
            'ml': 1,
            'tsp': 0.2,
            'tbsp': 0.0666,
            'cup': 0.0042267,
            'oz': 0.035274,
            'lb': 0.00220462,
            'kg': 0.001,
        },
        'kg': {
            'L': 1,
            'ml': 1000,
            'tsp': 240,
            'tbsp': 64,
            'cup': 8,
            'oz': 35.27391,
            'lb': 2.2046,
            'g': 1000,
        }
}
