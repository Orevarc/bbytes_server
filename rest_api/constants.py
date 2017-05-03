DEFAULT_MEASURABLE_UNIT = 'g'

MEASURABLE = 'MEASURABLE'
NON_MEASURABLE = 'NON_MEASURABLE'

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
